FROM python:3.13-slim

# System dependencies
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

# Working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install piper-phonemize

# Default command
CMD ["python", "jarvis.py"]
