import sqlite3
from brain.learning.utils import database_path

def query_emotions(emotion, start_date=None, end_date=None):
    try:
        conn = sqlite3.connect(database_path())

        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute("""
                SELECT evento, emocao, data, tags
                FROM memoria_emocional
                WHERE emocao = ?
                AND date(data) BETWEEN ? AND ?
                ORDER BY data DESC
                LIMIT 10
            """, (emotion, start_date, end_date))
        else:
            cursor.execute("""
                SELECT evento, emocao, data, tags
                FROM memoria_emocional
                WHERE emocao = ?
                ORDER BY data DESC
                LIMIT 10
            """, (emotion,))

        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print("[ERROR] Failed to query emotions:", e)
        return []