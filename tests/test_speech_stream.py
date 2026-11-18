"""Fala em fluxo (brain/speech_stream.py), sem áudio de verdade."""
import threading
import time
import unittest

from brain.speech_stream import iter_sentences, run_pipeline


class SentenceSplitTest(unittest.TestCase):
    def test_primeira_frase_sai_logo_e_as_seguintes_se_agrupam(self):
        chunks = ["A Open", "AI lançou o GPT-6.2 Astra. ", "Ele custa menos ",
                  "de um terço do anterior e saiu em 17/11. Além disso", ", cria documentos. Fim"]
        self.assertEqual(list(iter_sentences(chunks)), [
            "A OpenAI lançou o GPT-6.2 Astra.",
            # segundo trecho curto: sai na primeira frase com 40+ caracteres
            "Ele custa menos de um terço do anterior e saiu em 17/11.",
            # depois, agrupa até 90 caracteres; "Fim" entra junto
            "Além disso, cria documentos. Fim",
        ])

    def test_numeros_com_ponto_nao_cortam(self):
        self.assertEqual(list(iter_sentences(["Custa R$ 4.26 e a versão é 6.2 hoje."])),
                         ["Custa R$ 4.26 e a versão é 6.2 hoje."])


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.files = set()
        self.lock = threading.Lock()

    def synth(self, text):
        time.sleep(0.02)
        with self.lock:
            path = f"audio{len(self.files)}-{text[:5]}"
            self.files.add(path)
        return path

    def discard(self, path):
        with self.lock:
            self.files.discard(path)

    def test_primeira_frase_toca_antes_do_modelo_terminar(self):
        events = []

        def slow_model():
            yield "Primeira frase. "
            time.sleep(0.4)
            events.append("modelo terminou")
            yield "Segunda parte bem mais longa, que chega depois de um tempo considerável para o teste."

        def play(path, text):
            events.append("tocou: " + text[:8])
            return False

        spoken, interrupted = run_pipeline(slow_model(), self.synth, play, lambda t, b: t, self.discard)
        self.assertFalse(interrupted)
        self.assertEqual(events[0], "tocou: Primeira")
        self.assertIn("modelo terminou", events)
        self.assertEqual(self.files, set())

    def test_interromper_para_tudo_e_apaga_os_audios(self):
        played = []
        sentences = ["Um. "] + [f"Frase número {i} longa o bastante para formar um grupo próprio de fala aqui. " for i in range(6)]

        def play(path, text):
            played.append(text)
            return len(played) == 2

        spoken, interrupted = run_pipeline(iter(sentences), self.synth, play, lambda t, b: t, self.discard)
        self.assertTrue(interrupted)
        self.assertEqual(len(played), 2)
        self.assertEqual(self.files, set())

    def test_frase_repetida_e_limite_de_caracteres(self):
        played = []
        text = ["Oi. ", "Oi. ", "x" * 50 + ". ", "y" * 50 + ". ", "z" * 300 + "."]

        def prepare(t, budget):
            return t[:budget]

        spoken, _ = run_pipeline(iter(text), self.synth, lambda p, t: played.append(t), prepare,
                                 self.discard, max_chars=120)
        self.assertEqual(played.count("Oi."), 1)
        self.assertLessEqual(sum(len(t) for t in played), 120)

    def test_erro_no_modelo_fala_o_que_ja_veio(self):
        def broken():
            yield "Começo da resposta. "
            raise RuntimeError("conexão caiu")

        spoken, _ = run_pipeline(broken(), self.synth, lambda p, t: False, lambda t, b: t, self.discard)
        self.assertEqual(spoken, "Começo da resposta.")
