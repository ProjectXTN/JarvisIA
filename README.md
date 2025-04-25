# Jarvis IA

Jarvis is an intelligent, sarcastic and futuristic AI assistant inspired by Tony Stark's iconic system.  
Built in Python, it supports voice interaction, vision models, command automation, emotional memory, music search, personal journaling, and much more — running entirely on your machine.

## 💻 Requirements

- Python 3.10 or higher  
- CUDA-compatible GPU (recommended for Whisper and LLaMA)  
- [Ollama](https://ollama.com/) for LLaMA 3.3 and LLaMA 3.2 Vision models  
- `ffmpeg`, `git`, `git-lfs`  
- Internet connection for web search and autonomous learning  

## 🧠 Features

- 🎙 **Wake Word Detection** — Activates with “Jarvis”
- 🧠 **Voice Activity Detection (VAD)** — Smart and natural listening
- 🗣 **Text-to-Speech** — Using Microsoft Edge TTS (Antonio Neural)
- 🎧 **Speech-to-Text** — Using OpenAI Whisper (large)
- 🧠 **LLaMA 3.3** — For contextual responses and memory-based conversation
- 👁 **LLaMA 3.2 Vision 90B** — High-precision image understanding
- 🧩 **Multi-command parsing** — e.g. “Open the folder and play music”
- 🔍 **Fallback to Web** — When unsure, it searches autonomously
- 🖼 **Image vision from local images folder**
- 💾 **Short-term memory** — Maintains session context
- 🧠 **Long-term persistent memory** — Stored with SQLite
- ❤️ **Emotional memory** — Stores what made you happy, sad, etc.
- 📘 **Reflective mode** — Voice-based journaling with emotional tagging
- 🧪 **Voice emotion detection** *(optional, WIP)*
- 🧠 **Autonomous learning** — Learns new facts from the internet
- 💻 **App launching** — Steam, Discord, VS Code, etc.
- 🖱 **System control** — Open folders, apps, browser
- 🎵 **Apple Music voice integration** — Open, search and play music
- 🧱 **Modular architecture** — Commands separated in the `comandos/` folder

---

## 🗂 Project Structure

```bash
jarvis/
├── comandos/                # Modular command files (music, system, folders, memory, etc.)
├── brain/                   # Core AI: audio, memory, utils, learning, dev
├── core/                    # Initialization & model loaders
├── imagens/                 # Optional: images for vision tasks
├── tests/                   # Vision testing scripts
├── jarvis.py                # Main executable script
├── requirements.txt         # Dependencies
└── README.md

🗣️ Voice Commands — Examples
"Jarvis, open the downloads folder"
"Jarvis, describe the image skyline"
"Jarvis, shut down"
"Jarvis, play Arctic Monkeys"
"Jarvis, search on the internet what is quantum computing"
"Jarvis, remember that coding made me happy"
"Jarvis, what made me happy this month?"
"Jarvis, let's write today's diary"

🖼️ Vision Mode
To trigger Vision 90B (more precise model):

"Describe the image skyline with details"
"Give me a precise description of the image"

If not triggered, it defaults to a faster LLaVA model.

🎵 Apple Music Integration
Jarvis can:

🎶 Open your library: "Jarvis, open Apple Music"

🔍 Search and play a song: "Jarvis, play Arctic Monkeys"

⏯ Pause, skip, resume: "Jarvis, pause music", "next track"

❤️ Emotional Memory
Register moments: "Jarvis, remember that dinner with Camila made me happy"

Query feelings: "Jarvis, what made me sad this week?"

Reflective journaling: "Jarvis, I want to write my day"

🤖 Developer Mode
Jarvis understands multi-step voice commands using regex parsing:

"Open the documents folder and then play music"
"Start the browser and search for weather"

🧠 Autonomous Learning
Jarvis can learn by searching the internet:

text
Copier
Modifier
"Jarvis, search what is quantum entanglement and learn it"
It will:

Search using web scraping

Summarize and store the knowledge in the database with source + timestamp

🚀 Getting Started
bash
Copier
Modifier
git clone https://github.com/ProjectXTN/Jarvis_IA.git
cd Jarvis_IA
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
🔒 Lock System
Jarvis uses a .lock file to avoid multiple instances running at the same time.

🧘 Voice Deactivation
Say:

"Jarvis, stop responding"

"Jarvis, silence"

"Jarvis, mute"

To return to passive listening mode.

Made with 💥 by Pedro