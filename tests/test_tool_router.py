"""Roteador por ferramentas (brain/tool_router.py) e ferramentas (brain/tools.py).

Usa respostas simuladas no formato de stream do Ollama; nada de rede ou áudio.
"""
import json
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401  (instala os dublês de áudio e bibliotecas)
from brain import tool_router, tools


class FakeResponse:
    def __init__(self, lines):
        self.lines = [json.dumps(line).encode() for line in lines]
        self.closed = False

    def iter_lines(self):
        return iter(self.lines)

    def close(self):
        self.closed = True


def text_reply(*pieces):
    return FakeResponse([{"message": {"content": p}, "done": False} for p in pieces] + [{"done": True}])


def tool_reply(*calls, content=""):
    message = {"content": content, "tool_calls": [
        {"function": {"name": name, "arguments": args}} for name, args in calls
    ]}
    return FakeResponse([{"message": message, "done": False}, {"done": True}])


class RouterTest(unittest.TestCase):
    def setUp(self):
        self.spoken = []
        self.ran = []
        patches = [
            mock.patch.object(tool_router, "remember_turn"),
            mock.patch.object(tool_router, "memory_context", []),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def speak(self, pieces):
        text = "".join(pieces)
        self.spoken.append(text)
        return text

    def run_tool(self, name, args):
        self.ran.append((name, args))
        info = name in ("buscar_na_internet", "previsao_do_tempo")
        return (f"resultado de {name}", True) if info else (f"{name} feito", False)

    def handle(self, query, replies, interrupted=lambda: False):
        with mock.patch.object(tool_router, "open_chat", side_effect=replies) as chat:
            answer = tool_router.handle(query, speak=self.speak, run_tool=self.run_tool,
                                        interrupted=interrupted)
        return answer, chat

    def test_resposta_direta_sem_ferramentas(self):
        answer, chat = self.handle("como funciona a fotossíntese", [text_reply("As plantas ", "usam luz.")])
        self.assertEqual(answer, "As plantas usam luz.")
        self.assertEqual(self.spoken, ["As plantas usam luz."])
        self.assertEqual(self.ran, [])
        self.assertEqual(chat.call_count, 1)
        self.assertIn("tools", chat.call_args.kwargs)
        tool_router.remember_turn.assert_called_once_with("como funciona a fotossíntese", "As plantas usam luz.")

    def test_busca_volta_para_o_modelo_formular_a_resposta(self):
        replies = [tool_reply(("buscar_na_internet", {"consulta": "GPT-6.2 Astra"})),
                   text_reply("O Astra saiu em 17/11.")]
        answer, chat = self.handle("o que é o astra", replies)
        self.assertEqual(self.ran, [("buscar_na_internet", {"consulta": "GPT-6.2 Astra"})])
        self.assertEqual(answer, "O Astra saiu em 17/11.")
        followup = chat.call_args_list[1].args[0]
        tool_messages = [m for m in followup if m["role"] == "tool"]
        self.assertEqual(tool_messages[0]["content"], "resultado de buscar_na_internet")
        self.assertNotIn("tools", chat.call_args_list[1].kwargs)  # segunda chamada sem ferramentas

    def test_duas_acoes_na_ordem_sem_segunda_chamada(self):
        replies = [tool_reply(("abrir_programa", {"programa": "steam"}),
                              ("musica", {"acao": "tocar", "busca": "Queen"}))]
        answer, chat = self.handle("abra o steam e toque queen", replies)
        self.assertEqual([name for name, _ in self.ran], ["abrir_programa", "musica"])
        self.assertEqual(chat.call_count, 1)
        self.assertIn("abrir_programa feito", answer)

    def test_abrir_navegador_junto_com_pesquisa_nao_abre_janela_vazia(self):
        replies = [tool_reply(("abrir_programa", {"programa": "navegador"}),
                              ("pesquisar_no_google", {"consulta": "build ranger pvp aion 2"}))]
        self.handle("abra o chrome e pesquise a build", replies)
        self.assertEqual([name for name, _ in self.ran], ["pesquisar_no_google"])

    def test_abrir_steam_junto_com_pesquisa_continua(self):
        replies = [tool_reply(("abrir_programa", {"programa": "steam"}),
                              ("pesquisar_no_google", {"consulta": "aion 2"}))]
        self.handle("abra o steam e pesquise aion 2", replies)
        self.assertEqual([name for name, _ in self.ran], ["abrir_programa", "pesquisar_no_google"])

    def test_erro_do_ollama_aciona_a_reserva(self):
        with self.assertRaises(tool_router.RouterUnavailable):
            self.handle("oi", [RuntimeError("model does not support tools")])

    def test_interrompido_nao_executa_ferramentas(self):
        replies = [tool_reply(("abrir_programa", {"programa": "steam"}), content="Vou abrir. ")]
        self.handle("abra o steam", replies, interrupted=lambda: True)
        self.assertEqual(self.ran, [])

    def test_prompt_tem_data_e_orientacao(self):
        messages = tool_router._base_messages("oi", "pt")
        self.assertIn("Hoje é", messages[0]["content"])
        self.assertIn("ferramentas", messages[0]["content"])


class ToolsTest(unittest.TestCase):
    def test_esquemas_validos(self):
        names = [schema["function"]["name"] for schema in tools.schemas()]
        self.assertEqual(len(names), len(set(names)))
        for tool in tools.TOOLS:
            self.assertTrue(set(tool.required) <= set(tool.properties), tool.name)
            self.assertTrue(tool.description)

    def test_argumentos_em_texto_json_e_campos_extras(self):
        received = {}

        def fake(consulta):
            received["consulta"] = consulta
            return "ok"

        tool = tools.Tool("teste", "d", fake, {"consulta": {"type": "string"}}, ["consulta"], True)
        with mock.patch.dict(tools.BY_NAME, {"teste": tool}):
            self.assertEqual(tools.run_tool("teste", '{"consulta": "x", "extra": 1}'), ("ok", True))
        self.assertEqual(received, {"consulta": "x"})

    def test_pesquisar_no_google_abre_os_resultados_no_chrome(self):
        opened = []
        with mock.patch("brain.system.open_in_chrome", side_effect=opened.append), \
             mock.patch.object(tools, "_say"):
            tools.pesquisar_no_google("build de ranger pvp aion 2")
        self.assertEqual(opened, ["https://www.google.com/search?q=build+de+ranger+pvp+aion+2"])

    def test_abrir_site_monta_a_url_e_recusa_lixo(self):
        opened = []
        with mock.patch("brain.system.open_in_chrome", side_effect=opened.append), \
             mock.patch.object(tools, "_say"):
            tools.abrir_site("www.youtube.com")
            tools.abrir_site("https://www.youtube.com/results?search_query=queen")
            result = tools.abrir_site("javascript:alert(1)")
        self.assertEqual(opened, ["https://www.youtube.com",
                                  "https://www.youtube.com/results?search_query=queen"])
        self.assertIn("inválido", result)

    def test_tocar_no_youtube_abre_o_primeiro_video(self):
        page = mock.Mock(text='... "videoId":"fJ9rUzIMcZQ" ... "videoId":"outro123456"')
        opened = []
        with mock.patch("requests.get", return_value=page) as get, \
             mock.patch("brain.media_window.open_media", side_effect=opened.append), \
             mock.patch.object(tools, "_say"):
            tools.tocar_no_youtube("queen bohemian rhapsody")
        self.assertEqual(opened, ["https://www.youtube.com/watch?v=fJ9rUzIMcZQ"])
        self.assertIn("search_query=queen+bohemian+rhapsody", get.call_args.args[0])

    def test_tocar_no_youtube_sem_video_abre_a_busca(self):
        opened = []
        with mock.patch("requests.get", side_effect=OSError("sem rede")), \
             mock.patch("brain.media_window.open_media", side_effect=opened.append), \
             mock.patch.object(tools, "_say"):
            tools.tocar_no_youtube("queen")
        self.assertEqual(opened, ["https://www.youtube.com/results?search_query=queen"])

    def test_ferramenta_desconhecida_ou_com_erro_vira_texto(self):
        self.assertIn("desconhecida", tools.run_tool("nao_existe", {})[0])
        broken = tools.Tool("quebrada", "d", lambda: 1 / 0)
        with mock.patch.dict(tools.BY_NAME, {"quebrada": broken}):
            text, for_model = tools.run_tool("quebrada", {})
        self.assertIn("falhou", text)
        self.assertTrue(for_model)


class ResponseCacheTest(unittest.TestCase):
    def test_validade_e_limite(self):
        import jarvis_commands

        cache = jarvis_commands.ResponseCache(ttl=60, max_items=2)
        with mock.patch.object(jarvis_commands.time, "monotonic", return_value=100):
            cache["a"] = 1
            cache["b"] = 2
            cache["c"] = 3
        self.assertEqual(len(cache), 2)
        with mock.patch.object(jarvis_commands.time, "monotonic", return_value=120):
            self.assertIsNone(cache.get("a"))  # o mais antigo saiu
            self.assertEqual(cache.get("c"), 3)
        with mock.patch.object(jarvis_commands.time, "monotonic", return_value=200):
            self.assertIsNone(cache.get("c"))  # passou da validade


class ProcessCommandRoutingTest(unittest.TestCase):
    def setUp(self):
        import jarvis_commands

        self.jc = jarvis_commands

    def test_atalho_nao_chama_o_modelo(self):
        with mock.patch.object(self.jc, "TOOL_ROUTER_ENABLED", True), \
             mock.patch.object(self.jc.tool_router, "handle", side_effect=AssertionError("chamou o modelo")):
            self.assertTrue(self.jc.process_command("que horas são"))

    def test_roteador_atende_a_frase(self):
        with mock.patch.object(self.jc, "TOOL_ROUTER_ENABLED", True), \
             mock.patch.object(self.jc.tool_router, "handle", return_value="resposta") as handle, \
             mock.patch.object(self.jc, "log_interaction") as log, \
             mock.patch.object(self.jc, "should_save_to_file", return_value=False), \
             mock.patch.object(self.jc, "generate_response", side_effect=AssertionError("caminho antigo")):
            self.assertTrue(self.jc.process_command("abra o steam e toque queen"))
        handle.assert_called_once()
        log.assert_called_once_with("abra o steam e toque queen", "resposta")

    def test_roteador_indisponivel_usa_o_caminho_antigo(self):
        with mock.patch.object(self.jc, "TOOL_ROUTER_ENABLED", True), \
             mock.patch.object(self.jc.tool_router, "handle", side_effect=self.jc.tool_router.RouterUnavailable("sem tools")), \
             mock.patch.object(self.jc, "handle_weather_query", return_value=False), \
             mock.patch.object(self.jc, "run_command_handlers", return_value=(False, None)), \
             mock.patch.object(self.jc, "generate_response", return_value="antigo") as old, \
             mock.patch.object(self.jc, "log_interaction"), \
             mock.patch.object(self.jc, "should_save_to_file", return_value=False):
            self.assertTrue(self.jc.process_command("explique algo"))
        old.assert_called_once()


if __name__ == "__main__":
    unittest.main()
