import subprocess
import sys

def testar_sadtalker():
    audio_path = r"C:\Projetos\SadTalker\examples\driven_audio\jarvis.mp3"
    image_path = r"C:\Projetos\SadTalker\examples\source_image\jarvis_IA2.png"
    output_path = r"C:\Projetos\jarvis\imagens\video_output.mp4"
    checkpoint_dir = r"C:\Projetos\SadTalker\checkpoints"
    result_dir = r"C:\Projetos\jarvis\imagens"

    # Caminho do python da venv38
    python_venv38 = r"C:\Projetos\SadTalker\venv38\Scripts\python.exe"

    command = [
        python_venv38,
        r"C:\Projetos\SadTalker\inference.py",
        "--driven_audio", audio_path,
        "--source_image", image_path,
        "--result_dir", result_dir,
        "--checkpoint_dir", checkpoint_dir,
        "--verbose"
    ]

    print("[🧪] Rodando SadTalker via subprocess com venv38...")
    resultado = subprocess.run(command, capture_output=True, text=True)

    if resultado.returncode != 0:
        print("[❌] Falha ao gerar vídeo:")
        print(resultado.stderr)
    else:
        print("[✅] Vídeo gerado com sucesso!")
        print(f"Arquivo salvo em: {output_path}")

if __name__ == "__main__":
    testar_sadtalker()
