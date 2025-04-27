import asyncio, subprocess, uuid, os
import edge_tts
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
import tempfile
import whisper
import torch
import sys
import webrtcvad
import collections
import threading
import time

# === Global variable for GUI integration ===
gui_callback = None

# === Lock to prevent concurrency on Whisper ===
transcribe_lock = threading.Lock()

# === Fix Whisper assets path if running as .exe ===
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    os.environ["WHISPER_ASSETS"] = os.path.join(base_path, "whisper", "assets")

# === Transcription model ===
model = whisper.load_model("medium").to("cuda" if torch.cuda.is_available() else "cpu")
current_audio_process = None

# === Main speech function with GUI support ===
async def speak_with_gui(text):
    global current_audio_process

    if gui_callback:
        gui_callback(f"🤖 Jarvis: {text}")
    else:
        print(f"\n🧠 Jarvis: {text}")

    filename = f"jarvis_{uuid.uuid4().hex}.mp3"

    try:
        start_time = time.time()  # ⏱️ Start timing

        communicate = edge_tts.Communicate(text, voice="pt-BR-AntonioNeural")
        await communicate.save(filename)

        end_time = time.time()  # ⏱️ End timing

        duration = end_time - start_time
        print(f"⏱️ Time to generate audio: {duration:.2f} seconds.")

        current_audio_process = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filename],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        current_audio_process.wait()

    except Exception as e:
        print(f"Error in audio synthesis or playback: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        current_audio_process = None

# === Public speech function ===
def say(text):
    global current_audio_process

    # 🔇 Interrupt previous audio if playing
    if current_audio_process and current_audio_process.poll() is None:
        print("🔇 Interrupting previous audio...")
        current_audio_process.terminate()
        current_audio_process = None

    asyncio.run(speak_with_gui(text))

# === Listening function with VAD + Whisper ===
def listen():
    global current_audio_process
    stream = None

    if current_audio_process and current_audio_process.poll() is None:
        print("🔇 Interrupting active response...")
        current_audio_process.terminate()
        current_audio_process = None

    fs = 16000
    vad = webrtcvad.Vad(2)
    duration_ms = 30
    frame_size = int(fs * duration_ms / 1000)
    block_duration = frame_size / fs if fs > 0 else 0.01

    print("\n🎙️ Listening with VAD...")

    audio = []
    ring_buffer = collections.deque(maxlen=10)
    triggered = False
    silence_duration = 1.5
    silence_blocks = int(silence_duration / block_duration)
    silence_counter = 0

    try:
        stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', blocksize=frame_size)
        stream.start()

        while True:
            block, _ = stream.read(frame_size)
            is_speech = vad.is_speech(block.tobytes(), fs)

            if not triggered:
                ring_buffer.append((block, is_speech))
                if sum(1 for _, speech in ring_buffer if speech) > 0.6 * ring_buffer.maxlen:
                    triggered = True
                    audio.extend(b for b, _ in ring_buffer)
                    ring_buffer.clear()
            else:
                audio.append(block)
                if not is_speech:
                    silence_counter += 1
                    if silence_counter > silence_blocks:
                        break
                else:
                    silence_counter = 0
    except Exception as e:
        print(f"Error during audio capture: {e}")
        return ""
    finally:
        if stream:
            stream.stop()

    audio_np = np.concatenate(audio, axis=0)
    average_volume = np.abs(audio_np).mean()
    print(f"🔊 Average detected volume: {average_volume:.2f}")

    if average_volume < 100:
        print("🧘 Low volume detected, ignoring...")
        return ""

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        scipy.io.wavfile.write(f.name, fs, audio_np)
        print("🔎 Transcribing with Whisper...")

        try:
            start_time = time.time()
            
            with transcribe_lock:
                result = model.transcribe(f.name, language="pt")
                
            end_time = time.time()
            duration = end_time - start_time
            print(f"⏱️ Time to transcribe audio: {duration:.2f} seconds.")
            
            text_out = result["text"].strip()
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""

        if text_out:
            print("🖙️ You said:", text_out)
            return text_out
        else:
            print("No text detected.")
            return ""
