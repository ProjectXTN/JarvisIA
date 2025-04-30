import sqlite3
from brain.learning.utils import database_path

def atualizar_memoria(topico, novo_conteudo):
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE conhecimento SET conteudo = ? WHERE titulo = ?
    """, (novo_conteudo, topico.lower()))

    conn.commit()
    conn.close()
    return True
