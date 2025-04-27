import os
import re
import requests
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from brain.memoria import generate_response, DEFAULT_MODEL
from dotenv import load_dotenv

# Load .env variables
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

def search_web(query):
    if not BRAVE_API_KEY:
        return "API KEY da Brave Search não encontrada.", "internet"

    try:
        current_year = str(datetime.datetime.now().year)
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

        links_with_text = []
        for result in results:
            link = result["url"]
            try:
                page = requests.get(link, timeout=5)
                soup = BeautifulSoup(page.text, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                if any(year in text for year in [current_year, next_year]) and len(text) > 500:
                    links_with_text.append((link, text[:10000]))
                if len(links_with_text) >= 3:
                    break
            except:
                continue

        if not links_with_text:
            return "Não consegui acessar nenhum conteúdo atualizado.", "internet"

        # Combine texts (limiting to 5000 characters total to avoid problems)
        total_limit = 5000
        combined_texts = ""
        for _, text in links_with_text:
            if len(combined_texts) + len(text) > total_limit:
                combined_texts += text[:total_limit - len(combined_texts)]
                break
            combined_texts += text + "\n\n---\n\n"

        sources = "\n".join([f"🔗 {extract_readable_source(link)}" for link, _ in links_with_text])
        main_source = extract_readable_source(links_with_text[0][0]) if links_with_text else "internet"

        prompt = (
            f"Você é Jarvis, um assistente virtual altamente inteligente. "
            f"Com base nas informações coletadas abaixo de múltiplas fontes confiáveis, "
            f"responda à pergunta com clareza, objetividade e em português.\n\n"
            f"Pergunta: {query}\n\n"
            f"Conteúdo:\n{combined_texts}\n\n"
            f"Responda em português, de forma objetiva. No final, mostre as fontes usadas.\n"
        )

        try:
            answer = generate_response(prompt, DEFAULT_MODEL)
            answer = answer[:8000] if isinstance(answer, str) else "Erro: resposta inválida."
        except Exception as e:
            answer = f"Erro ao gerar resposta: {e}"

        return f"{answer.strip()}\n\n📚 Fontes:\n{sources}", main_source

    except Exception as e:
        return f"Erro ao buscar na web: {e}", "internet"