import sqlite3
from brain.learning.utils import caminho_banco

def apagar_memoria(topico):
    conn = sqlite3.connect(caminho_banco())
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM conhecimento WHERE titulo = ?
    """, (topico.lower(),))

    conn.commit()
    conn.close()
    return True
