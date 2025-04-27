import sqlite3
from brain.learning.utils import database_path

def register_emotion(event, emotion, date, tags=None):
    try:
        conn = sqlite3.connect(database_path())
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memoria_emocional (evento, emocao, data, tags)
            VALUES (?, ?, ?, ?)
        """, (event, emotion, date, tags))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[ERROR] Failed to register emotion:", e)
        return False
