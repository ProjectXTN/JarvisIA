import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.audio import say, listen
from brain.learning.inserir_emocao import registrar_emocao
from brain.learning.normalizar_emocao import normalizar_emocao

def iniciar_reflexao(conteudo):
    try:
        say("Vamos registrar seu dia. Como você se sentiu hoje?")
        emocao_raw = listen()
        emocao = normalizar_emocao(emocao_raw)

        say("O que mais te marcou hoje?")
        evento = listen()

        say("Quer adicionar alguma tag? Pode ser algo como trabalho, pessoal, estudo...")
        tags = listen()

        data = datetime.now().strftime("%Y-%m-%d")

        sucesso = registrar_emocao(evento, emocao, data, tags)

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
