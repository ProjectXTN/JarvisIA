import edge_tts
import asyncio

async def speak(text):
    communicate = edge_tts.Communicate(text, voice="pt-BR-AntonioNeural")
    await communicate.save("jarvis.mp3")

asyncio.run(speak("Olá Pedro, Jarvis está pronto para te ajudar. Vamos entrar no codigo da Matrix!"))
