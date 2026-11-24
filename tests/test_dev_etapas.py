"""Programador por etapas: perguntas, plano aprovado, etapas testadas, cancelar."""
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401
from brain import tools
from brain.dev import agente, conversa, executor, planejador, projeto


def _call(name, **args):
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": args}}]}


PLAN = {"entendimento": "Uma calculadora com janela.", "perguntas": ["Quer histórico das contas? (sugestão: sim)"],
        "opcoes": [{"abordagem": "Python + Tkinter", "pros": "leve", "contras": "visual simples"},
                   {"abordagem": "Web (HTML/JS)", "pros": "bonito", "contras": "precisa do navegador"}],
        "recomendacao": "Python + Tkinter: roda direto no Windows.",
        "etapas": [{"titulo": "Janela e soma", "descricao": "Tela com dois campos", "teste": "soma 2+3"},
                   {"titulo": "Histórico", "descricao": "Lista das contas", "teste": "mostra as contas"}],
        "pacotes": [], "arquivo_principal": "main.py"}


def _reply_when_asked(replies, said):
    """Responde às perguntas do programador como o Pedro faria (outra thread)."""
    def loop():
        for reply in replies:
            for _ in range(300):
                if conversa.pending():
                    break
                time.sleep(0.01)
            said.append(("pergunta", conversa.pending()["texto"]))
            conversa.answer(reply)
            time.sleep(0.05)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread


class PlanejadorTest(unittest.TestCase):
    def test_normaliza_e_markdown(self):
        plan = planejador.normalize(PLAN)
        self.assertEqual(len(plan["etapas"]), 2)
        md = planejador.to_markdown(plan, "calculadora", done=1)
        self.assertIn("- [x] 1. **Janela e soma**", md)
        self.assertIn("- [ ] 2. **Histórico**", md)
        self.assertIn("Python + Tkinter", md)
        self.assertIn("2 etapas", planejador.spoken_summary(plan))

    def test_plano_vazio_vira_uma_etapa(self):
        plan = planejador.normalize({})
        self.assertEqual(len(plan["etapas"]), 1)
        self.assertEqual(plan["perguntas"], [])

    def test_depois_das_respostas_nao_pergunta_de_novo(self):
        project = projeto.Project("x", tempfile.mkdtemp())
        project.create("x")
        seen = {}

        def llm(system, user):
            seen["user"] = user
            return PLAN

        plan = planejador.make_plan("calculadora", project, answers=[("Histórico?", "sim")], llm=llm)
        self.assertEqual(plan["perguntas"], [])
        self.assertIn("Histórico? -> sim", seen["user"])


class ConversaTest(unittest.TestCase):
    def test_pergunta_e_resposta(self):
        said = []
        _reply_when_asked(["sim"], said)
        self.assertEqual(conversa.ask("Pode começar?", "calc", say=lambda t: None, timeout=5), "sim")
        self.assertIsNone(conversa.pending())
        self.assertFalse(conversa.answer("ninguém perguntou"))

    def test_sem_resposta_volta_none(self):
        self.assertIsNone(conversa.ask("Oi?", "calc", timeout=0.3))


class ProjetoPorEtapasTest(unittest.TestCase):
    def setUp(self):
        conversa.cancel_flag.clear()
        self.project = projeto.Project("calculadora", tempfile.mkdtemp())
        self.project.create("uma calculadora")
        patcher = mock.patch.object(executor, "ensure_venv", return_value=sys.executable)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(conversa.cancel_flag.clear)

    def _run(self, replies, llm_script, plan=PLAN):
        said, done = [], threading.Event()
        planner = lambda request, project, answers=None, changes=None: planejador.normalize(  # noqa: E731
            plan, no_questions=bool(answers or changes))
        script = iter(llm_script)
        _reply_when_asked(replies, said)
        with mock.patch.object(executor, "open_folder"):
            self.assertTrue(agente.run_project(self.project, "uma calculadora", False, said.append,
                                               on_done=done.set, llm=lambda m: next(script),
                                               planner=planner, log=lambda *a: None))
            self.assertTrue(done.wait(10))
        return said

    def test_pergunta_aprova_e_faz_as_etapas(self):
        said = self._run(["sim, com histórico", "pode começar"], [
            _call("criar_arquivo", caminho="main.py", conteudo="print(2 + 3)"),
            _call("rodar_app", arquivo="main.py"),
            _call("terminar", resumo="Janela com soma.", funcionou=True),
            _call("criar_arquivo", caminho="main.py", conteudo="print(2 + 3)\nprint('historico')"),
            _call("rodar_app", arquivo="main.py"),
            _call("terminar", resumo="Histórico das contas.", funcionou=True, como_rodar="python main.py"),
        ])
        texts = [s if isinstance(s, str) else s[1] for s in said]
        self.assertTrue(any("1 pergunta" in t for t in texts))
        self.assertTrue(any("Posso começar" in t for t in texts))
        self.assertTrue(any("Etapa 1 de 2 pronta" in t for t in texts))
        self.assertTrue(any("Terminei o app calculadora, 2 etapas testadas" in t for t in texts))
        plano = self.project.read("PLANO.md")
        self.assertIn("- [x] 2. **Histórico**", plano)
        self.assertTrue(self.project.history()[-1]["funcionou"])

    def test_cancelar_na_aprovacao(self):
        said = self._run(["sim", "cancela, não quero mais"], [])
        self.assertTrue(any("cancelei" in s for s in said if isinstance(s, str)))
        self.assertNotIn("main.py", self.project.files())

    def test_pedir_mudanca_refaz_o_plano(self):
        calls = []
        plan_no_q = dict(PLAN, perguntas=[])

        def planner(request, project, answers=None, changes=None):
            calls.append(changes)
            return planejador.normalize(plan_no_q, no_questions=bool(changes))

        said, done = [], threading.Event()
        script = iter([_call("terminar", resumo="ok", funcionou=False)])
        _reply_when_asked(["troca para web", "sim"], said)
        with mock.patch.object(executor, "open_folder"):
            agente.run_project(self.project, "calc", False, said.append, on_done=done.set,
                               llm=lambda m: next(script), planner=planner, log=lambda *a: None)
            done.wait(10)
        self.assertEqual(calls, [None, "troca para web"])
        self.assertTrue(any("ajustar o plano" in s for s in said if isinstance(s, str)))


class FerramentasTest(unittest.TestCase):
    def test_responder_sem_pergunta(self):
        with mock.patch.object(tools, "_say"):
            self.assertIn("Não havia", tools.run_tool("responder_programador", {"resposta": "sim"})[0])

    def test_roteador_ve_a_pergunta_pendente(self):
        from brain import tool_router

        with mock.patch.object(conversa, "pending", return_value={"app": "calc", "texto": "Posso começar?"}):
            messages = tool_router._base_messages("sim", "pt")
        self.assertIn("responder_programador", messages[0]["content"])
        self.assertIn("Posso começar?", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
