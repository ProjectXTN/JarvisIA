import sqlite3
import os

def criar_banco():
    db_path = os.path.abspath('memoria_jarvis.db')
    print("📂 Banco de dados usado:", db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabela de conhecimentos gerais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conhecimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            conteudo TEXT,
            fonte TEXT,
            data TEXT
        )
    """)

    # Nova tabela: Memória Emocional
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
    print("✅ Tabelas criadas (ou já existentes).")

def listar_tabelas():
    conn = sqlite3.connect('memoria_jarvis.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()

    for tabela in tabelas:
        print("📁 Tabela encontrada:", tabela[0])

    conn.close()

if __name__ == "__main__":
    criar_banco()
    listar_tabelas()
