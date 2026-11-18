import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.audio import say, listen, ask
from brain.learning.insert_emotion import register_emotion
from brain.learning.normalize_emotions import normalize_emotion

def iniciar_reflexao(conteudo):
    try:
        emocao_raw = ask("Vamos registrar seu dia. Como você se sentiu hoje?")
        if not emocao_raw:
            return True
        emocao = normalize_emotion(emocao_raw)

        evento = ask("O que mais te marcou hoje?")
        if not evento:
            return True

        tags = ask("Quer adicionar alguma tag? Pode ser algo como trabalho, pessoal, estudo...")

        data = datetime.now().strftime("%Y-%m-%d")

        sucesso = register_emotion(evento, emocao, data, tags)

        if sucesso:
            say("Seu dia foi registrado com sucesso.")
        else:
            say("Tive um problema ao salvar suas lembranças.")

        return True

    except Exception as e:
        print(f"[ERRO] Modo reflexivo falhou: {e}")
        say("Ocorreu um erro ao tentar registrar seu dia.")
        return True


comandos_reflexao = {
    "quero registrar meu dia": iniciar_reflexao,
    "registrar meu dia": iniciar_reflexao,
    "como foi meu dia": iniciar_reflexao,
    "vamos fazer o diário": iniciar_reflexao,
}
