import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tkinter as tk
from tkinter import scrolledtext
import threading
from brain import audio
from jarvis_commands import process_command

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - Personal Assistant")
        self.root.geometry("600x500")

        self.chat = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Consolas", 11))
        self.chat.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(root, font=("Consolas", 12))
        self.entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.entry.bind("<Return>", self.on_enter)

        # Audio module callback to display bot messages
        audio.gui_callback = self.bot_say

        # Welcome message
        self.bot_say("Olá Pedro, Jarvis está online e pronto para te ajudar.")

        # Start continuous listening (VAD)
        self.start_continuous_listening()

    def bot_say(self, text):
        self.chat.configure(state='normal')
        self.chat.insert(tk.END, f"Jarvis: {text}\n")
        self.chat.configure(state='disabled')
        self.chat.see(tk.END)

    def user_say(self, text):
        self.chat.configure(state='normal')
        self.chat.insert(tk.END, f"Você: {text}\n")
        self.chat.configure(state='disabled')
        self.chat.see(tk.END)

    def on_enter(self, event):
        user_input = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not user_input:
            return
        self.user_say(user_input)
        threading.Thread(target=self.handle_input, args=(user_input,), daemon=True).start()

    def handle_input(self, text):
        result = process_command(text)
        time.sleep(0.8)
        if result is False:
            self.bot_say("Tchau! Jarvis desligando. Até a próxima.")
            self.root.after(1000, self.root.destroy)

    def start_continuous_listening(self):
        def listen_loop():
            while True:
                text = audio.listen()
                if text:
                    self.entry.delete(0, tk.END)
                    self.user_say(text)
                    self.handle_input(text)
        threading.Thread(target=listen_loop, daemon=True).start()

def start_gui():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
