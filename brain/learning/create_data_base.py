import sqlite3
import os

def create_database():
    db_path = os.path.abspath('memoria_jarvis.db')
    print("📂 Database used:", db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # General knowledge table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conhecimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            conteudo TEXT,
            fonte TEXT,
            data TEXT
        )
    """)

    # New table: Emotional Memory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memoria_emocional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento TEXT NOT NULL,
            emocao TEXT,
            data TEXT,
            tags TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Tables created (or already existing).")

def list_tables():
    conn = sqlite3.connect('memoria_jarvis.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        print("📁 Table found:", table[0])

    conn.close()

if __name__ == "__main__":
    create_database()
    list_tables()
