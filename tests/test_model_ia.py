import subprocess

prompt = "me conte a historia de Adolf Hitler, em português."
resultado = subprocess.run(
    ["ollama", "run", "llama3.3"],
    input=prompt,
    capture_output=True,
    encoding="utf-8"
)

print(resultado.stdout)
