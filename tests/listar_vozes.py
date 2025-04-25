import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

for idx, voice in enumerate(voices):
    print("[{}] {} - {} - {}".format(idx, voice.name, voice.languages, voice.id))
