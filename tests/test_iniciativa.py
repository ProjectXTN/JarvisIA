"""Fase 7: iniciativa (compromissos, puxar assunto) e painel."""
import sys
import unittest
from datetime import datetime
from unittest import mock

import tests.test_regressao  # noqa: F401
from tests.test_persona import _clean
from brain import semantic_memory, tools
from brain.persona import iniciativa, painel
from brain.persona.store import connect
from core import config


def _reset():
    _clean()
    iniciativa._table()
    with connect() as conn:
        conn.execute("DELETE FROM compromissos")
        conn.execute("DELETE FROM mencionados")


class CompromissoTest(unittest.TestCase):
    def setUp(self):
        _reset()

    def test_datas(self):
        self.assertEqual(iniciativa.parse_when("2026-11-25T15:00"), datetime(2026, 11, 25, 15, 0))
        self.assertEqual(iniciativa.parse_when("2026-11-25T15:00:00Z"), datetime(2026, 11, 25, 15, 0))
        self.assertEqual(iniciativa.parse_when("25/11/2026 08:30"), datetime(2026, 11, 25, 8, 30))
        self.assertEqual(iniciativa.parse_when("2026-11-25"), datetime(2026, 11, 25, 9, 0))
        self.assertIsNone(iniciativa.parse_when("amanhã"))
        now = datetime(2026, 11, 24, 10, 0)
        self.assertEqual(iniciativa.spoken_time(datetime(2026, 11, 25, 15, 0), now), "amanhã às 15h")
        self.assertEqual(iniciativa.spoken_time(datetime(2026, 11, 24, 18, 30), now), "hoje às 18h30")

    def test_ferramenta_anota_e_avisa_na_hora_uma_vez(self):
        spoken = []
        with mock.patch.object(tools, "_say", side_effect=spoken.append):
            tools.run_tool("lembrar_compromisso", {"quando": "2026-11-25T15:00", "o_que": "ligar para o banco"})
        self.assertIn("ligar para o banco", spoken[0])
        self.assertEqual(iniciativa.due(datetime(2026, 11, 25, 14, 59)), [])
        said = []
        with mock.patch.object(sys.modules["brain.audio"], "say", side_effect=said.append):
            with mock.patch.object(iniciativa, "due", return_value=iniciativa.due(datetime(2026, 11, 25, 15, 1))):
                iniciativa.check_and_announce()
        self.assertEqual(said, ["Pedro, lembrete: ligar para o banco."])
        self.assertEqual(iniciativa.due(datetime(2026, 11, 25, 15, 5)), [])

    def test_lembrete_espera_terminar_de_atender(self):
        iniciativa.add_reminder("2026-11-25T15:00", "reunião")
        config.NOT_BUSY.clear()
        try:
            with mock.patch.object(config.NOT_BUSY, "wait") as wait, mock.patch.object(sys.modules["brain.audio"], "say"), \
                 mock.patch.object(iniciativa, "due", return_value=iniciativa.due(datetime(2026, 11, 25, 15, 0))):
                iniciativa.check_and_announce()
            wait.assert_called_once()
        finally:
            config.NOT_BUSY.set()

    def test_cancelar(self):
        iniciativa.add_reminder("2026-11-25T15:00", "ligar para o banco")
        self.assertEqual(iniciativa.cancel("o lembrete do banco"), "ligar para o banco")
        self.assertIsNone(iniciativa.cancel("dentista"))


class AberturaTest(unittest.TestCase):
    def setUp(self):
        _reset()

    def test_compromisso_do_dia_e_assunto_novo_uma_vez(self):
        now = datetime(2026, 11, 24, 8, 0)
        iniciativa.add_reminder("2026-11-24T18:00", "buscar o carro")
        with mock.patch.object(semantic_memory, "embed", return_value=None):
            semantic_memory.add("lobo cinzento", "Vive 6 a 8 anos.", "Wiki (confiança media, estudado sozinho)", "aprendido")
            semantic_memory.add("impressora", "HP", "Pedro", "fato")
        lines = iniciativa.opening_lines(now)
        self.assertEqual(lines[0], "Seus compromissos de hoje: hoje às 18h, buscar o carro.")
        self.assertIn("estudei sobre lobo cinzento", lines[1])
        self.assertEqual(len(iniciativa.opening_lines(now)), 1)  # o assunto não repete


class PainelTest(unittest.TestCase):
    def setUp(self):
        _reset()

    def test_listar_corrigir_apagar(self):
        with mock.patch.object(semantic_memory, "embed", return_value=None):
            semantic_memory.add("preferência", "Pedro gosta de jazz.", "conversa", "perfil")
            data = painel.overview()
            memory_id = data["perfil"][0]["id"]
            painel.edit_memory(memory_id, "Pedro gosta de jazz e blues.")
        self.assertEqual(painel.overview()["perfil"][0]["texto"], "Pedro gosta de jazz e blues.")
        self.assertEqual(painel.delete_memory(memory_id), 1)
        self.assertEqual(painel.overview()["perfil"], [])

    def test_so_campos_permitidos(self):
        iniciativa.add_reminder("2026-11-25T15:00", "banco")
        row = painel.overview()["compromissos"][0]
        self.assertEqual(painel.edit_row("compromissos", row["id"], "texto", "banco às 16h"), 1)
        for table, field in (("compromissos", "id"), ("memorias", "texto"), ("x; DROP TABLE turnos", "a")):
            with self.assertRaises(ValueError):
                painel.edit_row(table, 1, field, "x")
        with self.assertRaises(ValueError):
            painel.delete_row("turnos", 1)


if __name__ == "__main__":
    unittest.main()
