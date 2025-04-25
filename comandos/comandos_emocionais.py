import re
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.audio import say
from brain.learning.inserir_emocao import registrar_emocao
from brain.learning.consultar_emocao import consultar_emocoes
from brain.learning.normalizar_emocao import normalizar_emocao
from brain.learning.interpretar_data import interpretar_intervalo_data



def registrar_lembranca_emocional(conteudo):
    try:
        match = re.search(
            r"(lembre que|lembra que|registre que|registro que) (.+?) (me deixou|me fez sentir|me deixa|me deixa com|eu gosto) (.+?)(?: em (.+))?$",
            conteudo,
            re.IGNORECASE,
        )
        if match:
            evento = match.group(2).strip()
            emocao_raw = match.group(4).strip().lower()
            emocao = normalizar_emocao(emocao_raw)

            data = (
                match.group(5)
                if match.group(5)
                else datetime.now().strftime("%Y-%m-%d")
            )
            tags = None

            sucesso = registrar_emocao(evento, emocao, data, tags)

            if sucesso:
                say(f"Lembrança registrada com emoção '{emocao}'.")
            else:
                say("Não consegui registrar essa lembrança.")
            return True
        else:
            print("[DEBUG] Regex não bateu.")
            say("Não entendi bem o que você quer que eu lembre com emoção.")
            return True
    except Exception as e:
        print(f"[ERRO] Falha no registro de lembrança emocional: {e}")
        say("Ocorreu um erro ao tentar registrar sua lembrança.")
        return True


def consultar_lembranca_emocional(conteudo):
    try:
        print(f"[DEBUG] Conteúdo recebido para consulta emocional: {conteudo}")
        match = re.search(
            r"(?:o que\s+|que\s+|)?me\s+(fez feliz|deixou feliz|deixou triste|estressou|marcou|irritou)(.*)?",
            conteudo,
            re.IGNORECASE,
        )
        if match:
            emocao_raw = match.group(1).strip().lower()
            complemento = match.group(2).strip().lower() if match.group(2) else ""
            emocao = normalizar_emocao(emocao_raw)
            data_inicio, data_fim = interpretar_intervalo_data(complemento)

            print(f"[DEBUG] Emoção detectada: {emocao}")
            print(f"[DEBUG] Intervalo de data: {data_inicio} -> {data_fim}")

            resultados = consultar_emocoes(emocao, data_inicio, data_fim)
            print(f"[DEBUG] Resultados encontrados: {resultados}")

            if resultados:
                frases = [f"- {r[0]} (em {r[2]})" for r in resultados]
                resposta = "\n".join(frases)
                say(f"Esses eventos te causaram '{emocao}':\n{resposta}")
            else:
                say(f"Não encontrei lembranças relacionadas a '{emocao}' nesse período.")
            return True
        else:
            print("[DEBUG] Nenhuma emoção reconhecida na frase.")
            say("Não consegui entender qual emoção ou período você quer que eu consulte.")
            return True
    except Exception as e:
        print(f"[ERRO] Falha ao consultar lembrança emocional: {e}")
        say("Ocorreu um erro ao tentar lembrar disso.")
        return True


comandos_emocionais = {
    "lembre que": registrar_lembranca_emocional,
    "lembra que": registrar_lembranca_emocional,
    "registre que": registrar_lembranca_emocional,
    "me fez feliz": consultar_lembranca_emocional,
    "me deixou triste": consultar_lembranca_emocional,
    "me estressou": consultar_lembranca_emocional,
    "me marcou": consultar_lembranca_emocional,
    "me irritou": consultar_lembranca_emocional,
    "me deixou feliz": consultar_lembranca_emocional,
}
