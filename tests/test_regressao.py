"""Testes de regressão dos bugs corrigidos na Fase 1 do PLANO.md.

Rodam sem GPU, microfone ou Ollama: o áudio é substituído por um dublê e
bibliotecas ausentes viram objetos falsos.

    python -m unittest tests.test_regressao -v
"""

import importlib.abc
import importlib.machinery
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Bibliotecas externas que o projeto usa. Se alguma não estiver instalada
# (por exemplo numa máquina sem GPU), ela é trocada por um objeto falso.
OPTIONAL_LIBRARIES = {
    "aiohttp", "bs4", "dotenv", "edge_tts", "faster_whisper", "flask",
    "flask_cors", "jsbeautifier", "keyboard", "llama_index", "numpy",
    "psutil", "pyautogui", "pyperclip", "requests", "scipy", "sounddevice",
    "tkinter", "torch", "unidecode", "webrtcvad", "whisper",
}


class _FakeMissingModules(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Último recurso na busca de módulos: só age se o import real falhou.

    Uma biblioteca instalada de verdade nunca é misturada com partes falsas:
    só falsificamos submódulos de bibliotecas que já são inteiras falsas.
    """

    faked = set()

    def find_spec(self, name, path=None, target=None):
        top = name.split(".")[0]
        if top not in OPTIONAL_LIBRARIES:
            return None
        if name == top:
            self.faked.add(top)
        elif top not in self.faked:
            return None
        return importlib.machinery.ModuleSpec(name, self, is_package=True)

    def create_module(self, spec):
        module = mock.MagicMock(name=spec.name)
        module.__path__ = []
        module.__spec__ = spec
        return module

    def exec_module(self, module):
        pass


sys.meta_path.append(_FakeMissingModules())

# O áudio real carrega o Whisper e abre o microfone; aqui só registramos as falas.
spoken = []
fake_audio = types.ModuleType("brain.audio")
fake_audio.say = lambda text, *a, **k: spoken.append(text)
fake_audio.listen = lambda: ""
sys.modules["brain.audio"] = fake_audio

from brain.memory import memory  # noqa: E402
from brain.utils.utils import sounds_like_jarvis  # noqa: E402
from commands.commands_day_time import datetime_commands  # noqa: E402
from commands.commands_music import music_commands  # noqa: E402
from commands.commands_systeme import is_shutdown_request  # noqa: E402
from core import initializer  # noqa: E402
import jarvis_commands  # noqa: E402
import re  # noqa: E402


def _matches(patterns, phrase):
    return any(re.search(pattern, phrase) for pattern, _ in patterns)


class ShutdownTest(unittest.TestCase):
    def test_pedidos_explicitos_desligam(self):
        for phrase in [
            "desligar",
            "Jarvis, desligar.",
            "jarvis pode desligar",
            "sair",
            "encerrar o sistema",
            "por favor desligue o jarvis",
            "Tchau, Jarvis!",
            "até logo",
        ]:
            self.assertTrue(is_shutdown_request(phrase), phrase)

    def test_palavras_soltas_nao_desligam(self):
        for phrase in [
            "o que o presidente falou hoje",
            "quando vai sair o novo iphone",
            "como desligar o computador pelo teclado",
            "o que significa off em inglês",
            "quero sair para jantar, alguma sugestão",
            "me diga tchau em japonês",
        ]:
            self.assertFalse(is_shutdown_request(phrase), phrase)


class HotwordTest(unittest.TestCase):
    def test_variacoes_de_jarvis_ativam(self):
        for phrase in ["jarvis que horas são", "jarves abre o steam", "ei javis", "jarbis"]:
            self.assertTrue(sounds_like_jarvis(phrase)[0], phrase)

    def test_outras_palavras_nao_ativam(self):
        for phrase in ["vou regar o jardim", "que horas são", "janeiro é quente", "java é bom"]:
            self.assertFalse(sounds_like_jarvis(phrase)[0], phrase)

    def test_modo_passivo_ignora_fala_sem_hotword(self):
        heard = iter(["vou regar o jardim", "tudo bem por aqui", "jarvis, bom dia"])
        with mock.patch.object(initializer, "listen", lambda: next(heard)):
            self.assertEqual(initializer.passive_mode(), "jarvis, bom dia")


class CommandPatternTest(unittest.TestCase):
    def test_horas(self):
        self.assertTrue(_matches(datetime_commands, "que horas são"))
        self.assertTrue(_matches(datetime_commands, "me diga as horas"))
        self.assertTrue(_matches(datetime_commands, "bom dia que horas é agora"))
        self.assertTrue(_matches(datetime_commands, "que hora é"))
        self.assertFalse(_matches(datetime_commands, "que horas é agora em lisboa"))
        self.assertFalse(_matches(datetime_commands, "quantas horas tem um dia"))
        self.assertFalse(_matches(datetime_commands, "que horas são em tóquio"))
        self.assertFalse(_matches(datetime_commands, "a que horas começa o jogo"))

    def test_data(self):
        self.assertTrue(_matches(datetime_commands, "que dia é hoje"))
        self.assertTrue(_matches(datetime_commands, "qual é a data de hoje"))

    def test_coloque(self):
        self.assertTrue(_matches(music_commands, "coloque uma música do queen"))
        self.assertTrue(_matches(music_commands, "toque queen"))
        self.assertFalse(_matches(music_commands, "coloque um alarme para as sete"))


class WeatherTest(unittest.TestCase):
    def test_grafias_erradas_da_cidade_de_casa(self):
        from brain.weatherAPI import weatherAPI

        for heard in ["Alexi", "Lexi", "Lexy", "Léxi"]:
            self.assertEqual(
                weatherAPI.resolve_location(heard), weatherAPI.HOME_LOCATION, heard
            )

    def test_outra_cidade_usa_geocodificacao(self):
        from brain.weatherAPI import weatherAPI

        reply = mock.Mock()
        reply.json.return_value = [{"name": "Lisbon", "country": "PT"}]
        with mock.patch.object(weatherAPI.requests, "get", return_value=reply):
            self.assertEqual(weatherAPI.resolve_location("Lisboa"), "Lisbon,PT")
        reply.json.return_value = []
        with mock.patch.object(weatherAPI.requests, "get", return_value=reply):
            self.assertIsNone(weatherAPI.resolve_location("Xyzabc"))

    def test_nao_pergunta_mais_o_pais(self):
        from brain.weatherAPI import weatherAPI

        spoken.clear()
        with mock.patch.object(weatherAPI, "get_weather", return_value="Sol.") as gw, \
             mock.patch.object(weatherAPI, "listen", side_effect=AssertionError("não deve ouvir")):
            weatherAPI.handle_weather_query("qual a previsão do tempo para alexi")
        self.assertEqual(gw.call_args.args[0], weatherAPI.HOME_LOCATION)
        self.assertEqual(spoken, ["Sol."])


class AvatarCommandTest(unittest.TestCase):
    def _handler(self, phrase):
        from commands.commands_avatar import avatar_view_commands

        for pattern, func in avatar_view_commands:
            if re.search(pattern, phrase):
                return func.__name__
        return None

    def test_mostrar(self):
        for phrase in ["mostre o avatar", "mostrar seu avatar", "abra o avatar", "quero ver seu rosto", "ative o holograma", "avatar"]:
            self.assertEqual(self._handler(phrase), "show_avatar", phrase)

    def test_esconder(self):
        for phrase in ["esconda o avatar", "feche o avatar", "pode tirar o avatar da tela"]:
            self.assertEqual(self._handler(phrase), "hide_avatar", phrase)

    def test_outras_frases_nao_abrem(self):
        for phrase in ["que horas são", "mostre a previsão do tempo", "o que é um avatar"]:
            self.assertIsNone(self._handler(phrase), phrase)

    def test_funcoes_do_avatar_nao_fazem_nada_com_a_janela_fechada(self):
        from brain import avatar

        self.assertFalse(avatar.is_open())
        avatar.set_state("listening")
        avatar.speak_start("arquivo_que_nao_existe.mp3", "oi")
        avatar.speak_stop()


class HandlerFlowTest(unittest.TestCase):
    def test_comando_que_devolve_false_nao_encerra(self):
        # "atualize o sistema" casa com a chave "atualize", mas o comando de
        # memória não reconhece a frase e devolve False. Isso não é desligar.
        handlers = [{"atualize": lambda q: False}, [(r"sistema", lambda q: "feito")]]
        with mock.patch.object(jarvis_commands, "COMMAND_HANDLERS", handlers):
            self.assertEqual(
                jarvis_commands.run_command_handlers("atualize o sistema"),
                (True, "feito"),
            )

    def test_nenhum_comando_vai_para_o_llm(self):
        with mock.patch.object(jarvis_commands, "COMMAND_HANDLERS", [{"x1": lambda q: True}]):
            self.assertEqual(jarvis_commands.run_command_handlers("oi"), (False, None))

    def test_erro_no_llm_nao_derruba_nem_vira_resposta(self):
        with mock.patch.object(jarvis_commands, "llama_query", side_effect=RuntimeError("x")), \
             mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_query_time_sensitive", return_value=False):
            self.assertIsNone(jarvis_commands.generate_response("qualquer coisa"))


class LlamaQueryTest(unittest.TestCase):
    def test_falha_do_ollama_devolve_none(self):
        with mock.patch.object(memory.session, "post", side_effect=ConnectionError("fora do ar")):
            self.assertIsNone(memory.llama_query("oi", mode="site"))

    def test_temperatura_vai_em_options_e_tem_timeout(self):
        reply = mock.Mock()
        reply.json.return_value = {"response": "Olá"}
        with mock.patch.object(memory.session, "post", return_value=reply) as post:
            self.assertEqual(memory.llama_query("oi", mode="site"), "Olá")
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["json"]["options"], {"temperature": 0.2})
        self.assertNotIn("temperature", kwargs["json"])
        self.assertIsNotNone(kwargs["timeout"])


class LockTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.lock = os.path.join(self.dir.name, "jarvis.lock")
        patcher = mock.patch.object(initializer, "LOCK_FILE", self.lock)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.dir.cleanup)

    def _write(self, pid):
        with open(self.lock, "w") as f:
            f.write(str(pid))

    def test_lock_de_processo_morto_e_ignorado(self):
        self._write(40160)
        with mock.patch.object(initializer, "_is_jarvis_process", return_value=False):
            self.assertFalse(initializer.is_already_running())
        with open(self.lock) as f:
            self.assertEqual(f.read(), str(os.getpid()))

    def test_lock_de_processo_vivo_bloqueia(self):
        self._write(40160)
        with mock.patch.object(initializer, "_is_jarvis_process", return_value=True):
            self.assertTrue(initializer.is_already_running())

    def test_segunda_instancia_nao_apaga_lock_da_primeira(self):
        self._write(40160)
        initializer.remove_lock()
        self.assertTrue(os.path.exists(self.lock))

    def test_instancia_apaga_o_proprio_lock(self):
        self._write(os.getpid())
        initializer.remove_lock()
        self.assertFalse(os.path.exists(self.lock))


if __name__ == "__main__":
    unittest.main()
