"""Fase 7: curiosidade, estudo autônomo, reflexão e rotina de fundo."""
import time
import unittest
from datetime import datetime
from unittest import mock

import numpy as np

import tests.test_regressao  # noqa: F401
from tests.test_persona import _clean
from brain import semantic_memory
from brain.persona import curiosidade, estudo, perfil, reflexao, rotina
from brain.persona.store import connect
from core import config


class CuriosidadeTest(unittest.TestCase):
    def setUp(self):
        _clean()
        with connect() as conn:
            conn.execute("DELETE FROM curiosidades")

    def test_fila_sem_repetir_e_pedido_tem_prioridade(self):
        self.assertTrue(curiosidade.add("Patch notes do Aion 2", "Pedro joga", "conversa"))
        self.assertFalse(curiosidade.add("patch notes do aion 2."))
        self.assertFalse(curiosidade.add("x"))
        curiosidade.add("ComfyUI LoRA", "pedido", "pedro", priority=5)
        self.assertEqual(curiosidade.next_theme()[1], "comfyui lora")

    def test_conversa_anota_temas(self):
        perfil.record_turn("quero entender LoRA no FLUX", "Posso estudar isso.")
        answer = {"fatos": [], "temas": [{"tema": "LoRA no FLUX.2", "motivo": "Pedro perguntou"}]}
        with mock.patch.object(perfil.llm, "ask", return_value=answer):
            perfil.process_pending()
        self.assertEqual(curiosidade.pending(), ["lora no flux.2"])

    def test_lista_vazia_pede_temas_dos_interesses(self):
        with mock.patch.object(semantic_memory, "embed", return_value=None):
            semantic_memory.add("preferência", "Pedro joga Aion 2.", "conversa", "perfil")
        with mock.patch.object(curiosidade.llm, "ask",
                               return_value={"temas": [{"tema": "builds de Ranger Aion 2", "motivo": "joga"}]}) as ask:
            self.assertEqual(curiosidade.refill(), 1)
        self.assertIn("Pedro joga Aion 2.", ask.call_args.args[1])


class EstudoTest(unittest.TestCase):
    def setUp(self):
        _clean()
        with connect() as conn:
            conn.execute("DELETE FROM curiosidades")
        curiosidade.add("tempo de vida do lobo cinzento")

    def test_estuda_guarda_e_rebaixa_confianca_sem_duas_fontes(self):
        summary = "O lobo cinzento vive de 6 a 8 anos na natureza e até 16 em cativeiro, segundo as fontes."
        with mock.patch.object(estudo, "_search", return_value=("texto das páginas", "Wikipedia\nNatgeo")), \
             mock.patch.object(estudo.llm, "ask", return_value={"resumo": summary, "confianca": "alta",
                                                                 "fontes_que_concordam": ["Wikipedia"]}), \
             mock.patch.object(estudo, "_log"), \
             mock.patch.object(semantic_memory, "embed", return_value=None):
            self.assertEqual(estudo.study_one(), "tempo de vida do lobo cinzento")
            found = semantic_memory.search("lobo cinzento vive", tipos=("aprendido",))
        self.assertIn("confiança media", found[0]["fonte"])
        self.assertEqual(curiosidade.pending(), [])

    def test_busca_vazia_descarta(self):
        with mock.patch.object(estudo, "_search", return_value=("Nenhum resultado.", "internet")), \
             mock.patch.object(estudo.llm, "ask") as ask:
            self.assertIsNone(estudo.study_one())
        ask.assert_not_called()

    def test_busca_do_estudo_nao_troca_as_fontes_do_pedro(self):
        from brain.websearch import websearch

        websearch.LAST_SOURCES[:] = [{"url": "https://pedro.example", "site": "x", "title": ""}]
        fake = mock.Mock()
        fake.json.return_value = {"web": {"results": [
            {"url": "http://192.168.0.1/admin", "title": "roteador"},
            {"url": "https://pt.wikipedia.org/wiki/Lobo", "title": "Lobo", "description": "lobo"}]}}
        with mock.patch.object(websearch, "BRAVE_API_KEY", "k"), \
             mock.patch.object(websearch.requests, "get", return_value=fake), \
             mock.patch.object(websearch, "fetch_multiple_pages", new=mock.AsyncMock(
                 return_value=[("https://pt.wikipedia.org/wiki/Lobo", "texto " * 50)])) as pages:
            estudo._search("lobo")
        self.assertEqual(pages.call_args.args[0], ["https://pt.wikipedia.org/wiki/Lobo"])  # rede local fora
        self.assertEqual(websearch.LAST_SOURCES[0]["url"], "https://pedro.example")


class ReflexaoTest(unittest.TestCase):
    def setUp(self):
        _clean()

    def _add(self, subject, text, vector):
        semantic_memory._connect().close()
        with semantic_memory._connect() as conn:
            conn.execute("INSERT INTO memorias (tipo, assunto, texto, fonte, criado, vetor, modelo) "
                         "VALUES ('aprendido', ?, ?, 'x', ?, ?, ?)",
                         (subject, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                          np.asarray(vector, dtype=np.float32).tobytes(), semantic_memory.EMBEDDING_MODEL))

    def test_junta_repetidas_e_forma_opiniao(self):
        self._add("lobo", "Lobos vivem 6 a 8 anos.", [1, 0, 0])
        self._add("lobo cinzento", "O lobo cinzento vive até 8 anos.", [0.999, 0.04, 0])
        self._add("flux", "FLUX.2 klein gera em 4 passos.", [0, 1, 0])

        def ask(system, user, **kw):
            if system == reflexao.MERGE_SYSTEM:
                return "Lobos cinzentos vivem de 6 a 8 anos na natureza, segundo as anotações juntadas."
            if system == reflexao.OPINION_SYSTEM:
                return {"opinioes": [{"tema": "modelos destilados", "opiniao": "Valem a pena para uso local.",
                                      "motivo": "O FLUX.2 klein é rápido."}]}
            return {"contradiz": False}

        with mock.patch.object(reflexao.llm, "ask", side_effect=ask), \
             mock.patch.object(semantic_memory, "embed", return_value=None):
            merged, contradictions, opinions = reflexao.reflect()
        self.assertEqual((merged, contradictions, opinions), (1, 0, 1))
        with connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM memorias").fetchone()[0], 2)
            self.assertEqual(conn.execute("SELECT tema FROM opinioes").fetchone()[0], "modelos destilados")


class RotinaTest(unittest.TestCase):
    def setUp(self):
        _clean()
        with connect() as conn:
            conn.execute("DELETE FROM rotina")
            conn.execute("DELETE FROM curiosidades")

    def test_so_trabalha_parado(self):
        config.LAST_ACTIVITY = time.monotonic()
        with mock.patch.object(rotina, "pc_idle_seconds", return_value=10**6):
            self.assertFalse(rotina.is_idle())  # Pedro acabou de falar
        config.LAST_ACTIVITY = 0.0
        with mock.patch.object(rotina, "pc_idle_seconds", return_value=5):
            self.assertFalse(rotina.is_idle())  # mexendo no PC
        with mock.patch.object(rotina, "pc_idle_seconds", return_value=10**6):
            self.assertTrue(rotina.is_idle())

    def test_ordem_dos_passos_e_limite_de_estudo(self):
        perfil.record_turn("eu gosto de jazz", "Anotado.")
        with mock.patch("brain.persona.perfil.process_pending", side_effect=lambda: perfil.pending_turns.__call__ and _mark_all()) as p, \
             mock.patch("brain.persona.diario.catch_up", return_value=0), \
             mock.patch("brain.persona.reflexao.reflect") as reflect, \
             mock.patch("brain.persona.estudo.study_one", return_value="jazz") as study, \
             mock.patch.object(rotina, "STUDY_PER_DAY", 2), \
             mock.patch.object(rotina, "reflection_due", return_value=False):
            self.assertEqual(rotina.step(), "perfil")
            self.assertEqual(rotina.step(), "estudo")
            self.assertEqual(rotina.step(), "estudo")
            self.assertIsNone(rotina.step())  # limite do dia
        reflect.assert_not_called()
        self.assertEqual(study.call_count, 2)

    def test_reflexao_uma_vez_por_dia_a_noite(self):
        night = datetime(2026, 11, 24, 23, 0)
        self.assertFalse(rotina.reflection_due(datetime(2026, 11, 24, 15, 0)))
        self.assertTrue(rotina.reflection_due(night))
        rotina._set("reflexao_dia", "2026-11-24")
        self.assertFalse(rotina.reflection_due(night))


def _mark_all():
    with connect() as conn:
        conn.execute("UPDATE turnos SET processado = 1")
    return 0


if __name__ == "__main__":
    unittest.main()
