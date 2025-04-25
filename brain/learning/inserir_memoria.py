import sqlite3
import os
from datetime import datetime
from brain.learning.utils import caminho_banco

def inserir_memoria(titulo, conteudo, fonte="usuário", data=None):
    try:
        conn = sqlite3.connect(caminho_banco())
        cursor = conn.cursor()

        if data is None:
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO conhecimento (titulo, conteudo, fonte, data)
            VALUES (?, ?, ?, ?)
        """, (titulo.lower(), conteudo, fonte, data))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao inserir memória: {e}")
        return False
