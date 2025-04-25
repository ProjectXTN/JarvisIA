import sqlite3
from brain.learning.utils import caminho_banco

def consultar_emocoes(emocao, data_inicio=None, data_fim=None):
    try:
        from brain.learning.utils import caminho_banco
        conn = sqlite3.connect(caminho_banco())

        cursor = conn.cursor()

        if data_inicio and data_fim:
            cursor.execute("""
                SELECT evento, emocao, data, tags
                FROM memoria_emocional
                WHERE emocao = ?
                AND date(data) BETWEEN ? AND ?
                ORDER BY data DESC
                LIMIT 10
            """, (emocao, data_inicio, data_fim))
        else:
            cursor.execute("""
                SELECT evento, emocao, data, tags
                FROM memoria_emocional
                WHERE emocao = ?
                ORDER BY data DESC
                LIMIT 10
            """, (emocao,))

        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except Exception as e:
        print("[ERRO] Falha ao consultar emoções:", e)
        return []
