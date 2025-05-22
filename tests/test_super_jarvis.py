import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from brain.pipeline.super_jarvis import super_jarvis_query

def main():
    print("=== Teste Jarvis: RAG + Web ===")
    while True:
        pergunta = input("\nFaça sua pergunta para o Jarvis ('sair' para encerrar):\n> ")
        if pergunta.strip().lower() in ['sair', 'exit', 'quit']:
            print("Encerrando teste.")
            break

        print("\n[🧠] Processando...")
        resposta = super_jarvis_query(pergunta)
        print("\n[Jarvis Respondeu]\n---------------------")
        print(resposta)
        print("---------------------")

if __name__ == "__main__":
    main()
