"""Fase 7: personalidade, perfil do Pedro, diário e limites."""
import os
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401 (banco temporário e bibliotecas falsas)
from core.settings import MEMORY_DB
from brain import semantic_memory
from brain.persona import core, diario, limites, perfil
from brain.persona.store import connect


def _clean():
    semantic_memory._connect().close()  # cria a tabela memorias se faltar
    with connect() as conn:
        for table in ("turnos", "diario", "humor", "opinioes", "memorias"):
            conn.execute(f"DELETE FROM {table}")
    core.invalidate()


class BancoTest(unittest.TestCase):
    def test_testes_usam_banco_temporario(self):
        self.assertIn("jarvis_teste_", MEMORY_DB)
        self.assertNotIn(os.path.join("brain", "learning"), MEMORY_DB)


class PersonaTest(unittest.TestCase):
    def setUp(self):
        _clean()

    def test_humor_do_dia_fica_o_mesmo(self):
        first = core.mood_of_day("2026-11-24")
        self.assertEqual(core.mood_of_day("2026-11-24"), first)
        self.assertIn(first[0], core.load_persona()["humores"])

    def test_bloco_tem_tracos_humor_perfil_e_diario(self):
        with mock.patch.object(semantic_memory, "embed", return_value=None):
            semantic_memory.add("preferência", "Pedro joga Aion 2 com a classe Ranger.", "conversa", "perfil")
        from datetime import date, timedelta

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        with connect() as conn:
            conn.execute("INSERT INTO diario VALUES (?, ?, ?)", (yesterday, "Falamos do FLUX.", "x"))
        block = core.prompt_block()
        self.assertIn("leal ao Pedro", block)
        self.assertIn("Hoje você", block)
        self.assertIn("Ranger", block)
        self.assertIn("Ontem, no seu diário: Falamos do FLUX.", block)

    def test_bloco_entra_no_roteador(self):
        from brain import tool_router

        with mock.patch.object(tool_router, "persona_block", return_value="\nBLOCO-PERSONA"):
            messages = tool_router._base_messages("oi", "pt")
        self.assertIn("BLOCO-PERSONA", messages[0]["content"])


class PerfilTest(unittest.TestCase):
    def setUp(self):
        _clean()

    def test_extrai_fatos_e_marca_turnos(self):
        perfil.record_turn("eu comprei uma RTX 4090 semana passada", "Ótima placa.")
        perfil.record_turn("que horas são", "São 10h.")
        answer = {"fatos": [{"categoria": "fato", "fato": "Pedro tem uma RTX 4090."},
                            {"categoria": "xx", "fato": "curto"}, "lixo"]}
        with mock.patch.object(perfil.llm, "ask", return_value=answer), \
             mock.patch.object(semantic_memory, "embed", return_value=None):
            self.assertEqual(perfil.process_pending(), 1)
            self.assertEqual(perfil.pending_turns(), [])
            self.assertEqual(perfil.process_pending(), 0)  # nada novo: nem chama o modelo
        self.assertEqual(perfil.profile_facts(), ["Pedro tem uma RTX 4090."])

    def test_fato_parecido_atualiza_em_vez_de_repetir(self):
        with mock.patch.object(semantic_memory, "embed", return_value=None):
            self.assertEqual(perfil.save_fact("projeto", "Pedro está criando o Jarvis em Python."), "novo")
            first_id = perfil.semantic_memory._connect().execute("SELECT MAX(id) FROM memorias").fetchone()[0]
            with mock.patch.object(semantic_memory, "search",
                                   return_value=[{"id": first_id, "score": 0.95}]):
                self.assertEqual(perfil.save_fact("projeto", "Pedro está criando o Jarvis em Python 3."), "atualizado")
        self.assertEqual(perfil.profile_facts(), ["Pedro está criando o Jarvis em Python 3."])

    def test_modelo_fora_nao_quebra_e_nao_perde_turnos(self):
        perfil.record_turn("eu moro em Lexy", "Anotado.")
        with mock.patch.object(perfil.llm, "ask", side_effect=OSError("ollama fora")):
            self.assertEqual(perfil.process_pending(), 0)
        self.assertEqual(len(perfil.pending_turns()), 1)


class DiarioTest(unittest.TestCase):
    def setUp(self):
        _clean()

    def test_escreve_dias_passados_uma_vez(self):
        with connect() as conn:
            conn.executemany("INSERT INTO turnos (criado, pergunta, resposta) VALUES (?, ?, ?)", [
                ("2026-11-20 10:00:00", "crie uma imagem de lobo", "Pronto."),
                ("2099-01-01 10:00:00", "hoje", "ainda não acabou"),
            ])
        with mock.patch.object(diario.llm, "ask", return_value="Hoje fizemos um lobo.") as ask:
            self.assertEqual(diario.catch_up(), 1)
            self.assertEqual(diario.catch_up(), 0)
        ask.assert_called_once()
        self.assertEqual(diario.read("2026-11-20"), "Hoje fizemos um lobo.")


class LimitesTest(unittest.TestCase):
    def test_so_leitura(self):
        self.assertTrue(limites.allowed("buscar_na_internet"))
        for name in ("abrir_programa", "esquecer", "memorizar", "criar_imagem", "tocar_no_youtube"):
            self.assertFalse(limites.allowed(name), name)
        with self.assertRaises(limites.NotAllowed):
            limites.autonomous_tool("abrir_programa", {"programa": "cmd"})

    def test_urls(self):
        self.assertEqual(limites.check_url("https://pt.wikipedia.org/wiki/Lobo"), "https://pt.wikipedia.org/wiki/Lobo")
        for bad in ("file:///C:/x", "http://127.0.0.1:11500/api", "http://192.168.0.1", "ftp://x"):
            with self.assertRaises(limites.NotAllowed):
                limites.check_url(bad)


if __name__ == "__main__":
    unittest.main()
