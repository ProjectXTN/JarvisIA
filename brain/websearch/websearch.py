import os
import requests
import asyncio
import aiohttp
import datetime
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from brain.memory.memory import llama_query, DEFAULT_MODEL
from dotenv import load_dotenv
from core.settings import WEB_MAX_PAGES, WEB_FETCH_BUDGET

load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")


BLOCK_LABELS = {
    "pt": {
        "title": "[TÍTULO]",
        "subtitle": "[SUBTÍTULO]",
        "paragraph": "[PARÁGRAFO]",
        "list": "[LISTA]",
        "block": "[BLOCO]",
        "body": "[BODY]",
        "source": "[FONTE]",
    },
    "en": {
        "title": "[TITLE]",
        "subtitle": "[SUBTITLE]",
        "paragraph": "[PARAGRAPH]",
        "list": "[LIST]",
        "block": "[BLOCK]",
        "body": "[BODY]",
        "source": "[SOURCE]",
    },
    "fr": {
        "title": "[TITRE]",
        "subtitle": "[SOUS-TITRE]",
        "paragraph": "[PARAGRAPHE]",
        "list": "[LISTE]",
        "block": "[BLOC]",
        "body": "[CORPS]",
        "source": "[SOURCE]",
    },
}


def extract_readable_source(url):
    try:
        domain = urlparse(url).netloc
        parts = domain.split(".")
        if "www" in parts:
            parts.remove("www")
        base = [p for p in parts if p not in ["com", "org", "net", "br"]]
        return base[0].capitalize() if base else domain
    except:
        return url


def parse_html_universal(html, url=None, lang="pt", max_blocks=10, min_block_length=80):
    soup = BeautifulSoup(html, "html.parser")
    labels = BLOCK_LABELS.get(lang, BLOCK_LABELS["en"])

    # Limpa elementos inúteis
    for tag in soup(
        [
            "nav",
            "footer",
            "aside",
            "header",
            "script",
            "style",
            "form",
            "noscript",
            "svg",
            "canvas",
            "iframe",
        ]
    ):
        tag.decompose()

    blocks = []

    if soup.title and soup.title.string:
        blocks.append(f"{labels['title']} {soup.title.string.strip()}")

    for h in soup.find_all(["h1", "h2", "h3"]):
        txt = h.get_text(strip=True)
        if txt and len(txt) >= min_block_length:
            blocks.append(f"{labels['subtitle']} {txt}")

    for p in soup.find_all("p"):
        txt = p.get_text(separator=" ", strip=True)
        if txt and len(txt) >= min_block_length:
            blocks.append(f"{labels['paragraph']} {txt}")

    for ul in soup.find_all(["ul", "ol"]):
        items = [li.get_text(" ", strip=True) for li in ul.find_all("li")]
        items = [i for i in items if len(i) >= 10]
        if items and len(" ".join(items)) > min_block_length:
            blocks.append(
                f"{labels['list']}\n" + "\n".join(f"- {item}" for item in items)
            )

    for tag in soup.find_all(["article", "section"]):
        txt = tag.get_text(separator="\n", strip=True)
        if txt and len(txt) > min_block_length:
            blocks.append(f"{labels['block']} {txt[:500]}...")

    seen = set()
    final_blocks = []
    for b in blocks:
        if b not in seen:
            final_blocks.append(b)
            seen.add(b)
        if len(final_blocks) >= max_blocks:
            break

    if not final_blocks:
        # Fallback: pega tudo do <body>
        body = soup.find("body")
        if body:
            txt = body.get_text(separator="\n", strip=True)
            if txt and len(txt) > min_block_length:
                final_blocks.append(f"{labels['body']} {txt[:1000]}...")

    if url:
        fonte = f"{labels['source']} {url}"
        final_blocks.append(fonte)

    return "\n\n".join(final_blocks)


# Navegador comum: muitos sites recusam pedidos sem User-Agent
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


async def fetch_page(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text(errors="ignore")
                return url, parse_html_universal(html, url)
            print(f"[WEB] {url} respondeu {response.status}")
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"[WEB] Falha ao buscar {url}: {type(e).__name__} {e}")
    return url, None


async def fetch_multiple_pages(links, budget=WEB_FETCH_BUDGET):
    """Baixa as páginas em paralelo, com prazo total: as que não chegarem a
    tempo ficam de fora em vez de atrasar a resposta. Mantém a ordem da busca."""
    timeout = aiohttp.ClientTimeout(total=budget)
    async with aiohttp.ClientSession(headers=_HEADERS, timeout=timeout) as session:
        tasks = [asyncio.create_task(fetch_page(session, link)) for link in links]
        done, pending = await asyncio.wait(tasks, timeout=budget)
        for task in pending:
            task.cancel()
        if pending:
            print(f"[WEB] {len(pending)} página(s) passaram de {budget:.1f}s e ficaram de fora.")
        results = []
        for task in tasks:
            if task in done and not task.cancelled() and task.exception() is None:
                results.append(task.result())
        return results


def _brave_snippets(results, limit=6):
    """Resumos que a própria Brave devolve: chegam com os links, sem custo extra."""
    lines = []
    for result in results[:limit]:
        title = BeautifulSoup(result.get("title", ""), "html.parser").get_text(" ", strip=True)
        parts = [result.get("description", "")] + list(result.get("extra_snippets") or [])[:2]
        text = " ".join(BeautifulSoup(p, "html.parser").get_text(" ", strip=True) for p in parts if p)
        age = result.get("age") or result.get("page_age") or ""
        if title or text:
            lines.append(f"- {title} ({extract_readable_source(result.get('url', ''))}{', ' + age if age else ''}): {text}")
    return "\n".join(lines)


# Páginas da última busca (web ou notícias), para Pedro poder pedir
# "abra a página onde você encontrou isso". Lista de {url, site, title}.
LAST_SOURCES = []


def remember_sources(items):
    """Guarda as fontes da última busca (substitui as anteriores)."""
    LAST_SOURCES[:] = [
        {"url": i["url"], "site": extract_readable_source(i["url"]), "title": i.get("title", "")}
        for i in items if i.get("url", "").startswith(("http://", "https://"))
    ]


def numbered_sources():
    """Texto com as fontes numeradas, para o modelo citar e para abrir depois."""
    return "\n".join(
        f"{n}. {s['site']} — {s['title']} ({s['url']})" for n, s in enumerate(LAST_SOURCES, 1)
    )


def search_web(query, min_length=80, total_limit=5000, max_links=WEB_MAX_PAGES,
               remember=True, url_filter=None):
    """Busca e lê páginas. remember=False não troca as fontes do "abrir a fonte"
    (estudo autônomo); url_filter(url) -> bool descarta endereços."""
    if not BRAVE_API_KEY:
        return "API KEY da Brave Search não encontrada.", "internet"

    try:
        started = time.monotonic()
        print(f"[🔎] Pesquisando na internet sobre: {query}")

        headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query[:400], "count": 8, "extra_snippets": "true"},
            headers=headers,
            timeout=(3, 8),
        )
        response.raise_for_status()
        results = response.json().get("web", {}).get("results", [])

        if not results:
            return "Nenhum resultado encontrado na web.", "internet"

        snippets = _brave_snippets(results)
        if url_filter:
            results = [r for r in results if url_filter(r.get("url", ""))]
            if not results:
                return "Nenhum resultado permitido.", "internet"
        links = [result["url"] for result in results[:max_links]]
        print(f"[🔗] Lendo {len(links)} páginas: {links}")

        pages_data = asyncio.run(fetch_multiple_pages(links))

        links_with_text = []
        for url, text in pages_data:
            if text and len(text) > min_length:
                links_with_text.append((url, text[:10000]))
            else:
                print(f"[WEB] Conteúdo curto ou vazio: {url}")

        # Resumos da busca primeiro (sempre há), depois o texto das páginas
        combined_texts = f"Resumos da busca:\n{snippets}\n\n---\n\n" if snippets else ""
        for _, text in links_with_text:
            if len(combined_texts) + len(text) > total_limit:
                combined_texts += text[: max(0, total_limit - len(combined_texts))]
                break
            combined_texts += text + "\n\n---\n\n"

        if not combined_texts.strip():
            return "Não consegui acessar nenhum conteúdo relevante.", "internet"

        used = [link for link, _ in links_with_text] or [r.get("url", "") for r in results[:3]]
        titles = {r.get("url"): BeautifulSoup(r.get("title", ""), "html.parser").get_text(" ", strip=True)
                  for r in results}
        if remember:
            remember_sources([{"url": link, "title": titles.get(link, "")} for link in used])
        sources = "\n".join(extract_readable_source(link) for link in used)
        print(f"[WEB] {len(links_with_text)} página(s) lidas em {time.monotonic() - started:.1f}s.")
        return combined_texts.strip(), sources

    except Exception as e:
        print(f"[ERRO] Erro durante a busca web: {e}")
        return f"Erro ao buscar na web: {e}", "internet"
