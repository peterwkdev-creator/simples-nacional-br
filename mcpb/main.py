"""Entrada do pacote MCPB: a biblioteca vai em lib/, ao lado deste arquivo, e
o servidor roda pelo Python de quem instala (3.9 ou mais novo)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from simples_nacional.mcp import main  # noqa: E402

if __name__ == "__main__":
    main()
