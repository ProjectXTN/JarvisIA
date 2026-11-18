"""Prepara Whisper sem bloquear a abertura do Jarvis; retoma arquivos do cache."""
import os
import time
from faster_whisper.utils import download_model
from core.settings import WHISPER_MODEL

if __name__ == '__main__':
    for attempt in range(1, 4):
        try:
            print(f'[WHISPER] Baixando {WHISPER_MODEL}, tentativa {attempt}/3', flush=True)
            path = download_model(WHISPER_MODEL)
            if not os.path.isfile(os.path.join(path, 'model.bin')):
                raise RuntimeError('Download terminou sem model.bin')
            print(f'[WHISPER] Download concluído: {path}', flush=True)
            break
        except Exception as error:
            print(f'[WHISPER] Falha: {error}', flush=True)
            if attempt == 3:
                raise
            time.sleep(5)
