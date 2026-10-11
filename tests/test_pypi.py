"""O que o PyPI publica: o README instala pelo nome do pyproject, e cada
comando que o pip cria aponta para uma função que existe."""

import contextlib
import importlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

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

    def test_descricao_igual_a_do_catalogo_mcp(self):
        # PyPI, catálogo MCP e GitHub mostram a mesma frase; até a 1.5.0, eram três
        spec = importlib.util.spec_from_file_location("montar_mcpb", RAIZ / "mcpb" / "montar.py")
        montar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(montar)
        self.assertEqual(self.projeto["description"], montar.DESCRICAO)


class TestAjudaDoComandoInstalado(unittest.TestCase):

    def test_ajuda_mostra_o_nome_digitado(self):
        # na 1.5.0, quem digitava simples-nacional --help lia "python -m ..."
        for nome, modulo in [("simples-nacional", "simples_nacional.__main__"),
                             ("simples-nacional-cnae", "simples_nacional.cnae")]:
            for argv0, prog in [(f"/venv/bin/{nome}", nome),
                                (f"C:/venv/Scripts/{nome}.exe", nome),
                                (f"/src/{modulo.replace('.', '/')}.py",
                                 "python -m " + modulo.replace(".__main__", ""))]:
                with self.subTest(argv0=argv0):
                    saida = io.StringIO()
                    with mock.patch.object(sys, "argv", [argv0]), \
                            contextlib.redirect_stdout(saida), self.assertRaises(SystemExit):
                        importlib.import_module(modulo).main(["--help"])
                    self.assertTrue(saida.getvalue().startswith(f"usage: {prog} "))


if __name__ == "__main__":
    unittest.main()
