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


def _fake_speak_stream(pieces, *a, **k):
    text = "".join(pieces)
    spoken.append(text)
    return text


fake_audio.speak_stream = _fake_speak_stream
fake_audio.ask = lambda question: (spoken.append(question), "")[1]
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


class SpeechTextTest(unittest.TestCase):
    SPOKEN = (
        "O Ranger ataca à distância com armas físicas, somando dano "
        "consistente com mobilidade para reposicionar durante o combate."
    )

    def test_ordens_de_parar_interrompem(self):
        from brain.speech_text import is_interrupt

        for phrase in [
            "Pare!", "pare", "para", "Entendi, pode parar.", "parar de falar",
            "chega", "já entendi", "Jarvis, para.", "Pare. Que horas são?", "Pari.",
            "Para, que horas são?",
        ]:
            self.assertTrue(is_interrupt(phrase, self.SPOKEN), phrase)

    def test_perguntas_e_conversa_nao_interrompem(self):
        from brain.speech_text import is_interrupt

        for phrase in [
            "Para que serve este item?", "para que serve este item",
            "pra que serve isso", "O que significa pare em inglês?",
            "Por que ele para de atacar?", "Ele para quando?",
            "Como faço para parar o boss?", "qual a previsão do tempo",
            "vou viajar para Paris", "Obrigado.",
            # eco: a própria voz do Jarvis saindo da caixa de som
            "mobilidade para reposicionar durante o combate",
        ]:
            self.assertFalse(is_interrupt(phrase, self.SPOKEN), phrase)

    def test_comando_junto_com_a_ordem(self):
        from brain.speech_text import interrupt_remainder

        self.assertEqual(interrupt_remainder("Para, que horas são?"), "que horas são?")
        self.assertEqual(interrupt_remainder("Jarvis, pare. Qual a previsão do tempo"), "Qual a previsão do tempo")
        self.assertEqual(interrupt_remainder("Entendi, pode parar."), "")
        self.assertEqual(interrupt_remainder("chega"), "")

    def test_texto_falado_sem_marcacoes(self):
        from brain.speech_text import prepare_for_speech

        raw = (
            "[TÍTULO] Ranger · AION 2 [PARÁGRAFO] O Ranger ataca à distância. "
            "[PARÁGRAFO] O Ranger ataca à distância. [LISTA] - Accuracy → Critical Hit. "
            "- #1 Accuracy — Ajuda a superar Evasion. [FONTE] https://aion2br.com.br/x"
        )
        spoken = prepare_for_speech(raw)
        for unwanted in ["[", "]", "→", "—", "#", "http", "·"]:
            self.assertNotIn(unwanted, spoken)
        self.assertEqual(spoken.count("O Ranger ataca à distância"), 1)
        self.assertEqual(prepare_for_speech("Agora são 08:32."), "Agora são 08:32.")
        self.assertLessEqual(len(prepare_for_speech("Frase longa. " * 300, 500)), 500)


class CodeRequestTest(unittest.TestCase):
    def test_palavras_comuns_nao_viram_pedido_de_codigo(self):
        from brain.utils.utils import is_code_request

        for phrase in [
            "bom dia informações sobre a classe ranger de aion 2",
            "me dá um exemplo de build",
            "qual a função do ranger no grupo",
            "qual o melhor método para estudar",
        ]:
            self.assertFalse(is_code_request(phrase), phrase)

    def test_pedidos_de_codigo(self):
        from brain.utils.utils import is_code_request

        for phrase in [
            "escreva um código em python que lê um arquivo",
            "crie uma classe em python para usuário",
            "faça um script para renomear arquivos",
            "como fazer uma regex para email",
            "monte uma página html",
        ]:
            self.assertTrue(is_code_request(phrase), phrase)


class WebPathTest(unittest.TestCase):
    def test_novidades_vao_para_o_caminho_de_noticias(self):
        from brain.websearch.news import is_news_request

        self.assertTrue(is_news_request("e falo sobre as novidades e tecnologias sobre ia hoje"))
        self.assertTrue(is_news_request("quais as últimas sobre o AION 2"))
        self.assertFalse(is_news_request("informações sobre a classe ranger"))

    def test_busca_web_tem_limite_proprio(self):
        self.assertEqual(memory._read_timeout("web")[1], min(memory.OLLAMA_TIMEOUT[1], memory.WEB_LLM_TIMEOUT))
        self.assertEqual(memory._read_timeout(None), memory.OLLAMA_TIMEOUT)

    def test_rag_desligado_nao_e_consultado(self):
        from brain.pipeline import super_jarvis

        with mock.patch.object(super_jarvis, "RAG_ENABLED", False), \
             mock.patch.object(super_jarvis, "search_web", return_value=("texto", "fonte")), \
             mock.patch.object(super_jarvis, "query_rag", side_effect=AssertionError("RAG chamado")), \
             mock.patch.object(super_jarvis, "llama_query", return_value="ok") as llm:
            self.assertEqual(super_jarvis.super_jarvis_query("explique a classe ranger"), "ok")
        self.assertEqual(llm.call_args.kwargs["mode"], "web")


class SearchContextTest(unittest.TestCase):
    def test_procure_sempre_busca_na_web(self):
        for phrase in [
            "procure sobre a nova versão do chat gpt astra 6.2",
            "pesquise o preço da rtx 5090",
            "busca as atualizações da openai",
        ]:
            self.assertTrue(jarvis_commands.is_explicit_search(phrase), phrase)
        self.assertFalse(jarvis_commands.is_explicit_search("me explica como funciona um motor"))

    def test_procure_vai_para_a_busca_e_nao_para_a_memoria(self):
        with mock.patch.object(jarvis_commands, "super_jarvis_query", return_value="achei") as web, \
             mock.patch.object(jarvis_commands, "llama_query", side_effect=AssertionError("respondeu sem buscar")), \
             mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_query_time_sensitive", return_value=False):
            self.assertEqual(jarvis_commands.generate_response("procure sobre o chatgpt astra"), "achei")
        web.assert_called_once()

    def test_continuacao_usa_o_assunto_da_conversa(self):
        from brain.pipeline import super_jarvis

        history = [(
            "procure sobre a nova versão do chat gpt astra 6.2",
            "Não encontrei essa versão. Quer que eu procure as atualizações mais recentes da OpenAI?",
        )]
        rewritten = "atualizações mais recentes da OpenAI"
        with mock.patch.object(super_jarvis, "memory_context", history), \
             mock.patch.object(super_jarvis, "RAG_ENABLED", False), \
             mock.patch.object(super_jarvis, "search_web", return_value=("texto", "fonte")) as search, \
             mock.patch.object(super_jarvis, "remember_turn"), \
             mock.patch.object(super_jarvis, "llama_query", side_effect=[rewritten, "resposta"]):
            super_jarvis.super_jarvis_query("procure pelas atualizações mais recentes", conversation=True)
        search.assert_called_once_with(rewritten)

    def test_resposta_com_busca_sabe_a_data_de_hoje(self):
        from datetime import datetime
        from brain.pipeline import super_jarvis

        line = super_jarvis.today_line("pt", datetime(2026, 11, 18))
        self.assertIn("quarta-feira, 18/11/2026", line)
        with mock.patch.object(super_jarvis, "RAG_ENABLED", False), \
             mock.patch.object(super_jarvis, "search_web", return_value=("texto", "fonte")), \
             mock.patch.object(super_jarvis, "llama_query", return_value="ok") as llm:
            super_jarvis.super_jarvis_query("procure o lançamento do gpt")
        self.assertIn("Hoje é", llm.call_args.args[0])

    def test_sem_conversa_nao_reescreve(self):
        from brain.pipeline import super_jarvis

        with mock.patch.object(super_jarvis, "llama_query", side_effect=AssertionError("não devia chamar")):
            self.assertEqual(super_jarvis.contextualize_search("preço do bitcoin", []), "preço do bitcoin")


class StreamingVoiceTest(unittest.TestCase):
    def test_pergunta_comum_fala_em_fluxo_e_guarda_o_texto(self):
        def fake_stream(query, lang="pt"):
            yield "Olá, "
            yield "Pedro."

        spoken.clear()
        with mock.patch.object(jarvis_commands, "STREAMING_ENABLED", True), \
             mock.patch.object(jarvis_commands, "run_command_handlers", return_value=(False, None)), \
             mock.patch.object(jarvis_commands, "handle_weather_query", return_value=False), \
             mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_explicit_search", return_value=False), \
             mock.patch.object(jarvis_commands, "is_query_time_sensitive", return_value=False), \
             mock.patch.object(jarvis_commands, "needs_web", return_value=False), \
             mock.patch.object(jarvis_commands, "llama_stream", side_effect=fake_stream), \
             mock.patch.object(jarvis_commands, "log_interaction") as log, \
             mock.patch.object(jarvis_commands, "should_save_to_file", return_value=False):
            self.assertTrue(jarvis_commands.process_command("me explica algo"))
        self.assertEqual(spoken, ["Olá, Pedro."])
        log.assert_called_once_with("me explica algo", "Olá, Pedro.")

    def test_stream_vazio_avisa_que_nao_conseguiu(self):
        spoken.clear()
        with mock.patch.object(jarvis_commands, "STREAMING_ENABLED", True), \
             mock.patch.object(jarvis_commands, "run_command_handlers", return_value=(False, None)), \
             mock.patch.object(jarvis_commands, "handle_weather_query", return_value=False), \
             mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_explicit_search", return_value=False), \
             mock.patch.object(jarvis_commands, "is_query_time_sensitive", return_value=False), \
             mock.patch.object(jarvis_commands, "needs_web", return_value=False), \
             mock.patch.object(jarvis_commands, "llama_stream", return_value=iter([])):
            jarvis_commands.process_command("me explica algo")
        self.assertIn("Desculpe, não consegui responder agora.", spoken)

    def test_api_nunca_usa_stream(self):
        with mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_explicit_search", return_value=False), \
             mock.patch.object(jarvis_commands, "is_query_time_sensitive", return_value=False), \
             mock.patch.object(jarvis_commands, "needs_web", return_value=False), \
             mock.patch.object(jarvis_commands, "llama_stream", side_effect=AssertionError("stream na API")), \
             mock.patch.object(jarvis_commands, "llama_query", return_value="ok"):
            self.assertEqual(jarvis_commands.generate_response("oi", api=True, stream=True), "ok")


class WebSearchSpeedTest(unittest.TestCase):
    def test_paginas_lentas_ficam_de_fora_e_a_ordem_se_mantem(self):
        import asyncio
        import time as _time
        from brain.websearch import websearch

        delays = {"a": 0.05, "lenta": 3, "erro": 0.02, "b": 0.1}

        async def fake_fetch(session, url):
            await asyncio.sleep(delays[url])
            return url, None if url == "erro" else f"texto {url}"

        started = _time.monotonic()
        with mock.patch.object(websearch, "fetch_page", fake_fetch):
            result = asyncio.run(websearch.fetch_multiple_pages(["a", "lenta", "erro", "b"], budget=0.5))
        self.assertLess(_time.monotonic() - started, 1.5)
        self.assertEqual(result, [("a", "texto a"), ("erro", None), ("b", "texto b")])

    def test_busca_usa_resumos_da_brave_e_poucas_paginas(self):
        from brain.websearch import websearch

        brave = mock.Mock()
        brave.json.return_value = {"web": {"results": [
            {"title": f"<b>Ranger</b> {i}", "url": f"https://site{i}.com/x",
             "description": f"Resumo <strong>{i}</strong>", "extra_snippets": ["Detalhe"]}
            for i in range(8)
        ]}}

        async def fake_pages(links, budget=None):
            return [(link, "Texto da página " * 20) for link in links]

        with mock.patch.object(websearch, "BRAVE_API_KEY", "x"), \
             mock.patch.object(websearch.requests, "get", return_value=brave) as get, \
             mock.patch.object(websearch, "fetch_multiple_pages", side_effect=fake_pages) as pages:
            text, sources = websearch.search_web("build ranger aion 2")
        self.assertEqual(get.call_args.kwargs["params"]["q"], "build ranger aion 2")
        self.assertLessEqual(len(pages.call_args.args[0]), websearch.WEB_MAX_PAGES)
        self.assertIn("Resumos da busca", text)
        self.assertIn("Resumo 0", text)
        self.assertNotIn("<strong>", text)


class WebRouterTest(unittest.TestCase):
    def _route(self, model_answer):
        with mock.patch.object(jarvis_commands, "WEB_ROUTER_ENABLED", True), \
             mock.patch.object(jarvis_commands, "llama_query", return_value=model_answer) as llm:
            return jarvis_commands.needs_web("o que é esse apagão que estão falando"), llm

    def test_modelo_manda_buscar(self):
        decided, llm = self._route("BUSCAR")
        self.assertTrue(decided)
        self.assertEqual(llm.call_args.kwargs["mode"], "route")
        self.assertIn("Hoje é", llm.call_args.args[0])

    def test_modelo_manda_responder_ou_falha(self):
        self.assertFalse(self._route("RESPONDER")[0])
        self.assertFalse(self._route(None)[0])

    def test_pergunta_que_o_modelo_manda_buscar_vai_para_a_web(self):
        with mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_explicit_search", return_value=False), \
             mock.patch.object(jarvis_commands, "is_query_time_sensitive", return_value=False), \
             mock.patch.object(jarvis_commands, "needs_web", return_value=True), \
             mock.patch.object(jarvis_commands, "super_jarvis_query", return_value="achei") as web:
            self.assertEqual(jarvis_commands.generate_response("o que é esse apagão"), "achei")
        web.assert_called_once()

    def test_regras_fixas_dispensam_o_roteador(self):
        with mock.patch.object(jarvis_commands, "is_code_request", return_value=False), \
             mock.patch.object(jarvis_commands, "is_explicit_search", return_value=True), \
             mock.patch.object(jarvis_commands, "needs_web", side_effect=AssertionError("chamou o roteador")), \
             mock.patch.object(jarvis_commands, "super_jarvis_query", return_value="achei"):
            self.assertEqual(jarvis_commands.generate_response("procure isso"), "achei")


class LearnFromWebTest(unittest.TestCase):
    def test_pesquise_sobre_simples_nao_e_aprendizado(self):
        from commands import commands_memorie

        with mock.patch.object(commands_memorie, "execute_search", side_effect=AssertionError("aprendeu")):
            self.assertFalse(commands_memorie.learn_from_web("pesquise sobre a bolsa de valores"))

    def test_aprende_quando_pedido_sem_perguntar(self):
        from commands import commands_memorie

        spoken.clear()
        with mock.patch.object(commands_memorie, "execute_search", return_value=("resumo", "G1")) as search, \
             mock.patch.object(commands_memorie, "insert_memory", return_value=True) as insert, \
             mock.patch.object(commands_memorie, "listen", side_effect=AssertionError("ficou esperando resposta")):
            self.assertTrue(commands_memorie.learn_from_web("pesquise sobre a bolsa de valores e aprenda"))
        search.assert_called_once_with("O que é a bolsa de valores?")
        self.assertEqual(insert.call_args.args[:3], ("a bolsa de valores", "resumo", "G1"))
        self.assertEqual(spoken, ["Guardei isso sobre a bolsa de valores."])

        with mock.patch.object(commands_memorie, "execute_search", return_value=("resumo", "G1")) as search, \
             mock.patch.object(commands_memorie, "insert_memory", return_value=True):
            commands_memorie.learn_from_web("aprenda sobre redes neurais")
        search.assert_called_once_with("O que é redes neurais?")


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
        reply.json.return_value = {"message": {"content": "Olá"}}
        with mock.patch.object(memory.session, "post", return_value=reply) as post:
            self.assertEqual(memory.llama_query("oi", mode="site"), "Olá")
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["json"]["options"]["temperature"], 0.2)
        self.assertNotIn("temperature", kwargs["json"])
        self.assertIsNotNone(kwargs["timeout"])


class LlamaStreamTest(unittest.TestCase):
    def _reply(self, lines):
        import json as _json

        reply = mock.Mock()
        reply.iter_lines.return_value = [_json.dumps(line).encode() for line in lines]
        return reply

    def test_pedacos_chegam_em_ordem_e_turno_guardado_no_fim(self):
        lines = [
            {"message": {"content": "Olá, "}, "done": False},
            {"message": {"content": "Pedro."}, "done": False},
            {"message": {"content": ""}, "done": True},
        ]
        done = []
        with mock.patch.object(memory.session, "post", return_value=self._reply(lines)) as post, \
             mock.patch.object(memory, "remember_turn") as remember, \
             mock.patch.object(memory, "check_personal_answer", return_value=None):
            pieces = list(memory.llama_stream("oi", on_complete=done.append))
        self.assertEqual(pieces, ["Olá, ", "Pedro."])
        self.assertTrue(post.call_args.kwargs["stream"])
        self.assertTrue(post.call_args.kwargs["json"]["stream"])
        remember.assert_called_once_with("oi", "Olá, Pedro.")
        self.assertEqual(done, ["Olá, Pedro."])

    def test_erro_no_meio_para_sem_derrubar(self):
        lines = [{"message": {"content": "Começo. "}, "done": False}, {"error": "model crashed"}]
        with mock.patch.object(memory.session, "post", return_value=self._reply(lines)), \
             mock.patch.object(memory, "check_personal_answer", return_value=None), \
             mock.patch.object(memory, "remember_turn"):
            self.assertEqual(list(memory.llama_stream("oi")), ["Começo. "])

    def test_falha_de_conexao_nao_gera_nada(self):
        with mock.patch.object(memory.session, "post", side_effect=ConnectionError("fora do ar")), \
             mock.patch.object(memory, "check_personal_answer", return_value=None), \
             mock.patch.object(memory, "remember_turn") as remember:
            self.assertEqual(list(memory.llama_stream("oi")), [])
        remember.assert_not_called()


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
