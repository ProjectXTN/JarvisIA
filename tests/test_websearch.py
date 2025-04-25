from brain.websearch import buscar_na_web

if __name__ == "__main__":
    consulta = input("🧠 Digite o que quer pesquisar: ")
    resultado = buscar_na_web(consulta)
    print("\n📡 Resultados da Brave Search:\n")
    print(resultado)
