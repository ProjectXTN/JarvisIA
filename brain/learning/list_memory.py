import sqlite3
from brain.learning.utils import database_path

def listar_memoria():
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()

    cursor.execute("SELECT titulo FROM conhecimento")
    resultados = cursor.fetchall()
    conn.close()

    return [linha[0] for linha in resultados]
