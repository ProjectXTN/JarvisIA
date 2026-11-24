"""Tabelas da Fase 7 no mesmo banco da memória (brain/learning/memoria_jarvis.db)."""
import sqlite3
import threading

from core.settings import MEMORY_DB

lock = threading.RLock()


def connect():
    conn = sqlite3.connect(MEMORY_DB, timeout=10)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criado TEXT, pergunta TEXT, resposta TEXT, processado INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS diario (
            data TEXT PRIMARY KEY, resumo TEXT, criado TEXT);
        CREATE TABLE IF NOT EXISTS humor (
            data TEXT PRIMARY KEY, humor TEXT, motivo TEXT);
        CREATE TABLE IF NOT EXISTS curiosidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT UNIQUE, motivo TEXT, origem TEXT, prioridade INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pendente', criado TEXT, estudado TEXT, resultado TEXT);
        CREATE TABLE IF NOT EXISTS contradicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memoria_a INTEGER, memoria_b INTEGER, explicacao TEXT, criado TEXT,
            resolvida INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS rotina (
            chave TEXT PRIMARY KEY, valor TEXT);
        CREATE TABLE IF NOT EXISTS opinioes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT UNIQUE, opiniao TEXT, motivo TEXT, criado TEXT, atualizado TEXT);
        """
    )
    return conn
