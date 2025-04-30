import sqlite3
import os
from datetime import datetime
from brain.learning.utils import database_path

def insert_memory(title, content, source="usuário", date=None):
    try:
        conn = sqlite3.connect(database_path())
        cursor = conn.cursor()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO conhecimento (titulo, conteudo, fonte, data)
            VALUES (?, ?, ?, ?)
        """, (title.lower(), content, source, date))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Failed to insert memory: {e}")
        return False
