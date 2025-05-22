from brain.websearch.websearch import search_web

if __name__ == "__main__":
    consulta = input("🧠 Digite o que quer pesquisar: ")
    resultado = search_web(consulta)
    print("\n📡 Resultados da Brave Search:\n")
    print(resultado)
