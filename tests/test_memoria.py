import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from comandos.comandos_memoria import comandos_memoria


def testar_aprender():
    comando = "aprenda que Python é uma linguagem de programação."
    print(f"\n[TESTE] Enviando: {comando}")
    comandos_memoria["aprenda que"](comando)

def testar_lembrar():
    comando = "o que você sabe sobre Python?"
    print(f"\n[TESTE] Enviando: {comando}")
    comandos_memoria["o que você sabe sobre"](comando)

def testar_atualizar():
    comando = "atualize Python para é uma linguagem poderosa."
    print(f"\n[TESTE] Enviando: {comando}")
    comandos_memoria["atualize"](comando)

def testar_esquecer():
    comando = "esqueça Python"
    print(f"\n[TESTE] Enviando: {comando}")
    comandos_memoria["esqueça"](comando)

if __name__ == "__main__":
    testar_aprender()
    testar_lembrar()
    testar_atualizar()
    testar_lembrar()
    testar_esquecer()
    testar_lembrar()
