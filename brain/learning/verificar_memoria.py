import sqlite3
from brain.learning.utils import caminho_banco

def memoria_ja_existe(titulo):
    conn = sqlite3.connect(caminho_banco())
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM conhecimento WHERE titulo = ?", (titulo.lower(),))
    existe = cursor.fetchone() is not None

    conn.close()
    return existe
