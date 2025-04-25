import sqlite3
from brain.learning.utils import caminho_banco

def registrar_emocao(evento, emocao, data, tags=None):
    try:
        conn = sqlite3.connect(caminho_banco())
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memoria_emocional (evento, emocao, data, tags)
            VALUES (?, ?, ?, ?)
        """, (evento, emocao, data, tags))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[ERRO] Falha ao registrar emoção:", e)
        return False
