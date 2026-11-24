@echo off
chcp 65001 >nul
title Compilando Jarvis com PyInstaller...
REM Gera dist\JarvisApp\JarvisApp.exe (pasta, não arquivo único: as bibliotecas
REM de GPU do Whisper são grandes demais para --onefile).
REM Os modelos (models\, Ollama, ComfyUI) e o .env ficam fora do executável:
REM copie a pasta models e o .env para dist\JarvisApp antes de usar.
cd /d %~dp0
if not exist venv\Scripts\pyinstaller.exe venv\Scripts\pip install pyinstaller
venv\Scripts\pyinstaller.exe --noconfirm --onedir --name JarvisApp ^
  --collect-all faster_whisper ^
  --collect-all ctranslate2 ^
  --collect-all kokoro_onnx ^
  --collect-all espeakng_loader ^
  --collect-binaries nvidia ^
  --collect-submodules brain ^
  --collect-submodules commands ^
  --add-data "vocabulario.txt;." ^
  --add-data "brain\avatar\static;brain\avatar\static" ^
  jarvis.py
echo.
echo Pronto: dist\JarvisApp\JarvisApp.exe
pause
