# Só a API de texto (server.py). O Jarvis de voz precisa de microfone, alto-falante
# e GPU do Windows e roda direto no venv (veja o README).
# O Ollama continua no Windows: passe OLLAMA_HOST=http://host.docker.internal:11500
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libportaudio2 libasound2 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV JARVIS_API_HOST=0.0.0.0 JARVIS_API_PORT=11600
EXPOSE 11600
CMD ["python", "server.py"]
