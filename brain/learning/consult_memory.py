import sqlite3
from brain.learning.utils import database_path

def consultar_memoria(topico):
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()

    print(f"[DEBUG] Consultando por: '{topico.lower()}'")

    cursor.execute("SELECT conteudo, fonte, data FROM conhecimento WHERE titulo = ?", (topico.lower(),))
    resultado = cursor.fetchone()

    conn.close()
    return resultado if resultado else None

def consultar_tudo():
    try:
        conn = sqlite3.connect(database_path())
        cursor = conn.cursor()

        cursor.execute("SELECT titulo, conteudo FROM conhecimento ORDER BY data DESC")
        resultados = cursor.fetchall()

        conn.close()
        return resultados if resultados else []

    except Exception as e:
        print(f"[ERRO] Falha ao consultar tudo: {e}")
        return []
