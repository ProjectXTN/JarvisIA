import sqlite3
from brain.learning.utils import caminho_banco

def listar_memoria():
    conn = sqlite3.connect(caminho_banco())
    cursor = conn.cursor()

    cursor.execute("SELECT titulo FROM conhecimento")
    resultados = cursor.fetchall()
    conn.close()

    return [linha[0] for linha in resultados]
