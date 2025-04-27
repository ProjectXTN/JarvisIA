FROM python:3.13-slim

# Dependências do sistema
RUN apt update && apt install -y \
    ffmpeg \
    espeak-ng \
    libespeak-ng1 \
    libasound2 \
    alsa-utils \
    build-essential \
    git \
    wget \
    curl \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install piper-phonemize

# Comando padrão
CMD ["python", "jarvis.py"]
