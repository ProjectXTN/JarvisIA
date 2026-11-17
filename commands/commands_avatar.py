import subprocess
import sys
from brain import avatar
from brain.audio import say


def show_avatar(query):
    """Abre a janela do avatar holográfico."""
    if avatar.show():
        say("Avatar na tela.")
    else:
        say("Não consegui abrir o avatar.")
    return True


def hide_avatar(query):
    """Fecha a janela do avatar."""
    avatar.hide()
    say("Avatar oculto.")
    return True


# Lista de (regex, função). "Esconder" vem antes para "feche o avatar" não
# cair no padrão de mostrar.
avatar_view_commands = [
    (r"\b(esconda|esconder|oculte|ocultar|feche|fechar|fecha|tire|tirar|remova|remover|desative|desativar)\b.*\b(avatar|holograma)\b", hide_avatar),
    (r"\b(mostre|mostrar|mostra|abra|abrir|abre|exiba|exibir|ative|ativar|quero ver|apareça|aparecer)\b.*\b(avatar|holograma|seu rosto)\b", show_avatar),
    (r"^(seu |o )?avatar$", show_avatar),
]


def generate_avatar(query):
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
            print(f"[ERROR] {result.stderr}")
            say("Houve um erro ao tentar gerar o vídeo.")
            return True

        say("Vídeo gerado com sucesso. Está na pasta de saída.")
        return True

    except Exception as e:
        print(f"[EXCEPTION] {e}")
        say("Ocorreu um erro inesperado.")
        return True

avatar_commands = {
    "gerar avatar": generate_avatar,
    "crie avatar": generate_avatar,
    "animar rosto": generate_avatar,
    "criar vídeo com avatar": generate_avatar
}
