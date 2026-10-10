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
        tags = re.findall(r"simples-nacional-br@v([\d.]+)", README.read_text(encoding="utf-8"))
        self.assertEqual(tags, [__version__])


if __name__ == "__main__":
    unittest.main()
