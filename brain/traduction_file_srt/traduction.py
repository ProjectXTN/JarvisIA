import re
import subprocess
import time

def translate_srt_llm(input_path, output_path, target_lang="portuguese", model="llama3.2"):
    print(f"[DEBUG] START: {input_path=} {output_path=} {target_lang=}")

    start_time = time.time()
    
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\n\n', content.strip())
    translated_srt = []

    for i, block in enumerate(blocks):
        block_start = time.time()

        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        index = lines[0]
        timecode = lines[1]
        text = "\n".join(lines[2:])

        # Prompt stays in Portuguese for accurate translation!
        prompt = (
            f"Traduza o seguinte texto para {target_lang}. "
            "Responda somente com a tradução, sem explicações, comentários ou adaptações. Não adicione nada ao texto.\n\n"
            f"{text}\n"
        )

        try:
            result = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                capture_output=True,
                encoding="utf-8",
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                print(f"Error translating block {i}: {result.stderr.strip()}")
                translated_text = text
            else:
                translated_text = result.stdout.strip()
        except Exception as e:
            print(f"Critical error in block {i}: {e}")
            translated_text = text

        translated_block = f"{index}\n{timecode}\n{translated_text}"
        translated_srt.append(translated_block)
        
        block_end = time.time()
        print(f"[LOG] Block {i+1}/{len(blocks)} translated in {block_end - block_start:.2f} seconds")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(translated_srt))
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"[LOG] Translation finished in {duration:.2f} seconds!")

    print(f"✔️ Translation complete! Subtitles saved to: {output_path}")
