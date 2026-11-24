## Jarvis IA

Jarvis is a local voice assistant inspired by Tony Stark's system. It listens, thinks and speaks on your own PC: speech recognition, the language model, the voice and image generation all run locally. Internet is used only for web search, news, weather and music.

**All voice commands and answers are in Brazilian Portuguese (PT-BR).**

The refactoring plan and a log of every change live in [PLANO.md](PLANO.md).

## 💻 Requirements

- Windows 10/11, Python 3.10+ (tested with the project `venv`)
- NVIDIA GPU with 24 GB (developed on an RTX 4090)
- [Ollama](https://ollama.com) with:
  ```
  ollama pull gemma4:26b             # conversation, tools and vision
  ollama pull qwen3-embedding:0.6b   # semantic memory and documents (runs on CPU)
  ollama pull qwen3.8:27b            # optional: programming
  ```
- Chrome (Edge is used only if Chrome is missing), ffmpeg
- Optional: [ComfyUI portable](https://github.com/Comfy-Org/ComfyUI/releases) for images
- API keys in `.env`: `BRAVE_API_KEY` (web search), `OPENWEATHER_API_KEY` (weather)

## 🧠 How it works

| Step | What runs |
|---|---|
| Wake word | "Jarvis" (and variations), voice activity detection with webrtcvad |
| Speech to text | faster-whisper `large-v3-turbo` on the GPU (int8_float16) |
| Thinking | `gemma4:26b` in Ollama with tool calling: the model decides whether to answer, search, open something, play music, remember... |
| Voice | Kokoro (`pm_santa`, local, CPU), Google TTS as fallback. Speech starts while the model is still writing |
| Interrupting | Say "pare", "para", "chega"... while Jarvis speaks. Questions such as "para que serve isso?" do not interrupt |

### Tools the model can use

Web search (Brave, with sources) and news · open the source page of the last answer · Google search in Chrome · open sites, programs and folders · play on YouTube (one media window that is reused) · Apple Music · weather · date and time · computer status · remember / recall / forget (semantic memory) · search your documents · learn about a topic from the web · emotional memory and daily journal · create images (FLUX) · describe images · translate SRT subtitles · avatar.

### Memory and documents

Memories are stored in SQLite (`brain/learning/memoria_jarvis.db`) with an embedding vector, so "what is the internet password?" finds what was saved as "wifi password". Put `.txt`, `.md` or `.pdf` files in `brain/data_jarvis/` (or set `JARVIS_DOCS_DIR`, several folders separated by `;`) and ask about them.

### Images

ComfyUI + FLUX.2 [klein] 4B (4 steps). Before generating, Jarvis unloads gemma4 from the GPU, generates, frees ComfyUI and reloads gemma4 in the background. Images are saved to `Pictures\Jarvis`.

1. Extract ComfyUI portable to `C:\ComfyUI` (or set `JARVIS_COMFYUI_DIR`).
2. `venv\Scripts\python.exe tests\prepare_flux.py` downloads the model, text encoder and VAE.
3. Ask: "Jarvis, crie uma imagem de um lobo na neve ao pôr do sol". Jarvis starts ComfyUI by itself.

## 🚀 Getting started

```powershell
git clone https://github.com/ProjectXTN/Jarvis_IA.git
cd Jarvis_IA
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python.exe tests\prepare_whisper.py   # downloads the Whisper model
venv\Scripts\python.exe tests\prepare_kokoro.py    # downloads the Kokoro voice
venv\Scripts\python.exe jarvis.py
```

After a cold boot gemma4 takes a minute or two to load; if you speak earlier, Jarvis says it is still loading and waits.

### Main `.env` settings

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server |
| `JARVIS_TOOL_ROUTER` | `1` | Model chooses the tools (0 = old keyword rules) |
| `JARVIS_EMBEDDING_MODEL` | `qwen3-embedding:0.6b` | Memory embeddings |
| `JARVIS_DOCS_DIR` | `brain/data_jarvis` | Document folders (`;` separated) |
| `JARVIS_IMAGE_ENGINE` | `flux` | `flux` (ComfyUI) or `sd` (old Stable Diffusion) |
| `JARVIS_COMFYUI_DIR` | `C:\ComfyUI` | ComfyUI folder |
| `JARVIS_CONSOLE_LEVEL` | `DEBUG` | `INFO` hides `[DEBUG]` lines in the window |
| `SECRET_TOKEN_JARVIS` | — | API token (16+ characters) |

## 🌐 HTTP API

```powershell
venv\Scripts\python.exe server.py
```

`POST http://127.0.0.1:11600/ask` with `Authorization: Bearer <SECRET_TOKEN_JARVIS>` and `{"question": "...", "lang": "pt"}`. Listens on 127.0.0.1 only (`JARVIS_API_HOST` to change), CORS only for `JARVIS_API_ORIGINS`, one request at a time, served with waitress.

## 📋 Logs

- `logs/jarvis.log`: everything printed, with time and level (rotates at 5 MB).
- `logs/tempos.csv`: how long each request, tool and image took.
- `logs/log_YYYY-MM-DD.txt`: the conversation.

## 🧪 Tests

```powershell
venv\Scripts\python.exe tests\run_all.py
```

## 🗂 Project structure

```
jarvis.py              voice loop (wake word → command)
jarvis_commands.py     shortcuts → tool router → old keyword rules
server.py              HTTP API
core/                  settings, startup, per-request state, logging
brain/tool_router.py   model + tools
brain/tools.py         the tools
brain/audio.py, tts.py, player.py, microphone.py, speech_*.py   listening and speaking
brain/semantic_memory.py   memory and documents
brain/image_gen.py     ComfyUI + FLUX
brain/websearch/       Brave search, news, page reading
commands/              old keyword commands (fallback)
tests/                 tests and setup scripts
```

## 🔒 Lock system

A `.lock` file prevents two Jarvis instances from running at the same time.

Made with 💥 by Pedro MEIRELES
