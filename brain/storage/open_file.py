import platform
import subprocess

def safe_open_file(filepath):
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["start", "", str(filepath)], shell=True)
        else:
            print(f"[INFO] Arquivo salvo em: {filepath}. Não abrindo automaticamente.")
    except Exception as e:
        print(f"[ERRO] Falha ao tentar abrir o arquivo: {e}")
