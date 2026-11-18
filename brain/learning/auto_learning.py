import time
import re
import string
import os
from datetime import datetime
from commands.commands_search import execute_search
from brain.learning.insert_memory import insert_memory
from brain.memory.memory import llama_query, DEFAULT_MODEL
from brain.learning.consult_memory import consultar_memoria

auto_learning_enabled = False

def clean_title(text):
    """Sanitize title for memory storage."""
    title = text.strip().lower()
    title = re.sub(r"\be\b$", "", title).strip()
    return title.strip(string.punctuation)

def generate_dynamic_topics():
    """Generate dynamic learning topics without predefined areas."""
    prompt = (
        "Liste 5 tópicos interessantes para aprender, sobre qualquer área (história, tecnologia, arte, ciências humanas, filosofia, negócios, etc). "
        "Cada tópico deve ter no máximo 3 palavras. Não inclua explicações, apenas a lista simples separada por vírgulas."
    )
    response = llama_query(prompt, direct_mode=True)

    if not isinstance(response, str):
        return []

    topics = [
        t.strip().lower()
        for t in response.split(",")
        if 2 < len(t.strip()) < 40 and re.search(r"\w", t)
    ]

    unique_topics = list(dict.fromkeys(topics))[:5]

    if not unique_topics:
        print(f"[DEBUG] Raw AI response: {response}")
        print("[FALLBACK] Using default topics...")
        unique_topics = [
            "história mundial",
            "filosofia moderna",
            "inteligência artificial",
            "desenvolvimento pessoal",
            "exploração espacial",
        ]

    return unique_topics

def log_learning(title, content, source, date):
    """Save learning logs for reference."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    today_date = datetime.now().strftime("%Y-%m-%d")
    file_name = os.path.join(log_dir, f"aprendizados_{today_date}.txt")

    try:
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(f"\n=== {title.upper()} ===\n")
            f.write(f" {date} |  Fonte: {source}\n")
            f.write(f"{content.strip()[:5000]}...\n")
            f.write("-" * 60 + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to save learning log: {e}")

def auto_learn():
    """Continuous loop for autonomous learning."""
    while True:
        if not auto_learning_enabled:
            print("🛑 [AUTO-LEARNING] Auto-learning mode disabled. Pausing...\n")
            break

        print(f"\n🧠 [AUTO-LEARNING] Starting new cycle at {datetime.now().strftime('%H:%M:%S')}...")
        topics = generate_dynamic_topics()

        if not topics:
            print("⚠️ No valid topics generated. Trying again shortly...\n")
            time.sleep(10)
            continue

        print(f"[AUTO-LEARNING] Generated topics: {topics}")
        learned_today = []

        for topic in topics:
            if not auto_learning_enabled:
                print("🛑 [AUTO-LEARNING] Auto-learning mode disabled during cycle. Pausing...\n")
                return

            question = f"O que é {topic}?"
            response, source = execute_search(question, speak=False)

            if isinstance(response, str) and "Erro" not in response:
                title = clean_title(topic)
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if consultar_memoria(title):
                    print(f"⚠️ Already learned about: {title}. Skipping...\n")
                    continue

                success = insert_memory(title, response, source, date)
                if success:
                    log_learning(title, response, source, date)
                    learned_today.append(title)
                    print(f"✅ Learned: {title} (Source: {source})\n")
                else:
                    print(f"⚠️ Failed to save: {title}")
            else:
                print(f"❌ Could not search about: {topic}")

        if learned_today:
            print("\n📚 [AUTO-LEARNING] Topics learned in this cycle:")
            for t in learned_today:
                print(f"   • {t}")
        else:
            print("🛑 No learning completed in this cycle.")

        print("\n🔁 Starting next cycle...\n")
        time.sleep(2)
