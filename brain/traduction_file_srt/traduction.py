import re
import subprocess
import time
import os

def translate_subtitle_llm(input_path, output_path, target_lang="portuguese", model="llama3.2"):
    print(f"[DEBUG] START: {input_path=} {output_path=} {target_lang=}")
    start_time = time.time()
    
    ext = os.path.splitext(input_path)[1].lower()
    is_ass = ext == ".ass"
    translated_lines = []

    if is_ass:
        # ASS: line by line, only Dialogue:
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.rstrip('\n')
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) < 10:
                    translated_lines.append(line)
                    continue
                dialogue_text = parts[9]
                prompt = (
                        f"Traduza o seguinte texto para {target_lang}, mas mantenha exatamente todas as tags ou comandos entre chaves '{{' e '}}' no mesmo lugar e formato. "
                        "Responda somente com a tradução do texto, sem explicações, comentários ou adaptações, e sem modificar nada dentro das chaves. "
                        "Não adicione nada ao texto. \n\n"
                        f"{dialogue_text}\n"
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
                        print(f"Error translating line {i}: {result.stderr.strip()}")
                        translated_text = dialogue_text
                    else:
                        translated_text = result.stdout.strip()
                except Exception as e:
                    print(f"Critical error in line {i}: {e}")
                    translated_text = dialogue_text

                translated_line = ",".join(parts[:9]) + "," + translated_text
                translated_lines.append(translated_line)
                print(f"[LOG] Line {i+1}/{len(lines)} translated (Dialogue)")
                time.sleep(0.2)
            else:
                translated_lines.append(line)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(translated_lines))
    else:
        # SRT: Block by block
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
            time.sleep(0.2)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(translated_srt))

    end_time = time.time()
    duration = end_time - start_time
    print(f"[LOG] Translation finished in {duration:.2f} seconds!")
    print(f"✔️ Translation complete! Subtitles saved to: {output_path}")

