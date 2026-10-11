"""O que o PyPI publica: o README instala pelo nome do pyproject, e cada
comando que o pip cria aponta para uma função que existe."""

import importlib
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


@unittest.skipIf(sys.version_info < (3, 11), "tomllib entra no 3.11; o CI roda também nas novas")
class TestPyPI(unittest.TestCase):

    def setUp(self):
        import tomllib
        self.projeto = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    def test_readme_instala_pelo_nome_do_pyproject(self):
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"pip install {self.projeto['name']}\n", readme)

    def test_comandos_apontam_para_funcoes(self):
        # um alvo errado em [project.scripts] só quebra depois do pip install
        comandos = self.projeto.get("scripts", {})
        self.assertTrue(comandos)
        for nome, alvo in comandos.items():
            with self.subTest(comando=nome):
                modulo, funcao = alvo.split(":")
                self.assertTrue(callable(getattr(importlib.import_module(modulo), funcao)))


if __name__ == "__main__":
    unittest.main()
