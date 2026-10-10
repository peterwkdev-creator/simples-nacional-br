"""Pacote MCPB e server.json do catálogo: o zip montado roda sozinho, pelo
comando do manifest, fora do checkout e sem PYTHONPATH.

Formatos consultados em 10/10/2026 (fontes em mcpb/montar.py).
"""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from simples_nacional import __version__
from simples_nacional.mcp import FERRAMENTAS

BIBLIOTECA = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("montar_mcpb", BIBLIOTECA / "mcpb" / "montar.py")
montar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(montar)


class TestPacote(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        cls.saida = Path(cls.pasta.name)
        r = subprocess.run([sys.executable, str(BIBLIOTECA / "mcpb" / "montar.py"),
                            "--saida", str(cls.saida)], capture_output=True, timeout=60)
        assert r.returncode == 0, r.stderr
        cls.mcpb = cls.saida / f"simples-nacional-br-{__version__}.mcpb"
        cls.dados = cls.mcpb.read_bytes()
        cls.server = json.loads((cls.saida / "server.json").read_text(encoding="utf-8"))
        with zipfile.ZipFile(cls.mcpb) as z:
            cls.nomes = z.namelist()
            cls.datas = {i.date_time for i in z.infolist()}
            cls.manifest = json.loads(z.read("manifest.json"))

    @classmethod
    def tearDownClass(cls):
        cls.pasta.cleanup()

    def test_conteudo_do_zip(self):
        self.assertEqual(self.nomes[0], "manifest.json")
        for nome in ("LICENSE", "server/main.py", "server/lib/simples_nacional/mcp.py",
                     "server/lib/simples_nacional/cnae_subclasses.tsv"):
            self.assertIn(nome, self.nomes)
        self.assertFalse([n for n in self.nomes if "__pycache__" in n or n.endswith(".pyc")])
        modulos = sorted(p.name for p in (BIBLIOTECA / "simples_nacional").glob("*.py"))
        self.assertEqual(sorted(n.rsplit("/", 1)[1] for n in self.nomes
                                if n.startswith("server/lib/") and n.endswith(".py")), modulos)

    def test_manifest(self):
        m = self.manifest
        for campo in ("manifest_version", "name", "version", "description", "author", "server"):
            self.assertIn(campo, m)
        self.assertEqual(m["manifest_version"], "0.3")
        self.assertEqual(m["version"], __version__)
        self.assertEqual(m["license"], "MIT")
        self.assertEqual(m["server"]["type"], "python")
        self.assertIn(m["server"]["entry_point"], self.nomes)
        self.assertEqual([t["name"] for t in m["tools"]], [f["name"] for f in FERRAMENTAS])
        self.assertEqual(m["compatibility"]["runtimes"]["python"], ">=3.9")

    def test_server_json(self):
        s = self.server
        self.assertEqual(s["name"], "io.github.peterwkdev-creator/simples-nacional-br")
        self.assertEqual(s["version"], __version__)
        self.assertTrue(1 <= len(s["description"]) <= 100, len(s["description"]))
        self.assertEqual(s["description"], self.manifest["description"])
        (pacote,) = s["packages"]
        self.assertEqual(pacote["registryType"], "mcpb")
        self.assertEqual(pacote["transport"], {"type": "stdio"})
        # o catálogo só aceita Release do GitHub, https, com "mcp" no endereço
        self.assertRegex(pacote["identifier"], r"^https://github\.com/peterwkdev-creator/"
                         r"simples-nacional-br/releases/download/v" + re.escape(__version__)
                         + "/" + re.escape(self.mcpb.name) + "$")
        self.assertIn("mcp", pacote["identifier"])
        self.assertRegex(pacote["fileSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(pacote["fileSha256"], hashlib.sha256(self.dados).hexdigest())

    def test_reprodutivel(self):
        # data fixa em cada entrada: duas montagens no mesmo segundo não provam isso
        self.assertEqual(self.datas, {montar.DATA_FIXA})
        self.assertEqual(montar.montar_zip(), self.dados)

    def test_roda_pelo_comando_do_manifest(self):
        """Como o cliente: extrai, troca ${__dirname} e roda de outra pasta."""
        with tempfile.TemporaryDirectory() as extraido, tempfile.TemporaryDirectory() as fora:
            with zipfile.ZipFile(self.mcpb) as z:
                z.extractall(extraido)
            config = self.manifest["server"]["mcp_config"]
            if sys.platform == "win32":
                config = {**config, **config["platform_overrides"]["win32"]}
            self.assertIn(config["command"], ("python", "python3"))
            args = [a.replace("${__dirname}", extraido) for a in config["args"]]
            pedidos = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                    "protocolVersion": "2025-11-25", "capabilities": {},
                    "clientInfo": {"name": "teste", "version": "0"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                    "name": "calcular_das", "arguments": {
                        "anexo": "III", "rbt12": "3.000.000", "receita_mes": 100000,
                        "ano": 2026}}},
            ]
            entrada = "".join(json.dumps(p) + "\n" for p in pedidos).encode("utf-8")
            env = {k: v for k, v in os.environ.items()
                   if k not in ("PYTHONPATH", "PYTHONIOENCODING")}
            # sys.executable no lugar de "python": o mesmo Python que roda o teste
            r = subprocess.run([sys.executable] + args, cwd=fora, input=entrada,
                               capture_output=True, env=env, timeout=60)
        self.assertEqual((r.returncode, r.stderr), (0, b""))
        saida = [json.loads(linha) for linha in r.stdout.decode("utf-8").splitlines()]
        self.assertEqual([m["id"] for m in saida], [1, 2, 3])
        self.assertEqual(saida[0]["result"]["serverInfo"]["version"], __version__)
        self.assertEqual([t["name"] for t in saida[1]["result"]["tools"]],
                         [f["name"] for f in FERRAMENTAS])
        self.assertEqual(saida[2]["result"]["structuredContent"]["valor_do_mes"], "16812.00")


if __name__ == "__main__":
    unittest.main()
