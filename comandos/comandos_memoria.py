import re
import string
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.learning.inserir_memoria import inserir_memoria
from brain.learning.consultar_memoria import consultar_memoria
from brain.learning.atualizar_memoria import atualizar_memoria
from brain.learning.apagar_memoria import apagar_memoria
from brain.learning.listar_memoria import listar_memoria
from brain.learning.verificar_memoria import memoria_ja_existe
from comandos.comandos_pesquisa import executar_pesquisa
from brain.learning.consultar_aprendizados_do_dia import aprendizados_de_hoje
from brain.audio import say,listen

def aprender(conteudo):
    match = re.search(r"aprenda que (.+)", conteudo)
    if match:
        dado = match.group(1).strip()

        partes = dado.split(" é ", 1)
        if len(partes) == 2:
            topico = partes[0].strip().lower()
            informacao = "é " + partes[1].strip()

            if memoria_ja_existe(topico):
                say("Eu já sabia disso, mas obrigado por reforçar!")
                return True

            if inserir_memoria(topico, informacao):
                say("Aprendido com sucesso.")
            else:
                say("Algo deu errado ao tentar aprender isso.")
        else:
            say("Não consegui entender o que devo aprender.")
        return True
    return False



def lembrar(conteudo):
    match = re.search(r"(o que você sabe sobre|lembra sobre) (.+)", conteudo)
    if match:
        assunto = match.group(2).strip().rstrip("?.,!").lower()
        resultado = consultar_memoria(assunto)
        if resultado:
            conteudo, fonte, data = resultado
            say(f"Sim, eu sei que {conteudo} (Fonte: {fonte}, Aprendido em {data})")
        else:
            say("Não tenho essa informação guardada.")
        return True
    return False

def atualizar_info(conteudo):
    match = re.search(r"atualize (.+) para (.+)", conteudo)
    if match:
        antigo = match.group(1).strip()
        novo = match.group(2).strip()
        if atualizar_memoria(antigo, novo):
            say("Informação atualizada.")
        else:
            say("Não consegui atualizar isso.")
        return True
    return False

def esquecer(conteudo):
    match = re.search(r"esqueça (.+)", conteudo)
    if match:
        dado = match.group(1).strip()
        if apagar_memoria(dado):
            say("Informação esquecida.")
        else:
            say("Não consegui encontrar isso para esquecer.")
        return True
    return False

def listar_tudo(conteudo):
    titulos = listar_memoria()
    if titulos:
        lista = ", ".join(titulos)
        say(f"Eu sei sobre: {lista}.")
    else:
        say("Ainda não aprendi nada.")
    return True

def aprender_da_web(conteudo):
    match = re.search(r"(pesquise|procure|busque)\s+sobre\s+(.+?)(?:\s+e\s+(aprenda|aprenda isso))?$", conteudo, re.IGNORECASE)
    if match:
        assunto = match.group(2).strip()

        # Agora retorna (resposta, fonte_principal)
        resposta, fonte = executar_pesquisa(f"O que é {assunto}?")
        if not resposta or "Erro" in resposta:
            say("Não consegui encontrar nada relevante na internet.")
            return True

        say(f"Deseja que eu memorize isso como conhecimento sobre {assunto}?")

        confirmacao = listen().lower()
        if "sim" in confirmacao or "pode" in confirmacao:
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Limpeza do título
            titulo_limpo = assunto.strip().lower()
            titulo_limpo = re.sub(r"\be\b$", "", titulo_limpo).strip()
            titulo_limpo = titulo_limpo.strip(string.punctuation)

            sucesso = inserir_memoria(titulo_limpo, resposta, fonte, data)

            if sucesso:
                say(f"Informação aprendida com sucesso a partir da fonte {fonte}.")
            else:
                say("Não consegui armazenar essa informação.")
        else:
            say("Tudo bem, não vou memorizar isso.")
        return True
    return False

def aprendizados_hoje(conteudo):
    titulos = aprendizados_de_hoje()
    if titulos:
        lista = ", ".join(titulos)
        say(f"Hoje eu aprendi sobre: {lista}.")
    else:
        say("Hoje ainda não aprendi nada novo.")
    return True



comandos_memoria = {
    "aprenda que": aprender,
    "o que você sabe sobre": lembrar,
    "lembra sobre": lembrar,
    "atualize": atualizar_info,
    "esqueça": esquecer,
    "liste tudo o que você sabe": listar_tudo,
    "liste tudo que você sabe": listar_tudo,
    "pesquise sobre": aprender_da_web,
    "o que você aprendeu hoje": aprendizados_hoje,
    "o que você aprendeu": aprendizados_hoje 
}
