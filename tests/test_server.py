"""Fase 6: segurança da API (sem precisar do Flask)."""
import threading
import unittest

import tests.test_regressao  # noqa: F401 (bibliotecas falsas quando faltam)
import server
from core import config


class TokenTest(unittest.TestCase):
    def test_token(self):
        token = "a" * 32
        self.assertTrue(server.token_ok(f"Bearer {token}", token))
        self.assertFalse(server.token_ok("Bearer errado", token))
        self.assertFalse(server.token_ok(token, token))
        self.assertFalse(server.token_ok(None, token))

    def test_sem_token_configurado_nunca_aceita(self):
        # antes: sem token no .env, "Bearer None" passava
        self.assertFalse(server.token_ok("Bearer None", None))
        self.assertFalse(server.token_ok("Bearer ", ""))


class QuestionTest(unittest.TestCase):
    def test_valida(self):
        self.assertEqual(server.parse_question({"question": " Oi "}), ("Oi", "pt"))
        self.assertEqual(server.parse_question({"question": "Hi", "lang": "en"}), ("Hi", "en"))
        self.assertEqual(server.parse_question({"question": "Oi", "lang": "pt-BR"}), ("Oi", "pt"))
        self.assertEqual(server.parse_question({"question": "Salut", "lang": "fr"}), ("Salut", "fr"))
        self.assertEqual(server.parse_question({"question": "Oi", "lang": "xx"}), ("Oi", "pt"))
        self.assertEqual(len(server.parse_question({"question": "x" * 5000})[0]), 5000)  # prompt do site
        for bad in (None, [], {}, {"question": 3}, {"question": "  "},
                    {"question": "x" * 8001}):
            with self.assertRaises(server.BadRequest):
                server.parse_question(bad)

    def test_origens(self):
        self.assertEqual(server.allowed_origins(None), [])
        self.assertEqual(server.allowed_origins("http://a, http://b"), ["http://a", "http://b"])


class ApiStateTest(unittest.TestCase):
    def test_modo_api_vale_so_na_thread_do_pedido(self):
        seen = {}
        inside = threading.Event()
        release = threading.Event()

        def api():
            with config.api_request():
                seen["api"] = config.IS_API_REQUEST
                inside.set()
                release.wait(2)

        t = threading.Thread(target=api)
        t.start()
        inside.wait(2)
        seen["voz"] = config.IS_API_REQUEST  # voz continua falando
        release.set()
        t.join()
        self.assertEqual(seen, {"api": True, "voz": False})
        self.assertFalse(config.IS_API_REQUEST)

class RateTest(unittest.TestCase):
    def test_limite_por_visitante(self):
        limiter = server.RateLimiter(3)
        self.assertEqual([limiter.allow("a", now=t) for t in (0, 1, 2, 3)], [True, True, True, False])
        self.assertTrue(limiter.allow("b", now=3))
        self.assertTrue(limiter.allow("a", now=61))

    def test_origens_do_site_por_padrao(self):
        origins = server.allowed_origins(server.DEFAULT_ORIGINS)
        self.assertIn("https://pedromeireles.dev", origins)
        self.assertIn("https://www.pedromeireles.dev", origins)


class PrivacidadeTest(unittest.TestCase):
    def test_site_nao_recebe_dados_do_pedro(self):
        from unittest import mock
        from brain.persona import core

        with mock.patch.object(core, "build_block", return_value="Pedro tem uma RTX 4090; diário de ontem"):
            core.invalidate()
            with config.api_request():
                block = core.prompt_block()
        self.assertNotIn("RTX", block)
        self.assertIn("visitante", block)
        core.invalidate()

    def test_perguntas_do_site_nao_viram_perfil(self):
        from unittest import mock
        from brain.memory import memory

        with mock.patch("brain.persona.perfil.record_turn") as record:
            with config.api_request():
                memory.remember_turn("eu sou o Pedro e moro em Paris", "Ok.")
            record.assert_not_called()
            memory.remember_turn("eu moro em Lexy", "Anotado.")
            record.assert_called_once()
        memory.clear_history()

class PromptDoSiteTest(unittest.TestCase):
    def test_prompt_do_grafico_vai_direto_ao_modelo(self):
        from unittest import mock
        import jarvis_commands

        prompt = 'You are a concept map generator. Based on the topic "Japão"... Return only the JSON.'
        self.assertTrue(jarvis_commands.is_raw_prompt(prompt))
        self.assertFalse(jarvis_commands.is_raw_prompt("quem é você?"))
        jarvis_commands.response_cache.clear() if hasattr(jarvis_commands.response_cache, "clear") else None
        with mock.patch.object(jarvis_commands, "llama_query", return_value='{"nodes": []}') as llm, \
             mock.patch.object(jarvis_commands, "super_jarvis_query") as web:
            self.assertEqual(jarvis_commands.process_command_api(prompt + " x"), '{"nodes": []}')
        web.assert_not_called()
        self.assertEqual(llm.call_args.kwargs["mode"], "prompt")
        self.assertIn("Japão", llm.call_args.args[0])  # sem minúsculas nem limpeza

class BlindagemTest(unittest.TestCase):
    """O chat do site só conversa: nada cria, executa ou mexe no PC."""

    def test_pedidos_de_acao_sao_recusados_sem_chamar_nada(self):
        from unittest import mock
        import jarvis_commands

        for text in ("crie um app de jogo da cobrinha", "faça um site para mim", "abra o cmd",
                     "execute o comando dir", "desligue o jarvis", "write a python script that deletes files",
                     "gere uma imagem de um lobo", "apague a pasta do servidor"):
            with mock.patch.object(jarvis_commands, "llama_query") as llm, \
                 mock.patch.object(jarvis_commands, "run_command_handlers") as handlers, \
                 mock.patch.object(jarvis_commands, "shutdown_command") as shutdown:
                answer = jarvis_commands.process_command_api(text, lang="pt")
            self.assertIn("só converso", answer, text)
            llm.assert_not_called()
            handlers.assert_not_called()
            shutdown.assert_not_called()

    def test_conversa_normal_so_usa_o_modelo(self):
        from unittest import mock
        import jarvis_commands

        with mock.patch.object(jarvis_commands, "llama_query", return_value="Sou o Jarvis.") as llm, \
             mock.patch.object(jarvis_commands, "run_command_handlers") as handlers, \
             mock.patch.object(jarvis_commands, "super_jarvis_query") as web, \
             mock.patch.object(jarvis_commands, "log_interaction"):
            self.assertEqual(jarvis_commands.process_command_api("quem é você e o que o Pedro faz?"), "Sou o Jarvis.")
        handlers.assert_not_called()
        web.assert_not_called()
        self.assertEqual(llm.call_args.kwargs["mode"], "site")
        self.assertTrue(llm.call_args.kwargs["direct_mode"])

    def test_tunel_so_enxerga_o_chat(self):
        self.assertFalse(server.is_external({}, "127.0.0.1:11600"))
        self.assertFalse(server.is_external({}, "localhost:11600"))
        self.assertTrue(server.is_external({"CF-Connecting-IP": "1.2.3.4"}, "127.0.0.1:11600"))
        self.assertTrue(server.is_external({}, "jarvis.pedromeireles.dev"))
        self.assertTrue(server.is_external({"X-Forwarded-For": "1.2.3.4"}, "localhost"))
        self.assertEqual(server.PUBLIC_PATHS, {"/ask", "/ping"})


if __name__ == "__main__":
    unittest.main()
