## Jarvis IA

Jarvis is an intelligent, sarcastic, and futuristic AI assistant inspired by Tony Stark's iconic system.Built entirely in Python, it supports voice interaction, vision models, autonomous learning, weather reports, emotional memory, music search, journaling, and much more — running 100% on your local machine.

## 🗣️ Important: All Jarvis voice commands are in Brazilian Portuguese (PT-BR).

## 💻 Requirements

Python 3.10 or higher

CUDA-compatible GPU (recommended for Whisper and LLaMA)

Ollama for LLaMA 3.3 and LLaMA 3.2 Vision models

ffmpeg, git, git-lfs

Brave Search API Key (for web searches)

OpenWeather API Key (for weather forecasts)

Internet connection (for searches and autonomous learning)

## 🧠 Features

🎙 Wake Word Detection — Activates with “Jarvis” or variations (e.g., "Javis")

🧠 Voice Activity Detection (VAD) — Natural listening using smart silence detection

🗣 Text-to-Speech — Using Google TTS API

🎧 Speech-to-Text — Using OpenAI Whisper/Fast-Whisper (large model optimized for PT-BR)

🧠 LLaMA 3.3 — For deep contextual conversations and memory-based learning

👁 LLaMA 3.2 Vision 90B — For detailed image analysis and description

🌦️ Weather Forecast — Voice-based weather queries by city and country

🔍 RAG + Autonomous Internet Search — Now hybrid: Combines local LLM, memory, and real-time web search for up-to-date answers!

🖼 Local Image Vision — Scan and describe images stored locally

🧠 AI Image Generation — Create stunning AI-generated images based on voice prompts using Stable Diffusion

💾 Session Memory — Maintains context during conversations

🧠 Long-Term Memory — Persists important facts, feelings, and events via SQLite

❤️ Emotional Memory — Records happiness, sadness, anger, and more

📘 Reflective Mode — Journaling about daily experiences with emotional tagging

🧪 (WIP) Voice emotion recognition

🧠 Autonomous Learning — Searches, summarizes, and learns new information online

💻 App Automation — Launch Steam, Discord, VS Code, browsers, and more

💜 OS Control — Open folders, close programs, manage files

🎵 Apple Music Voice Integration — Search and control your music library

🧱 Modular Architecture — Commands split into organized modules (commands/)

🌎 SRT Subtitle Translation — Translate subtitle files (.srt) to any language by voice command, preserving timing and format.


## 🗂 Project Structure

jarvis/
├── comandos/                # Modular command files (music, system, folders, memory, search, weather, etc.)
├── brain/                   # Core modules: audio, memory, utils, learning, weatherAPI
├── core/                    # Initialization and model bootstrapping
├── imagens/                 # (Optional) Images for vision analysis
├── tests/                   # Testing scripts (vision, weather, etc.)
├── jarvis.py                # Main executable
├── requirements.txt         # Dependencies
└── README.md

## 🗣️ Voice Commands — Examples (in Portuguese)

"Jarvis, abrir a pasta de downloads"

"Jarvis, descreva a imagem skyline"

"Jarvis, desligar"

"Jarvis, tocar Arctic Monkeys"

"Jarvis, pesquisar o que é computação quântica"

"Jarvis, lembre que programar me deixou feliz"

"Jarvis, o que me deixou feliz este mês?"

"Jarvis, como está o clima em Paris?"

"Jarvis, previsão do tempo para São Paulo"

"Jarvis, traduzir o arquivo (Name of ile) para (langue)"

## 🖼️ Vision Mode

To trigger Vision 90B model (for precise descriptions):

"Descreva a imagem skyline com detalhes"

"Quero uma análise precisa da imagem"

Fallback to faster vision models if necessary.

🚀 What's New: RAG + Web Search (Hybrid Intelligence)
Smart Decision Making:
Jarvis analyzes every question and decides:

If it’s time-sensitive or about current events, it automatically performs a live web search, parses results, and feeds context to the LLM before answering.

If the answer is timeless (history, science, definitions), it responds instantly using its own knowledge.

Languages Supported:
Regex and heuristics are multi-lingual, so Jarvis intelligently detects queries in Portuguese, English, or French and fetches real-time answers when needed.

No more “Biden em 2025”!
If you ask “Who is the president of the USA?” Jarvis will always give you the most current answer, not just what’s in its model.

## 🧠 How RAG + Web Search Works
Question Received:
User asks anything by voice or text.

Intent & Context Detection:
Jarvis uses regex and heuristics to decide if the answer should come from memory or if it’s time-sensitive (current events, “who is...”, “quanto é o dólar”, etc).

Hybrid Answering:

Timeless? → Responds instantly from LLaMA’s memory.

Current/Time-sensitive? → Runs real-time Brave Search, parses the web, summarizes context, then LLaMA 3.3 generates a rich answer with references.

Conversation stays fast, relevant, and never obsolete!

## 🌐 Example Queries
"Quem é o presidente dos Estados Unidos?"
→ Busca web + resposta atualizada

"Qual a cotação do euro hoje?"
→ Busca web + resposta atualizada

"Me conte a história de Napoleão"
→ LLM responde direto (não vai pra internet)

"Jarvis, previsão do tempo para Lisboa amanhã"
→ Busca web (se necessário) + dados atualizados

## 🌦️ Weather Forecast

Ask naturally about the weather, including for the next days:

"Jarvis, previsão do tempo em Lisboa"  
"Jarvis, como está o clima em São Paulo?"  
"Jarvis, previsão do tempo para a próxima semana em Nova York"  
"Jarvis, meteo em Paris nos próximos dias"

Jarvis will:
- Detect if you're asking about today's weather or a forecast.
- Automatically ask for the country if necessary.
- Understand requests like "semana que vem", "amanhã", or "próximos dias".
- Fetch accurate, day-by-day weather information using the OpenWeather API.
- Handle incomplete questions by politely requesting missing information (city or country).

If no specific city is detected, Jarvis defaults to a configured location (Lexy by default).

Jarvis will intelligently ask for the country if needed and retrieve a detailed weather report using OpenWeather API.

## 🎵 Apple Music Integration

Jarvis can:

🎶 Open Apple Music app: "Jarvis, abra o Apple Music"

🔍 Search and play songs: "Jarvis, toque Arctic Monkeys"

⏯ Pause, skip, resume: "Jarvis, pause a música", "próxima música", "continuar música"

## ❤️ Emotional Memory

Register positive/negative events: "Jarvis, lembre que jantei com Camila e fiquei feliz"

Retrieve emotional states: "Jarvis, o que me deixou triste essa semana?"

Voice-based journaling: "Jarvis, quero escrever sobre meu dia"

## 🧬 Developer Mode

Jarvis can chain multiple commands in a single voice phrase:

"Abra a pasta de imagens e depois toque uma música"

"Inicie o navegador e procure sobre inteligência artificial"

## 🧠 Autonomous Learning
Jarvis can:

Search the internet autonomously

Summarize new knowledge

Store learned facts with sources and dates into the database

Example:

"Jarvis, learn about quantum entanglement."

## 🖼️ AI Image Generation
Jarvis can:

Generate AI images based on voice prompts

Use Stable Diffusion locally (with support for high-resolution images)

Automatically refine and upscale images when necessary

Example:

"Jarvis, create an ultra-realistic 4K image of a cyberpunk futuristic city with lots of neon and people."

"Jarvis, draw a medieval castle with a dragon flying above."

The generated images are automatically saved under:

## 🌎 SRT Subtitle Translation

Quickly translate any `.srt` subtitle file to your preferred language — just with your voice.

**Example voice commands:**

"Jarvis, traduzir o arquivo legenda para inglês"

"Jarvis, traduzir o arquivo cs50 para espanhol"

"Jarvis, traduzir o arquivo my_subs para português"

**How it works:**
- Say the command specifying the file name (without `.srt`) and the target language.
- Jarvis finds the file in your Documents folder.
- The translation is handled by your local LLM, preserving all subtitle timings and formatting.
- The translated subtitle is saved as a new `.srt` file (e.g., `legenda-ingles.srt`).

**Jarvis ensures:**
- Timing and subtitle numbering are always preserved.
- Only the dialogue text is translated — no explanation or commentary.
- You can translate to any language supported by your LLM.

Perfect for movies, online courses, or sharing educational content in multiple languages!

## 🚀 Getting Started

git clone https://github.com/ProjectXTN/Jarvis_IA.git

cd Jarvis_IA

python -m venv venv

venv\Scripts\activate  # or source venv/bin/activate on Linux/Mac

pip install -r requirements.txt

Make sure your .env file contains your API Keys:

BRAVE_API_KEY=your_brave_api_key

OPENWEATHER_API_KEY=your_openweather_api_key

## 🔒 Lock System

Jarvis uses a .lock file system to prevent multiple instances from running simultaneously.

## 💌 Voice Deactivation

Say:

"Jarvis, pare de responder"

"Jarvis, silênço"

"Jarvis, mutar"

Jarvis will return to passive mode until called again.

Made with 💥 by Pedro MEIRELES

## 📢 Note:

All commands and conversations with Jarvis are fully in Brazilian Portuguese (PT-BR).For the best experience, speak naturally and clearly.

