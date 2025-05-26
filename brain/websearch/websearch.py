import os
import requests
import asyncio
import aiohttp
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from brain.memory.memory import llama_query, DEFAULT_MODEL
from dotenv import load_dotenv

load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

def extract_readable_source(url):
    try:
        domain = urlparse(url).netloc
        parts = domain.split('.')
        if "www" in parts:
            parts.remove("www")
        base = [p for p in parts if p not in ['com', 'org', 'net', 'br']]
        return base[0].capitalize() if base else domain
    except:
        return url
    
def parse_html_universal(html, url=None, max_blocks=10, min_block_length=80):
    soup = BeautifulSoup(html, "html.parser")
    
    # Limpa elementos inúteis
    for tag in soup(["nav", "footer", "aside", "header", "script", "style", "form", "noscript", "svg", "canvas", "iframe"]):
        tag.decompose()
    
    blocks = []

    # 1. Título da página
    if soup.title and soup.title.string:
        blocks.append(f"[TÍTULO] {soup.title.string.strip()}")

    # 2. Subtítulos
    for h in soup.find_all(['h1', 'h2', 'h3']):
        txt = h.get_text(strip=True)
        if txt and len(txt) >= min_block_length:
            blocks.append(f"[SUBTÍTULO] {txt}")

    # 3. Parágrafos grandes
    for p in soup.find_all('p'):
        txt = p.get_text(separator=" ", strip=True)
        if txt and len(txt) >= min_block_length:
            blocks.append(f"[PARÁGRAFO] {txt}")

    # 4. Listas
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text(" ", strip=True) for li in ul.find_all('li')]
        items = [i for i in items if len(i) >= 10]
        if items and len(" ".join(items)) > min_block_length:
            blocks.append(f"[LISTA]\n" + "\n".join(f"- {item}" for item in items))

    # 5. Artigos/Seções
    for tag in soup.find_all(['article', 'section']):
        txt = tag.get_text(separator="\n", strip=True)
        if txt and len(txt) > min_block_length:
            blocks.append(f"[BLOCO] {txt[:500]}...")  # Amostra do conteúdo

    # Remove duplicados e limita o número de blocos
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
        body = soup.find('body')
        if body:
            txt = body.get_text(separator="\n", strip=True)
            if txt and len(txt) > min_block_length:
                final_blocks.append(f"[BODY] {txt[:1000]}...")

    if url:
        fonte = f"[FONTE] {url}"
        final_blocks.append(fonte)

    return "\n\n".join(final_blocks)

async def fetch_page(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                html = await response.text()
                parsed_text = parse_html_universal(html, url)
                return url, parsed_text
    except Exception as e:
        print(f"[ERRO] Falha ao buscar {url}: {e}")
        return url, None

async def fetch_multiple_pages(links):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, link) for link in links]
        return await asyncio.gather(*tasks)

def search_web(query, min_length=80, total_limit=5000, max_links=10):
    if not BRAVE_API_KEY:
        return "API KEY da Brave Search não encontrada.", "internet"

    try:
        print(f"[🔎] Pesquisando na internet sobre: {query}")

        url = f"https://api.search.brave.com/res/v1/web/search?q={query}"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        results = data.get("web", {}).get("results", [])

        if not results:
            return "Nenhum resultado encontrado na web.", "internet"

        links = [result["url"] for result in results[:max_links]]
        print(f"[🔗] Links encontrados: {links}")

        pages_data = asyncio.run(fetch_multiple_pages(links))

        links_with_text = []
        for result in pages_data:
            if not result:
                continue 

            url, text = result
            # Aceita qualquer texto relevante, não depende mais do ano
            if text and len(text) > min_length:
                print(f"Conteúdo válido encontrado em: {url}")
                links_with_text.append((url, text[:10000]))
            else:
                print(f"Conteúdo ignorado (curto ou vazio): {url}")

        if not links_with_text:
            return "Não consegui acessar nenhum conteúdo relevante.", "internet"

        # Set up web context
        combined_texts = ""
        for _, text in links_with_text:
            if len(combined_texts) + len(text) > total_limit:
                combined_texts += text[:total_limit - len(combined_texts)]
                break
            combined_texts += text + "\n\n---\n\n"

        sources = "\n".join([f"{extract_readable_source(link)}" for link, _ in links_with_text])
        main_source = extract_readable_source(links_with_text[0][0]) if links_with_text else "internet"

        return combined_texts.strip(), sources

    except Exception as e:
        print(f"[ERRO] Erro durante a busca web: {e}")
        return f"Erro ao buscar na web: {e}", "internet"
