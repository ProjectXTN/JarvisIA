import os
import re
import unicodedata
import subprocess
from jsbeautifier import beautify

PASTA_CODIGOS = "codigos"
os.makedirs(PASTA_CODIGOS, exist_ok=True)

def detectar_linguagem(codigo):
    if re.search(r"def\s+\w+\s*\(.*\):", codigo):
        return "py"
    elif re.search(r"function\s+\w+\s*\(.*\)", codigo):
        return "js"
    elif re.search(r"#include\s+<.*>", codigo):
        return "c"
    elif re.search(r"public\s+class\s+\w+", codigo):
        return "java"
    elif re.search(r"<html>|<!DOCTYPE html>", codigo, re.IGNORECASE):
        return "html"
    elif re.search(r"^SELECT\s+.*\s+FROM", codigo, re.IGNORECASE):
        return "sql"
    elif re.search(r"\.style|{[^}]*}", codigo):
        return "css"
    return "txt"

def limpar_nome_arquivo(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r"[^\w\s-]", "", texto)
    texto = re.sub(r"\s+", "_", texto)
    return texto.lower().strip("_")

def formatar_codigo(codigo, linguagem):
    if linguagem == "py":
        try:
            temp = "temp.py"
            with open(temp, "w", encoding="utf-8") as f:
                f.write(codigo)
            subprocess.run(["black", temp, "--quiet"], check=True)
            with open(temp, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[BLACK] Erro: {e}")
            return codigo

    elif linguagem in ["js", "html", "css"]:
        try:
            temp = f"temp.{linguagem}"
            with open(temp, "w", encoding="utf-8") as f:
                f.write(codigo)
            subprocess.run(["prettier", "--write", temp], check=True)
            with open(temp, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[PRETTIER] Falha, tentando beautify: {e}")
            try:
                return beautify(codigo)
            except Exception as e:
                print(f"[BEAUTIFY] Falhou também: {e}")
                return codigo

    return codigo

def extrair_e_salvar_codigo(resposta_completa, titulo="codigo"):
    blocos = re.findall(r"```(?:\w+\n)?(.*?)```", resposta_completa, re.DOTALL)
    if not blocos:
        print("[DEV] Nenhum bloco de código encontrado.")
        return None

    codigo = "\n\n".join(bloco.strip() for bloco in blocos)
    linguagem = detectar_linguagem(codigo)

    # Testa compilação antes de formatar, se for Python
    if linguagem == "py":
        try:
            compile(codigo, "<string>", "exec")
        except Exception as e:
            print(f"[SYNTAX] Erro de sintaxe no código Python: {e}")

    try:
        codigo = formatar_codigo(codigo, linguagem)
    except Exception as e:
        print(f"[FORMAT] Falha na formatação: {e}")

    nome_limpo = limpar_nome_arquivo(titulo or "codigo")
    nome_arquivo = f"{nome_limpo}.{linguagem}"
    caminho = os.path.join(PASTA_CODIGOS, nome_arquivo)

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(codigo.strip())

    print(f"[DEV] Código salvo como: {caminho}")
    return caminho
