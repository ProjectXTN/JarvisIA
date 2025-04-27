import re
import string
import time

from comandos.comandos_datahora import comandos_datahora
from comandos.comandos_musica import comandos_musica
from comandos.comandos_navegador import comandos_navegador
from comandos.comandos_sistema import comandos_sistema, comando_desligar
from comandos.comandos_imagem import comandos_imagem
from comandos.comandos_pastas import comandos_pastas
from comandos.comandos_software import comandos_software
from comandos.comandos_multiplos import comandos_multiplos
from comandos.comandos_memoria import comandos_memoria
from comandos.comandos_avatar import comandos_avatar
from comandos.comandos_emocionais import comandos_emocionais
from comandos.comandos_pesquisa import executar_pesquisa
from comandos.comandos_reflexao import comandos_reflexao
from brain.llama_connection import llama_query

from brain.audio import say
from brain.utils import log_interaction
from brain.dev import extrair_e_salvar_codigo

# Novo: Conexão persistente com o LLaMA3
import requests
session = requests.Session()

# Cache de respostas para acelerar
respostas_cache = {}

# Junta todos os comandos com detecção baseada em regex interna
COMMAND_HANDLERS = [
    comandos_multiplos,
    comandos_software,
    comandos_datahora,
    comandos_musica,
    comandos_navegador,
    comandos_sistema,
    comandos_pastas,
    comandos_imagem,
    comandos_memoria,
    comandos_reflexao,
    comandos_emocionais,
    comandos_avatar
]

def process_command(query):
    query = query.lower().strip()

    # Remove "jarvis" do começo com ou sem vírgula/espaço
    query = re.sub(r"^jarvis[\s,]*", "", query)
    query = query.lstrip(", ").strip()
    query = query.rstrip(string.punctuation)

    print(f"[DEBUG] Frase recebida: {query}")

    if comando_desligar(query) is False:
        return False

    if re.search(r"\b(pesquise|procure|busque)\s+(na\s+)?(internet|web)\b", query):
        if executar_pesquisa(query):
            return True

    for grupo in COMMAND_HANDLERS:
        if isinstance(grupo, dict):
            for chave, func in grupo.items():
                if chave in query:
                    print(f"[DEBUG] Executando comando: {chave}")
                    return func(query)
        elif isinstance(grupo, list):
            for padrao, func in grupo:
                if re.search(padrao, query):
                    print(f"[DEBUG] Executando regex: {padrao}")
                    return func(query)

    # 🔁 Fallback usando LLaMA3 + Cache
    if query in respostas_cache:
        resposta = respostas_cache[query]
        print("[DEBUG] Resposta recuperada do cache.")
    else:
        start_time = time.time()
        resposta = llama_query(query)
        end_time = time.time()
        print(f"⏱️ Tempo para gerar resposta (memória turbo): {end_time - start_time:.2f} segundos.")

        if resposta:
            respostas_cache[query] = resposta

    if resposta:
        log_interaction(query, resposta)

        if "```" in resposta:
            print("[🤖 SALVANDO] Código detectado via memória.")
            extrair_e_salvar_codigo(resposta, titulo=query)
        say(resposta)
        return True

    say("Desculpe, ainda não aprendi sobre isso.")
    return True
