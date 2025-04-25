import sqlite3
from datetime import datetime
from brain.learning.utils import caminho_banco

def aprendizados_de_hoje():
    conn = sqlite3.connect(caminho_banco())
    cursor = conn.cursor()

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT titulo FROM conhecimento WHERE data LIKE ?
    """, (f"{data_hoje}%",))

    resultados = cursor.fetchall()
    conn.close()

    return [titulo[0] for titulo in resultados] if resultados else []
