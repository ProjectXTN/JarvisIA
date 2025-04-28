import requests
import base64
import os
from pathlib import Path
import time
from brain.storage.open_file import safe_open_file


class StableDiffusionGenerator:
    def __init__(self, url="http://127.0.0.1:7860"):
        self.url = url

    def generate_image(
        self,
        prompt,
        output_folder=None,
        steps=50,
        cfg_scale=10,
        width=1024,
        height=1024,
        sampler_name="DPM++ 2M Karras",
        refiner=True,
    ):
        if output_folder is None:
            pictures_folder = Path.home() / "Pictures" / "Jarvis" / "Imagens"
            output_folder = pictures_folder


        Path(output_folder).mkdir(parents=True, exist_ok=True)

        payload = {
            "prompt": prompt,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "sampler_name": sampler_name,
        }

        try:
            response = requests.post(
                f"{self.url}/sdapi/v1/txt2img", json=payload, timeout=300
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[ERRO] Erro na requisição ao Stable Diffusion: {e}")
            return
        except Exception as e:
            print(f"[ERRO] Erro inesperado durante envio ao Stable Diffusion: {e}")
            return

        try:
            r = response.json()
        except Exception as e:
            print(f"[ERRO] Falha ao decodificar o JSON de resposta: {e}")
            return

        try:
            if "images" not in r or not r["images"]:
                raise Exception("Nenhuma imagem retornada pela API de geração.")

            image_data = r["images"][0]

            if not image_data:
                raise Exception("Imagem retornada está vazia.")

            temp_image_path = Path(output_folder) / f"temp_{int(time.time())}.png"

            with open(temp_image_path, "wb") as f:
                f.write(base64.b64decode(image_data.split(",", 1)[-1]))

            final_path = temp_image_path

            if refiner:

                with open(temp_image_path, "rb") as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode()

                img2img_payload = {
                    "init_images": [f"data:image/png;base64,{img_base64}"],
                    "denoising_strength": 0.2,
                    "prompt": prompt,
                    "steps": 20,
                    "cfg_scale": cfg_scale,
                    "width": width,
                    "height": height,
                    "sampler_name": sampler_name,
                }

                try:
                    response = requests.post(
                        f"{self.url}/sdapi/v1/img2img", json=img2img_payload, timeout=60
                    )
                    response.raise_for_status()
                except Exception as e:
                    print(f"[ERRO] Falha ao comunicar com img2img: {e}")
                    raise Exception("Erro na comunicação com o Refiner.")

                r = response.json()

                if "images" not in r or not r["images"]:
                    raise Exception("Nenhuma imagem retornada pela API de refinamento.")

                refined_image_data = r["images"][0]

                final_path = (
                    Path(output_folder)
                    / f"{prompt[:50].replace(' ', '_').replace(',', '').replace('!', '').replace('?', '')}_refined.png"
                )

                with open(final_path, "wb") as f:
                    f.write(base64.b64decode(refined_image_data.split(",", 1)[-1]))

                os.remove(temp_image_path)

            if final_path.exists():
                safe_open_file(final_path)
            else:
                print(f"[ERRO] Arquivo {final_path} não encontrado. Não é possível abrir.")


            return str(final_path)

        except Exception as e:
            print(f"[ERRO] Falha ao processar ou salvar imagem: {e}")
            raise Exception("Erro ao processar a imagem.")
