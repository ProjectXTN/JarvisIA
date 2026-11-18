"""Fase 6: gerador de imagens com ComfyUI + FLUX.2 klein (sem ComfyUI de verdade)."""
import os
import tempfile
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401 (bibliotecas falsas quando faltam)
from brain import image_gen


class Resp:
    def __init__(self, data=None, ok=True, content=b""):
        self._data, self.ok, self.content, self.text = data, ok, content, str(data)

    def json(self):
        return self._data

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError("http")


class WorkflowTest(unittest.TestCase):
    def test_grafo_destilado_ligado(self):
        g = image_gen.build_workflow("a red fox", 832, 1216, seed=7)
        types = {n["class_type"] for n in g.values()}
        for needed in ("UNETLoader", "CLIPLoader", "VAELoader", "CLIPTextEncode", "Flux2Scheduler",
                       "EmptyFlux2LatentImage", "SamplerCustomAdvanced", "VAEDecode", "SaveImage"):
            self.assertIn(needed, types)
        self.assertEqual(g["2"]["inputs"]["type"], "flux2")
        self.assertEqual(g["4"]["inputs"]["text"], "a red fox")
        self.assertEqual((g["8"]["inputs"]["steps"], g["6"]["inputs"]["cfg"]), (4, 1.0))
        self.assertEqual((g["10"]["inputs"]["width"], g["10"]["inputs"]["height"]), (832, 1216))
        for node in g.values():  # toda ligação aponta para um nó que existe
            for value in node["inputs"].values():
                if isinstance(value, list):
                    self.assertIn(value[0], g)


class GenerateTest(unittest.TestCase):
    def test_gera_salva_e_devolve_a_vram(self):
        out = tempfile.mkdtemp()
        calls = []

        def get(url, **kw):
            calls.append(("GET", url))
            if url.endswith("/object_info/UNETLoader"):
                return Resp({"UNETLoader": {"input": {"required": {"unet_name": [["flux-2-klein-4b-fp8.safetensors"]]}}}})
            if "/history/" in url:
                return Resp({"abc": {"status": {"status_str": "success"},
                                     "outputs": {"13": {"images": [{"filename": "J_1.png", "subfolder": "", "type": "output"}]}}}})
            if url.endswith("/view"):
                return Resp(content=b"PNG")
            return Resp({})

        def post(url, json=None, **kw):
            calls.append(("POST", url, json))
            if url.endswith("/prompt"):
                self.assertEqual(json["prompt"]["1"]["inputs"]["unet_name"], "flux-2-klein-4b-fp8.safetensors")
                return Resp({"prompt_id": "abc"})
            return Resp({})

        with mock.patch.object(image_gen, "start_comfy"), \
             mock.patch.object(image_gen.requests, "get", side_effect=get), \
             mock.patch.object(image_gen.requests, "post", side_effect=post), \
             mock.patch.object(image_gen, "IMAGE_OUTPUT_DIR", out), \
             mock.patch.object(image_gen.threading, "Thread") as thread:
            path = image_gen.generate("a fox", open_after=False)
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"PNG")
        posts = [c[1] for c in calls if c[0] == "POST"]
        self.assertTrue(posts[0].endswith("/api/generate"))  # descarrega o gemma antes
        self.assertTrue(posts[1].endswith("/prompt"))
        thread.assert_called_once()  # libera o ComfyUI e recarrega o gemma depois

    def test_erro_do_comfy_ainda_devolve_a_vram(self):
        with mock.patch.object(image_gen, "start_comfy"), \
             mock.patch.object(image_gen, "available_unet", return_value="x"), \
             mock.patch.object(image_gen, "unload_llm"), \
             mock.patch.object(image_gen.requests, "post", return_value=Resp({"error": 1}, ok=False)), \
             mock.patch.object(image_gen, "free_comfy_and_reload_llm") as free:
            with self.assertRaises(image_gen.ImageError):
                image_gen.generate("a fox", open_after=False)
        free.assert_called_once()

    def test_sem_comfy_e_sem_pasta(self):
        with mock.patch.object(image_gen, "comfy_running", return_value=False), \
             mock.patch.object(image_gen, "COMFYUI_DIR", os.path.join(tempfile.gettempdir(), "nao_existe")):
            with self.assertRaises(image_gen.ImageError):
                image_gen.start_comfy()


if __name__ == "__main__":
    unittest.main()
