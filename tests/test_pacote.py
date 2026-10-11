"""O pacote instalado: todo arquivo não-.py que ele lê vai junto (o package-data) e todo subpacote está no packages."""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PACOTE = "simples_nacional"


@unittest.skipIf(sys.version_info < (3, 11), "tomllib entra no 3.11; o CI roda também nas novas")
class TestEmpacotamento(unittest.TestCase):

    def test_dados_do_pacote_no_package_data(self):
        # o .tsv da 1.3.0 passava no checkout e sumia no pip install, sem aviso
        import tomllib
        cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
        dados = cfg.get("tool", {}).get("setuptools", {}).get("package-data", {})
        padroes = dados.get(PACOTE, []) + dados.get("*", [])
        pasta = RAIZ / PACOTE
        # glob do Path, como o setuptools: o fnmatch deixava "*.tsv" valer em subpasta
        cobertos = {p for g in padroes for p in pasta.glob(g)}
        fora = [p.relative_to(pasta).as_posix() for p in sorted(pasta.rglob("*"))
                if p.is_file() and p.suffix not in (".py", ".pyc") and "__pycache__" not in p.parts
                and p not in cobertos]
        self.assertEqual(fora, [], "fora do [tool.setuptools.package-data]: não vão na instalação")

    def test_subpacotes_no_packages(self):
        # packages = ["simples_nacional"] não leva subpasta com .py: o import quebra só depois do pip install
        import tomllib
        cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
        pacotes = cfg.get("tool", {}).get("setuptools", {}).get("packages", [])
        if not isinstance(pacotes, list):
            return  # packages.find acha os subpacotes sozinho
        pasta = RAIZ / PACOTE
        subs = sorted({".".join((PACOTE,) + p.parent.relative_to(pasta).parts)
                       for p in pasta.rglob("*.py") if "__pycache__" not in p.parts})
        self.assertEqual([s for s in subs if s not in pacotes], [],
                         "fora do packages do [tool.setuptools]: não vão na instalação")


if __name__ == "__main__":
    unittest.main()
