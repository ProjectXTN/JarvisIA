# Jarvis IA

Jarvis is an intelligent, sarcastic, and futuristic AI assistant inspired by Tony Stark's iconic system.
Built in Python, it supports voice interaction, vision models, command automation, emotional memory, music search, personal journaling, and much more — running entirely on your machine.

🗣️ Important: All Jarvis voice commands and responses are in Brazilian Portuguese (PT-BR).

## 💻 Requirements
Python 3.10 or higher

CUDA-compatible GPU (recommended for Whisper and LLaMA)

Ollama for LLaMA 3.3 and LLaMA 3.2 Vision models

ffmpeg, git, git-lfs

Internet connection for web search and autonomous learning

## 🧠 Features
🎙 Wake Word Detection — Activates with “Jarvis”

🧠 Voice Activity Detection (VAD) — Smart and natural listening

🗣 Text-to-Speech — Using Microsoft Edge TTS (Antonio Neural)

🎧 Speech-to-Text — Using OpenAI Whisper (large)

🧠 LLaMA 3.3 — For contextual responses and memory-based conversation

👁 LLaMA 3.2 Vision 90B — High-precision image understanding

🧩 Multi-command parsing — e.g. “Open the folder and play music”

🔍 Fallback to Web — When unsure, it searches autonomously

🖼 Image vision from local images folder

💾 Short-term memory — Maintains session context

🧠 Long-term persistent memory — Stored with SQLite

❤️ Emotional memory — Stores what made you happy, sad, etc.

📘 Reflective mode — Voice-based journaling with emotional tagging

🧪 Voice emotion detection (optional, WIP)

🧠 Autonomous learning — Learns new facts from the internet

💻 App launching — Steam, Discord, VS Code, etc.

🖱 System control — Open folders, apps, browser

🎵 Apple Music voice integration — Open, search and play music

🧱 Modular architecture — Commands separated in the comandos/ folder

##  🗂 Project Structure

jarvis/
├── comandos/                # Modular command files (music, system, folders, memory, etc.)
├── brain/                   # Core AI: audio, memory, utils, learning, dev
├── core/                    # Initialization & model loaders
├── imagens/                 # Optional: images for vision tasks
├── tests/                   # Vision testing scripts
├── jarvis.py                # Main executable script
├── requirements.txt         # Dependencies
└── README.md

## 🗣️ Voice Commands — Examples (in Portuguese)
"Jarvis, abra a pasta de downloads"
"Jarvis, descreva a imagem skyline"
"Jarvis, desligar"
"Jarvis, toque Arctic Monkeys"
"Jarvis, pesquise na internet o que é computação quântica"
"Jarvis, lembre que programar me deixou feliz"
"Jarvis, o que me deixou feliz este mês?"
"Jarvis, vamos escrever o diário de hoje"

## 🖼️ Vision Mode
To trigger Vision 90B (more precise model):

"Descreva a imagem skyline com detalhes"
"Me dê uma descrição precisa da imagem"

If not triggered, it defaults to a faster LLaVA model.

## 🎵 Apple Music Integration
Jarvis can:

🎶 Open your library: "Jarvis, abra o Apple Music"
🔍 Search and play a song: "Jarvis, toque Arctic Monkeys"
⏯ Pause, skip, resume: "Jarvis, pause a música", "próxima música"

## ❤️ Emotional Memory
Register moments: "Jarvis, lembre que o jantar com a Camila me deixou feliz"
Query feelings: "Jarvis, o que me deixou triste essa semana?"
Reflective journaling: "Jarvis, quero escrever sobre meu dia"

## 🤖 Developer Mode
Jarvis understands multi-step voice commands using regex parsing:

"Abra a pasta de documentos e depois toque música"
"Inicie o navegador e pesquise o clima"

## 🧠 Autonomous Learning
Jarvis can learn by searching the internet:

"Jarvis, pesquise o que é entrelaçamento quântico e aprenda"

It will:

Search using web scraping

Summarize and store the knowledge in the database with source + timestamp

## 🚀 Getting Started

git clone https://github.com/ProjectXTN/Jarvis_IA.git
cd Jarvis_IA
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## 🔒 Lock System
Jarvis uses a .lock file to avoid multiple instances running at the same time.

## 🧘 Voice Deactivation
Say:

"Jarvis, pare de responder"
"Jarvis, silêncio"
"Jarvis, mutar"

To return to passive listening mode.

## Made with 💥 by Pedro MEIRELES

## 📢 Observação:
Todos os comandos e falas do Jarvis são em português do Brasil (PT-BR).
Para uma experiência fluida, fale naturalmente em português.