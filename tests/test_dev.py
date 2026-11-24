"""Fase 8: modo programador (pasta isolada, execução, ciclo de correção)."""
import os
import sys
import tempfile
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401
from brain.dev import agente, executor, projeto


class ProjetoTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.p = projeto.Project("Calculadora de Gorjeta!", self.base)
        self.p.create("uma calculadora de gorjeta")

    def test_nome_e_readme(self):
        self.assertEqual(self.p.name, "calculadora_de_gorjeta")
        self.assertIn("uma calculadora de gorjeta", self.p.read("README.md"))
        self.assertEqual(projeto.list_projects(self.base), ["calculadora_de_gorjeta"])

    def test_nada_sai_da_pasta(self):
        for bad in ("../fora.txt", "C:/Windows/x.py", "/etc/passwd", "a/../../b.py", ".jarvis/historico.json", ""):
            with self.assertRaises(projeto.OutsideProject, msg=bad):
                self.p.write(bad, "x")
        self.assertEqual(self.p.write("src/app.py", "print(1)"), os.path.join("src", "app.py"))

    def test_achar_pelo_nome_falado(self):
        self.assertEqual(projeto.find_project("o app da calculadora", self.base).name, "calculadora_de_gorjeta")
        self.assertIsNone(projeto.find_project("jogo da cobrinha", self.base))

    def test_historico(self):
        self.p.add_history("adicione modo escuro", "Botão de tema escuro.", True)
        self.assertEqual(self.p.history()[-1]["pedido"], "adicione modo escuro")
        self.assertIn("Botão de tema escuro.", self.p.read("README.md"))


class ExecutorTest(unittest.TestCase):
    def setUp(self):
        self.p = projeto.Project("teste", tempfile.mkdtemp())
        self.p.create("teste")
        # sem criar venv de verdade: usa o Python atual
        patcher = mock.patch.object(executor, "ensure_venv", return_value=sys.executable)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_ok_erro_e_abriu(self):
        self.p.write("ok.py", "print('olá')")
        self.p.write("bug.py", "print(1/0)")
        self.p.write("janela.py", "import time\nprint('abrindo', flush=True)\ntime.sleep(30)")
        self.assertEqual(executor.run(self.p, "ok.py")[0], "ok")
        status, out = executor.run(self.p, "bug.py")
        self.assertEqual(status, "erro")
        self.assertIn("ZeroDivisionError", out)
        self.assertEqual(executor.run(self.p, "janela.py", timeout=2)[0], "abriu")
        self.assertEqual(executor.run(self.p, "nao_existe.py")[0], "erro")

    def test_pacote_suspeito_recusado(self):
        for bad in (["--index-url=http://mal.com", "x"], ["requests; rm -rf /"], []):
            ok, _ = executor.install(self.p, bad)
            self.assertFalse(ok, bad)


def _call(name, **args):
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": args}}]}


class AgenteTest(unittest.TestCase):
    def setUp(self):
        self.p = projeto.Project("soma", tempfile.mkdtemp())
        self.p.create("um programa que soma 2 e 3")
        patcher = mock.patch.object(executor, "ensure_venv", return_value=sys.executable)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_escreve_roda_corrige_e_termina(self):
        script = iter([
            _call("criar_arquivo", caminho="main.py", conteudo="print(2 + tres)" + "\n#" * 500),
            _call("rodar_app", arquivo="main.py"),
            _call("criar_arquivo", caminho="main.py", conteudo="print(2 + 3)"),
            _call("rodar_app", arquivo="main.py"),
            _call("terminar", resumo="Programa que soma 2 e 3.", como_rodar="python main.py",
                  arquivo_principal="main.py", funcionou=True),
        ])
        seen = []

        def llm(messages):
            seen.append(list(messages))
            return next(script)

        result = agente.Session(self.p, "soma", llm=llm, log=lambda *_: None).work()
        self.assertTrue(result["ok"])
        self.assertEqual(self.p.read("main.py"), "print(2 + 3)")
        tool_texts = [m["content"] for m in seen[-1] if m.get("role") == "tool"]
        self.assertTrue(any("NameError" in t for t in tool_texts))  # o erro voltou para o modelo
        compacted = [m for m in seen[-1] if m.get("role") == "assistant" and m.get("tool_calls")][0]
        self.assertIn("linhas salvas", compacted["tool_calls"][0]["function"]["arguments"]["conteudo"])

    def test_sem_permissao_nao_roda(self):
        script = iter([_call("rodar_app", arquivo="main.py"),
                       _call("terminar", resumo="Escrevi os arquivos.", funcionou=True)])
        session = agente.Session(self.p, "soma", allow_run=False, llm=lambda m: next(script), log=lambda *_: None)
        with mock.patch.object(executor, "run") as run:
            result = session.work()
        run.assert_not_called()
        self.assertTrue(result["ok"])

    def test_dizer_que_funcionou_sem_testar_nao_vale(self):
        script = iter([_call("criar_arquivo", caminho="main.py", conteudo="print(1/0)"),
                       _call("terminar", resumo="Pronto.", funcionou=True)])
        result = agente.Session(self.p, "x", llm=lambda m: next(script), log=lambda *_: None).work()
        self.assertFalse(result["ok"])

    def test_limite_de_tentativas(self):
        self.p.write("main.py", "print(1/0)")
        calls = iter([_call("rodar_app", arquivo="main.py")] * 7 +
                     [_call("terminar", resumo="Travei no 1/0.", funcionou=False)])
        result = agente.Session(self.p, "x", llm=lambda m: next(calls), log=lambda *_: None).work()
        self.assertFalse(result["ok"])

    def test_em_segundo_plano_um_por_vez(self):
        said = []
        with mock.patch.object(agente, "Session") as session:
            session.return_value.work.return_value = {"ok": True, "resumo": "Feito.", "como_rodar": "python main.py",
                                                      "principal": "main.py", "passos": 3}
            with mock.patch.object(executor, "open_folder"):
                import threading
                gate = threading.Event()
                session.return_value.work.side_effect = lambda: (gate.wait(2), session.return_value.work.return_value)[1]
                self.assertTrue(agente.run_in_background(self.p, "soma", True, False, said.append))
                self.assertFalse(agente.run_in_background(self.p, "outra", True, False, said.append))
                gate.set()
                for _ in range(100):
                    if said:
                        break
                    import time
                    time.sleep(0.02)
        self.assertIn("Terminei o app soma. Feito.", said[0])
        self.assertIn("python main.py", said[0])


class FerramentaTest(unittest.TestCase):
    def test_sim_e_nao(self):
        from brain import tools

        for yes in ("sim", "pode sim", "claro, manda ver", "ok"):
            self.assertTrue(tools._is_yes(yes), yes)
        for no in ("não", "não pode", "", "espera um pouco", "sim, mas não instala"):
            self.assertFalse(tools._is_yes(no), no)


if __name__ == "__main__":
    unittest.main()
