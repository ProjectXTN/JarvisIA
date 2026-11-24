@echo off
chcp 65001 >nul
REM API do Jarvis para o site (pedromeireles.dev) e o painel: http://127.0.0.1:11600/painel
REM Abre também o túnel do Cloudflare (https://jarvis.pedromeireles.dev -> 127.0.0.1:11600),
REM igual à função "server" do $PROFILE do PowerShell.
cd /d "%~dp0"
if "%JARVIS_CLOUDFLARED%"=="" set JARVIS_CLOUDFLARED=C:\Tools\cloudflared.exe
if "%JARVIS_TUNNEL%"=="" set JARVIS_TUNNEL=jarvis-tunnel
tasklist /FI "IMAGENAME eq cloudflared.exe" | find /I "cloudflared.exe" >nul
if errorlevel 1 (
    if exist "%JARVIS_CLOUDFLARED%" (
        start "Jarvis - tunel" /min "%JARVIS_CLOUDFLARED%" tunnel run %JARVIS_TUNNEL%
    ) else (
        echo Tunel nao aberto: nao achei %JARVIS_CLOUDFLARED%
    )
)
"%~dp0venv\Scripts\python.exe" server.py
