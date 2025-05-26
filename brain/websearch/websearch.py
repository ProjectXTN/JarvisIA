import os
import requests
import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv
import re

load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

def extract_readable_source(url):
    """
    Extract a readable domain name from a given URL.
    """
    try:
        domain = urlparse(url).netloc
        parts = domain.split('.')
        if "www" in parts:
            parts.remove("www")
        base = [p for p in parts if p not in ['com', 'org', 'net', 'br']]
        return base[0].capitalize() if base else domain
    except Exception:
        return url

def extract_relevant_blocks(soup, max_blocks=20):
    """
    General-purpose extraction: headlines, subheadings, paragraphs, list items.
    Picks up to `max_blocks` blocks of reasonable size for LLM context.
    """
    blocks = []
    for tag in ['h1', 'h2', 'h3', 'p', 'li']:
        for el in soup.find_all(tag):
            text = el.get_text(strip=True)
            if text and 25 < len(text) < 300:
                blocks.append(text)
            if len(blocks) >= max_blocks:
                break
        if len(blocks) >= max_blocks:
            break
    # Fallback: If nothing is found, use the first part of the body (avoids empty context)
    if not blocks:
        body = soup.find('body')
        if body:
            text = body.get_text(separator="\n", strip=True)
            if text:
                blocks = [text[:1000]]
    return '\n'.join(blocks[:max_blocks])

def extract_news_blocks(soup, max_blocks=20):
    """
    Specialized extraction for news: headlines and blocks that mention 'today', current date, or day of the week.
    Falls back to general blocks if nothing is found.
    """
    today_str = datetime.now().strftime("%d/%m/%Y")
    day_of_week = datetime.now().strftime("%A").lower()
    blocks = []
    # Try to prioritize lines that mention today or the current date
    for tag in ['h1', 'h2', 'h3', 'p', 'li']:
        for el in soup.find_all(tag):
            text = el.get_text(strip=True)
            if not text or len(text) < 20 or len(text) > 300:
                continue
            lowered = text.lower()
            if "hoje" in lowered or today_str in text or day_of_week in lowered:
                blocks.append(text)
            elif len(blocks) < max_blocks:
                blocks.append(text)
        if len(blocks) >= max_blocks:
            break
    if not blocks:
        return extract_relevant_blocks(soup, max_blocks)
    return '\n'.join(blocks[:max_blocks])

async def fetch_page(session, url, extractor):
    """
    Fetch a single page asynchronously and extract relevant blocks of text using the provided extractor.
    """
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                html = await response.text(errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                relevant_text = extractor(soup)
                return url, relevant_text
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return url, None

async def fetch_multiple_pages(links, extractor):
    """
    Fetch multiple pages concurrently and extract their relevant content using the provided extractor.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, link, extractor) for link in links]
        return await asyncio.gather(*tasks)

def is_url_recent(url, years_back=1):
    """
    Check if a URL contains the current year or recent years.
    Useful for filtering news or recent information.
    """
    year = datetime.now().year
    years = [str(year - i) for i in range(years_back + 1)]
    for y in years:
        if f"/{y}/" in url or f"-{y}-" in url or f"{y}." in url:
            return True
    return False

def is_news_query(query):
    """
    Simple heuristic to detect if the query is about news or current events.
    """
    news_keywords = [
        "notícia", "noticias", "news", "hoje", "today", "últimas", "latest", "atual", "now", "headline"
    ]
    lowered = query.lower()
    return any(word in lowered for word in news_keywords)

def search_web(query, min_length=150, total_limit=5000, max_links=10):
    """
    Search the web using Brave Search API, extract relevant text blocks,
    and prepare context for the LLM. Uses a news-focused extractor if the query seems to be about current events.
    """
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

        # Choose extractor based on query type
        extractor = extract_news_blocks if is_news_query(query) else extract_relevant_blocks

        pages_data = asyncio.run(fetch_multiple_pages(links, extractor))

        links_with_text = []
        for i, result in enumerate(pages_data):
            if not result:
                print(f"[DEBUG] None result for {links[i]}")
                continue
            url, text = result
            if not url or not text:
                continue
            if is_url_recent(url) or len(text) > min_length:
                print(f"Valid content found at: {url}")
                links_with_text.append((url, text[:10000]))
            else:
                print(f"Ignored content (incomplete or outdated): {url}")

        if not links_with_text:
            return "Não consegui acessar nenhum conteúdo atualizado.", "internet"

        # Build context with only the relevant blocks, not a huge text dump
        combined_texts = ""
        for _, text in links_with_text:
            if len(combined_texts) + len(text) > total_limit:
                combined_texts += text[:total_limit - len(combined_texts)]
                break
            combined_texts += text + "\n\n---\n\n"

        sources = "\n".join([f"{extract_readable_source(link)}" for link, _ in links_with_text])

        return combined_texts.strip(), sources

    except Exception as e:
        print(f"[ERROR] Error during web search: {e}")
        return f"Erro ao buscar na web: {e}", "internet"
