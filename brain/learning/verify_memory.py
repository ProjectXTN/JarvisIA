import sqlite3
from brain.learning.utils import database_path

def memoria_ja_existe(titulo):
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM conhecimento WHERE titulo = ?", (titulo.lower(),))
    existe = cursor.fetchone() is not None

    conn.close()
    return existe
