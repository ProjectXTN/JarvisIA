@echo off
chcp 65001 >nul
REM Instala tudo o que o Jarvis precisa num computador novo (Windows 10/11).
REM Dois cliques aqui, ou: install.bat
cd /d "%~dp0"
REM Sempre o PowerShell de 64 bits: aberto pelo instalador (32 bits), o Windows
REM escondia o nvidia-smi e o "Program Files" (placa NVIDIA e Chrome "não encontrados").
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
pause
