@echo off
chcp 65001 >nul
REM API do Jarvis para o site (pedromeireles.dev) e o painel: http://127.0.0.1:11600/painel
REM O site chega aqui pelo túnel https://jarvis.pedromeireles.dev -> 127.0.0.1:11600
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" server.py
