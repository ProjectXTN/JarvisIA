import os
import re
import requests
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from brain.memoria import generate_response, DEFAULT_MODEL
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

def extrair_fonte_legivel(url):
    try:
        dominio = urlparse(url).netloc
        partes = dominio.split('.')
        if "www" in partes:
            partes.remove("www")
        base = [p for p in partes if p not in ['com', 'org', 'net', 'br']]
        return base[0].capitalize() if base else dominio
    except:
        return url

def buscar_na_web(query):
    if not BRAVE_API_KEY:
        return "API KEY da Brave Search não encontrada.", "internet"

    try:
        ano_atual = str(datetime.datetime.now().year)
        ano_seguinte = str(int(ano_atual) + 1)

        url = f"https://api.search.brave.com/res/v1/web/search?q={query}"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        resultados = data.get("web", {}).get("results", [])

        if not resultados:
            return "Nenhum resultado encontrado na web.", "internet"

        links_com_texto = []
        for resultado in resultados:
            link = resultado["url"]
            try:
                page = requests.get(link, timeout=5)
                soup = BeautifulSoup(page.text, "html.parser")
                texto = soup.get_text(separator="\n", strip=True)
                if any(ano in texto for ano in [ano_atual, ano_seguinte]) and len(texto) > 500:
                    links_com_texto.append((link, texto[:10000]))
                if len(links_com_texto) >= 3:
                    break
            except:
                continue

        if not links_com_texto:
            return "Não consegui acessar nenhum conteúdo atualizado.", "internet"

        # Junta os textos (limitando o total a 5000 caracteres pra evitar problemas)
        limite_total = 5000
        textos_combinados = ""
        for _, texto in links_com_texto:
            if len(textos_combinados) + len(texto) > limite_total:
                textos_combinados += texto[:limite_total - len(textos_combinados)]
                break
            textos_combinados += texto + "\n\n---\n\n"

        fontes = "\n".join([f"🔗 {extrair_fonte_legivel(link)}" for link, _ in links_com_texto])
        fonte_principal = extrair_fonte_legivel(links_com_texto[0][0]) if links_com_texto else "internet"

        prompt = (
            f"Você é Jarvis, um assistente virtual altamente inteligente. "
            f"Com base nas informações coletadas abaixo de múltiplas fontes confiáveis, "
            f"responda à pergunta com clareza, objetividade e em português.\n\n"
            f"Pergunta: {query}\n\n"
            f"Conteúdo:\n{textos_combinados}\n\n"
            f"Responda em português, de forma objetiva. No final, mostre as fontes usadas.\n"
        )

        try:
            resposta = generate_response(prompt, DEFAULT_MODEL)
            resposta = resposta[:8000] if isinstance(resposta, str) else "Erro: resposta inválida."
        except Exception as e:
            resposta = f"Erro ao gerar resposta: {e}"

        return f"{resposta.strip()}\n\n📚 Fontes:\n{fontes}", fonte_principal

    except Exception as e:
        return f"Erro ao buscar na web: {e}", "internet"

