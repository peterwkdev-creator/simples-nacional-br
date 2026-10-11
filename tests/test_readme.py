"""Os exemplos em Python do README rodam como estão, cada bloco sozinho, e a
instalação aponta para a tag da versão atual."""

import contextlib
import io
import re
import unittest
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


class TestExemplosDoReadme(unittest.TestCase):

    def test_blocos_python_rodam(self):
        blocos = re.findall(r"```python\n(.*?)```", README.read_text(encoding="utf-8"), re.S)
        self.assertGreaterEqual(len(blocos), 2)
        for i, bloco in enumerate(blocos, 1):
            # a linha que mostra um erro ("ambíguo: ValueError") fica no comentário
            with self.subTest(bloco=i), contextlib.redirect_stdout(io.StringIO()):
                exec(compile(bloco, f"README, bloco {i}", "exec"), {})

    def test_instalar_pela_tag_da_versao_atual(self):
        # a 1.1.0 e a 1.2.0 saíram com o README ainda em @v1.0.0
        from simples_nacional import __version__
        tags = re.findall(r"simples-nacional-br@v(\d+(?:\.\d+)*)", README.read_text(encoding="utf-8"))
        self.assertTrue(tags, "o README não manda instalar pela tag")
        self.assertEqual(set(tags), {__version__})

    def test_sem_link_relativo(self):
        # o PyPI mostra este README e não acha arquivo do repositório nem
        # âncora de título: na 1.5.0, o GIF e o LICENSE não abriam lá
        relativos = re.findall(r"\]\((?!https?://)([^)]*)\)", README.read_text(encoding="utf-8"))
        self.assertEqual(relativos, [])

    def test_primeira_conta_mostra_a_saida_de_verdade(self):
        from simples_nacional.__main__ import main
        m = re.search(r"```bash\nsimples-nacional (.+?)\n```\n\n```text\n(.*?)```",
                      README.read_text(encoding="utf-8"), re.S)
        self.assertTrue(m, "o README não mostra a primeira conta com a saída")
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            main(m.group(1).split())
        self.assertEqual(saida.getvalue(), m.group(2))


if __name__ == "__main__":
    unittest.main()
