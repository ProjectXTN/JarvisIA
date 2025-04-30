import os
import re
import unicodedata
import subprocess
from jsbeautifier import beautify

CODE_FOLDER = "codes"
os.makedirs(CODE_FOLDER, exist_ok=True)

def detect_language(code):
    if re.search(r"def\s+\w+\s*\(.*\):", code):
        return "py"
    elif re.search(r"function\s+\w+\s*\(.*\)", code):
        return "js"
    elif re.search(r"#include\s+<.*>", code):
        return "c"
    elif re.search(r"public\s+class\s+\w+", code):
        return "java"
    elif re.search(r"<html>|<!DOCTYPE html>", code, re.IGNORECASE):
        return "html"
    elif re.search(r"^SELECT\s+.*\s+FROM", code, re.IGNORECASE):
        return "sql"
    elif re.search(r"\.style|{[^}]*}", code):
        return "css"
    return "txt"

def clean_filename(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text.lower().strip("_")

def format_code(code, language):
    if language == "py":
        try:
            temp = "temp.py"
            with open(temp, "w", encoding="utf-8") as f:
                f.write(code)
            subprocess.run(["black", temp, "--quiet"], check=True)
            with open(temp, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[BLACK] Error: {e}")
            return code

    elif language in ["js", "html", "css"]:
        try:
            temp = f"temp.{language}"
            with open(temp, "w", encoding="utf-8") as f:
                f.write(code)
            subprocess.run(["prettier", "--write", temp], check=True)
            with open(temp, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[PRETTIER] Failed, trying beautify: {e}")
            try:
                return beautify(code)
            except Exception as e:
                print(f"[BEAUTIFY] Also failed: {e}")
                return code

    return code

def extract_and_save_code(full_response, title="codigo"):
    blocks = re.findall(r"```(?:\w+\n)?(.*?)```", full_response, re.DOTALL)
    if not blocks:
        print("[DEV] No code block found.")
        return None

    code = "\n\n".join(block.strip() for block in blocks)
    language = detect_language(code)

    # Test compilation before formatting, if Python
    if language == "py":
        try:
            compile(code, "<string>", "exec")
        except Exception as e:
            print(f"[SYNTAX] Python syntax error: {e}")

    try:
        code = format_code(code, language)
    except Exception as e:
        print
