import time
import re
import string
import os
from datetime import datetime
from comandos.comandos_pesquisa import execute_search
from brain.learning.inserir_memoria import insert_memory
from brain.memoria import generate_response, DEFAULT_MODEL
from brain.learning.consultar_memoria import consultar_memoria

aprendizado_ativado = False  # Flag global de controle


def limpar_titulo(texto):
    titulo = texto.strip().lower()
    titulo = re.sub(r"\be\b$", "", titulo).strip()
    return titulo.strip(string.punctuation)


def gerar_topicos_populares():
    prompt = (
        "Liste 5 tópicos relevantes, atuais e populares nas áreas de ciência, tecnologia, inovação ou sociedade. "
        "Inclua temas emergentes, pesquisas em destaque, avanços científicos ou tendências tecnológicas. "
        "Cada tópico deve conter no máximo 3 palavras. Não inclua explicações, apenas a lista simples separada por vírgulas.\n"
        "Exemplo: inteligência artificial, blockchain, computação quântica, cidades inteligentes, biotecnologia avançada"
    )
    resposta = generate_response(prompt, DEFAULT_MODEL)

    if not isinstance(resposta, str):
        return []

    topicos = [
        t.strip().lower()
        for t in resposta.split(",")
        if 2 < len(t.strip()) < 40 and re.search(r"\w", t)
    ]

    topicos_unicos = list(dict.fromkeys(topicos))[:5]

    if not topicos_unicos:
        print(f"[DEBUG] Resposta bruta da IA: {resposta}")
        print("[FALLBACK] Usando tópicos padrão...")
        topicos_unicos = [
            "inteligência artificial",
            "blockchain",
            "robótica",
            "biotecnologia",
            "computação quântica",
        ]

    return topicos_unicos


def log_aprendizado(titulo, conteudo, fonte, data):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Define nome do arquivo com base na data de hoje
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = os.path.join(log_dir, f"aprendizados_{data_hoje}.txt")

    try:
        with open(nome_arquivo, "a", encoding="utf-8") as f:
            f.write(f"\n=== {titulo.upper()} ===\n")
            f.write(f" {data} |  Fonte: {fonte}\n")
            f.write(f"{conteudo.strip()[:5000]}...\n")
            f.write("-" * 60 + "\n")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar log de aprendizado: {e}")


def auto_aprender():
    while True:
        if not aprendizado_ativado:
            print("🛑 [AUTO-LEARNING] Modo de aprendizado desativado. Pausando...\n")
            break

        print(f"\n🧠 [AUTO-LEARNING] Iniciando novo ciclo às {datetime.now().strftime('%H:%M:%S')}...")
        topicos = gerar_topicos_populares()

        if not topicos:
            print("⚠️ Nenhum tópico válido gerado. Tentando novamente em instantes...\n")
            time.sleep(10)
            continue

        print(f"[AUTO-LEARNING] Tópicos gerados: {topicos}")
        aprendidos_hoje = []

        for topico in topicos:
            if not aprendizado_ativado:  # Checar também dentro do FOR para parar no meio
                print("🛑 [AUTO-LEARNING] Modo de aprendizado desativado durante ciclo. Pausando...\n")
                return

            pergunta = f"O que é {topico}?"
            resposta, fonte = execute_search(pergunta, falar=False)

            if isinstance(resposta, str) and "Erro" not in resposta:
                titulo = limpar_titulo(topico)
                data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if consultar_memoria(titulo):
                    print(f"⚠️ Já sei sobre: {titulo}. Pulando...\n")
                    continue

                sucesso = insert_memory(titulo, resposta, fonte, data)
                if sucesso:
                    log_aprendizado(titulo, resposta, fonte, data)
                    aprendidos_hoje.append(titulo)
                    print(f"✅ Aprendido: {titulo} (Fonte: {fonte})\n")
                else:
                    print(f"⚠️ Falha ao salvar: {titulo}")
            else:
                print(f"❌ Não foi possível pesquisar sobre: {topico}")

        if aprendidos_hoje:
            print(f"\n📚 [AUTO-LEARNING] Tópicos aprendidos neste ciclo:")
            for t in aprendidos_hoje:
                print(f"   • {t}")
        else:
            print("🛑 Nenhum aprendizado concluído neste ciclo.")

        print(f"\n🔁 Iniciando próximo ciclo...\n")
        time.sleep(2)
