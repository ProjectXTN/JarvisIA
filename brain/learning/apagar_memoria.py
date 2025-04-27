import sqlite3
from brain.learning.utils import database_path

def apagar_memoria(topico):
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM conhecimento WHERE titulo = ?
    """, (topico.lower(),))

    conn.commit()
    conn.close()
    return True
