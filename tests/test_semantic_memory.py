"""Fase 5: memória por semelhança e documentos (embeddings falsos, sem Ollama)."""
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import tests.test_regressao  # noqa: F401 (bibliotecas falsas quando faltam)
from brain import semantic_memory as sm

# Vetores "de significado" de mentira: cada tema é uma direção
_TOPICS = {
    "impressora": 0, "hp": 0, "papel": 0,
    "cachorro": 1, "rex": 1, "ração": 1,
    "senha": 2, "wifi": 2, "roteador": 2,
}


def fake_embed(texts, query=False):
    out = []
    for text in texts:
        v = np.full(4, 0.05, dtype=np.float32)
        for word, axis in _TOPICS.items():
            if word in text.lower():
                v[axis] += 1
        out.append(v / np.linalg.norm(v))
    return np.asarray(out)


class SemanticMemoryTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db = os.path.join(self.dir, "m.db")
        self.patches = [mock.patch.object(sm, "MEMORY_DB", self.db),
                        mock.patch.object(sm, "embed", side_effect=fake_embed)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_acha_por_semelhanca_sem_nome_exato(self):
        sm.add("minha impressora", "É uma HP Laser que só aceita papel A4.")
        sm.add("meu cachorro", "O Rex come ração duas vezes por dia.")
        found = sm.search("qual o modelo da impressora?")
        self.assertEqual(found[0]["assunto"], "minha impressora")
        self.assertEqual(len(found), 1)

    def test_nada_parecido_devolve_vazio(self):
        sm.add("meu cachorro", "O Rex come ração.")
        self.assertEqual(sm.search("senha do wifi"), [])

    def test_esquecer_apaga_o_mais_parecido(self):
        sm.add("wifi", "A senha do roteador é 1234.")
        sm.add("meu cachorro", "O Rex come ração.")
        removed = sm.forget("senha do wifi")
        self.assertIn("1234", removed["texto"])
        self.assertEqual(sm.list_subjects(), ["meu cachorro"])

    def test_sem_embeddings_cai_para_palavras(self):
        with mock.patch.object(sm, "embed", return_value=None):
            sm.add("minha impressora", "HP Laser, papel A4")
            found = sm.search("impressora papel")
        self.assertEqual(found[0]["assunto"], "minha impressora")

    def test_migra_memorias_antigas_uma_vez_e_pula_lixo(self):
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE conhecimento (titulo, conteudo, fonte, data)")
        conn.executemany("INSERT INTO conhecimento VALUES (?,?,?,?)", [
            ("impressora", "A impressora do escritório é uma HP Laser com papel A4.", "Pedro", "2025"),
            ("história", "Não consegui acessar nenhum conteúdo atualizado.", "internet", "2025"),
            ("curto", "oi", "internet", "2025"),
        ])
        conn.commit(); conn.close()
        self.assertEqual(sm.migrate_old_memories(), 1)
        self.assertEqual(sm.migrate_old_memories(), 0)
        self.assertEqual(sm.search("impressora")[0]["tipo"], "fato")

    def test_documentos_indexa_reindexa_e_remove(self):
        docs = os.path.join(self.dir, "docs")
        os.makedirs(docs)
        path = os.path.join(docs, "casa.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("A senha do wifi do roteador da sala é jarvis2026.")
        self.assertEqual(sm.index_documents(docs), 1)
        self.assertEqual(sm.index_documents(docs), 0)  # não mudou
        found = sm.search_documents("qual a senha do wifi?")
        self.assertIn("jarvis2026", found[0]["texto"])
        self.assertEqual(sm.search("senha do wifi"), [])  # documentos não misturam com lembranças
        os.chmod(path, 0o666)
        os.remove(path) if os.access(docs, os.W_OK) else None
        if not os.path.exists(path):
            sm.index_documents(docs)
            self.assertEqual(sm.search_documents("senha do wifi"), [])

    def test_trechos_longos_sao_divididos(self):
        text = ". ".join(f"Frase número {i} sobre o assunto" for i in range(200))
        chunks = list(sm._chunks(text))
        self.assertGreater(len(chunks), 3)
        self.assertTrue(all(len(c) <= 900 for c in chunks))


if __name__ == "__main__":
    unittest.main()
