import subprocess
import sys
from brain.audio import say

def gerar_avatar(query):
    try:
        say("Gerando vídeo com o avatar. Isso pode levar alguns segundos.")

        command = [
            sys.executable,
            "C:/Projetos/SadTalker/inference.py",
            "--driven_audio", r"C:/Projetos/SadTalker/examples/driven_audio/chinese_news.wav",
            "--source_image", r"C:/Projetos/SadTalker/examples/source_image/art_1.png",
            "--checkpoint_dir", r"C:/Projetos/SadTalker/checkpoints",
            "--result_dir", r"C:/Projetos/avatares/output",
            "--verbose"
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[ERRO] {result.stderr}")
            say("Houve um erro ao tentar gerar o vídeo.")
            return True

        say("Vídeo gerado com sucesso. Está na pasta de saída.")
        return True

    except Exception as e:
        print(f"[EXCEPTION] {e}")
        say("Ocorreu um erro inesperado.")
        return True

comandos_avatar = {
    "gerar avatar": gerar_avatar,
    "crie avatar": gerar_avatar,
    "animar rosto": gerar_avatar,
    "criar vídeo com avatar": gerar_avatar
}
