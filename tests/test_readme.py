"""Os exemplos em Python do README rodam como estão, cada bloco sozinho."""

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
            with self.subTest(bloco=i):
                exec(compile(bloco, f"README, bloco {i}", "exec"), {})


if __name__ == "__main__":
    unittest.main()
