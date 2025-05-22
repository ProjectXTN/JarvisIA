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

async def fetch_page(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                main_content = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find('body')
                )

                if main_content:
                    for tag in main_content.find_all(["nav", "footer", "aside", "header", "script", "style"]):
                        tag.decompose()

                    text = main_content.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)

                return url, text
    except Exception as e:
        print(f"[ERRO] Falha ao buscar {url}: {e}")
        return url, None

async def fetch_multiple_pages(links):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, link) for link in links]
        return await asyncio.gather(*tasks)

def search_web(query, min_length=300, total_limit=5000, max_links=10):
    if not BRAVE_API_KEY:
        return "API KEY da Brave Search não encontrada.", "internet"

    try:
        print(f"[🔎] Pesquisando na internet sobre: {query}")

        current_year = str(datetime.datetime.now().year)
        previous_year = str(int(current_year) - 1)
        next_year = str(int(current_year) + 1)

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
            # Here: you can change the logic if you want to accept shorter/older texts
            if text and any(year in text for year in [current_year, next_year, previous_year]) and len(text) > min_length:
                print(f"Conteúdo válido encontrado em: {url}")
                links_with_text.append((url, text[:10000]))
            else:
                print(f"Conteúdo ignorado (incompleto ou desatualizado): {url}")

        if not links_with_text:
            return "Não consegui acessar nenhum conteúdo atualizado.", "internet"

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
