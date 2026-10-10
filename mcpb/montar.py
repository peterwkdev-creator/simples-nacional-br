"""Monta o pacote MCPB do servidor MCP e o server.json do catálogo oficial de
servidores MCP, só com a biblioteca padrão.

    python mcpb/montar.py --saida dist

Gera `dist/simples-nacional-br-<versão>.mcpb` (zip com o manifest.json, o
servidor e a biblioteca) e `dist/server.json`. O zip é reprodutível (datas e
ordem fixas): os mesmos arquivos dão o mesmo fileSha256.

Formatos consultados em 10/10/2026: manifest MCPB 0.3
(https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md) e
server.json 2025-12-11 (https://github.com/modelcontextprotocol/registry,
docs/modelcontextprotocol-io/package-types.mdx).
"""

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

BIBLIOTECA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIBLIOTECA))

from simples_nacional import __version__  # noqa: E402
from simples_nacional.mcp import FERRAMENTAS  # noqa: E402

REPOSITORIO = "https://github.com/peterwkdev-creator/simples-nacional-br"
VITRINE = "https://peterwkdev-creator.github.io/simples-nacional-br/"
NOME = "io.github.peterwkdev-creator/simples-nacional-br"
# o catálogo aceita até 100 caracteres
DESCRICAO = ("Simples Nacional pela LC 123: alíquota efetiva, DAS, repartição por tributo, "
             "Fator R e CNAE")
ESQUEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
DATA_FIXA = (2026, 1, 1, 0, 0, 0)


def nome_do_arquivo(versao=__version__):
    return f"simples-nacional-br-{versao}.mcpb"


def endereco(versao=__version__):
    """Onde o workflow da Release anexa o pacote."""
    return f"{REPOSITORIO}/releases/download/v{versao}/{nome_do_arquivo(versao)}"


def manifesto(versao=__version__):
    return {
        "manifest_version": "0.3",
        "name": "simples-nacional-br",
        "display_name": "Simples Nacional",
        "version": versao,
        "description": DESCRICAO,
        "author": {"name": "Peter", "url": "https://github.com/peterwkdev-creator"},
        "repository": {"type": "git", "url": REPOSITORIO},
        "homepage": VITRINE,
        "documentation": f"{REPOSITORIO}#servidor-mcp",
        "support": f"{REPOSITORIO}/issues",
        "license": "MIT",
        "keywords": ["simples nacional", "das", "fator r", "lc 123", "contabilidade"],
        "server": {
            "type": "python",
            "entry_point": "server/main.py",
            # no macOS e no Linux o Python 3 costuma ser só python3; no Windows, python
            "mcp_config": {
                "command": "python3",
                "args": ["${__dirname}/server/main.py"],
                "platform_overrides": {"win32": {"command": "python",
                                                 "args": ["${__dirname}/server/main.py"]}},
            },
        },
        "tools": [{"name": f["name"], "description": f["description"]} for f in FERRAMENTAS],
        "compatibility": {"platforms": ["darwin", "win32", "linux"],
                          "runtimes": {"python": ">=3.9"}},
    }


def arquivos():
    """(caminho no zip, bytes), em ordem fixa."""
    itens = [
        ("manifest.json",
         (json.dumps(manifesto(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
        ("LICENSE", (BIBLIOTECA / "LICENSE").read_bytes()),
        ("server/main.py", (BIBLIOTECA / "mcpb" / "main.py").read_bytes()),
    ]
    for p in sorted((BIBLIOTECA / "simples_nacional").iterdir()):
        if p.suffix in (".py", ".tsv"):
            itens.append((f"server/lib/simples_nacional/{p.name}", p.read_bytes()))
    return itens


def montar_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for caminho, dados in arquivos():
            info = zipfile.ZipInfo(caminho, DATA_FIXA)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, dados)
    return buf.getvalue()


def server_json(sha256, versao=__version__):
    return {
        "$schema": ESQUEMA,
        "name": NOME,
        "description": DESCRICAO,
        "repository": {"url": REPOSITORIO, "source": "github"},
        "version": versao,
        "packages": [{
            "registryType": "mcpb",
            "identifier": endereco(versao),
            "fileSha256": sha256,
            "transport": {"type": "stdio"},
        }],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Monta o pacote MCPB e o server.json.")
    p.add_argument("--saida", required=True, type=Path, help="pasta de saída")
    a = p.parse_args(argv)
    a.saida.mkdir(parents=True, exist_ok=True)
    dados = montar_zip()
    sha = hashlib.sha256(dados).hexdigest()
    (a.saida / nome_do_arquivo()).write_bytes(dados)
    (a.saida / "server.json").write_text(
        json.dumps(server_json(sha), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{nome_do_arquivo()}: {len(dados)} bytes, sha256 {sha}")


if __name__ == "__main__":
    main()
