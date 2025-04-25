@echo off
chcp 65001 >nul
title Compilando Jarvis com PyInstaller...
echo ======================================
echo 🔧 Iniciando compilação do Jarvis...
echo ======================================

REM Caminho relativo do ambiente virtual
set VENV=venv\Scripts
set PYINSTALLER=%VENV%\pyinstaller.exe

REM Caminhos dos arquivos necessários do Whisper
set MEL_FILTERS=venv\Lib\site-packages\whisper\assets\mel_filters.npz
set MULTILINGUAL=venv\Lib\site-packages\whisper\assets\multilingual.tiktoken

REM Compilação
"%PYINSTALLER%" --noconfirm --onefile --name JarvisApp ^
--add-data "%MEL_FILTERS%;whisper/assets" ^
--add-data "%MULTILINGUAL%;whisper/assets" ^
--add-data "utils_datetime.py;." ^
jarvis.py

echo.
echo ✅ Compilação concluída! O executável está em dist\JarvisApp.exe
pause
