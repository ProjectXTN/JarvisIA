@echo off
chcp 65001 >nul
REM Instala tudo o que o Jarvis precisa num computador novo (Windows 10/11).
REM Dois cliques aqui, ou: install.bat
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
pause
