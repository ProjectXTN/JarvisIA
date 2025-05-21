import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from commands.commands_traduction import execute_traducao_legenda

def testar_traducao():
    print("\n=== TESTE DE TRADUÇÃO DE LEGENDA ===")
    nome_arquivo = input("Digite o nome do arquivo (sem .srt): ").strip()
    idioma = input("Digite o idioma de destino (ex: português, inglês, pt, en): ").strip()

    comando = f"traduzir o arquivo {nome_arquivo} para {idioma}"
    print(f"\n[TESTE] Enviando: {comando}")
    resultado = execute_traducao_legenda(comando, speak=False)
    print(f"\nResultado: {resultado}")

if __name__ == "__main__":
    testar_traducao()
