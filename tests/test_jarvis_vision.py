import sys
import os

# Garante que a raiz do projeto está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from jarvis_vision import descrever_imagem

# Nome da imagem que você quer testar (deixe na pasta Pictures)
nome_imagem = "boxe.jpg"
caminho_imagem = os.path.expanduser(f"~/Pictures/{nome_imagem}")

if not os.path.exists(caminho_imagem):
    print(f"Imagem não encontrada: {caminho_imagem}")
else:
    print(f"Testando descrição da imagem: {nome_imagem}")
    descricao = descrever_imagem(caminho_imagem)
    print("\nJarvis Vision respondeu:\n")
    print(descricao)
