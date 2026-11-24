"""Fase 6, item 46: as ferramentas que o modelo vê estão bem descritas."""
import unittest
import unittest.mock

import tests.test_regressao  # noqa: F401
from brain import tools


class SchemaTest(unittest.TestCase):
    def test_esquemas_validos(self):
        names = set()
        for schema in tools.schemas():
            fn = schema["function"]
            self.assertEqual(schema["type"], "function")
            self.assertNotIn(fn["name"], names, "nome repetido")
            names.add(fn["name"])
            self.assertTrue(fn["description"].strip(), fn["name"])
            params = fn["parameters"]
            self.assertEqual(params["type"], "object")
            for req in params.get("required", []):
                self.assertIn(req, params["properties"], f"{fn['name']}: {req}")
            for prop in params["properties"].values():
                self.assertIn(prop["type"], ("string", "integer", "number", "boolean", "array", "object"))
        for needed in ("criar_imagem", "consultar_documentos", "memorizar", "abrir_fonte", "buscar_na_internet"):
            self.assertIn(needed, names)

    def test_ferramenta_desconhecida_nao_quebra(self):
        text, _ = tools.run_tool("nao_existe", {})
        self.assertIn("desconhecida", text)

    def test_argumentos_estranhos_sao_ignorados(self):
        with unittest.mock.patch.object(tools, "_say"):
            text, _ = tools.run_tool("data_e_hora", '{"lixo": 1}')
        self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
