import requests
import os

# URL direta do modelo JARVIS da OpenWakeWord no HuggingFace
url = "https://huggingface.co/datasets/spokestack/wakeword/resolve/main/jarvis.onnx"

# Pasta padrão onde o openwakeword espera encontrar os modelos
output_dir = os.path.expanduser("~/.cache/openwakeword/models")

# Garante que o diretório existe
os.makedirs(output_dir, exist_ok=True)

# Caminho completo para salvar o modelo
output_path = os.path.join(output_dir, "jarvis.onnx")

# Baixa o modelo
print("⬇️ Baixando modelo 'jarvis'...")
response = requests.get(url)
with open(output_path, "wb") as f:
    f.write(response.content)

print(f"✅ Modelo salvo em: {output_path}")
