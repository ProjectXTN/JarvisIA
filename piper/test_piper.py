from piper.voice import PiperVoice
import wave

# Caminho para o modelo
model_path = "pt_BR-faber-medium.onnx"
voice = PiperVoice.load(model_path)

# Texto para sintetizar
text = "Jarvis está falando com sucesso via Python no WSL, Pedro!"

# Configura e cria o arquivo WAV
with wave.open("fala_jarvis.wav", "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(voice.config.sample_rate)

    # Sintetiza diretamente no arquivo
    voice.synthesize(text, wav_file)
