#!/usr/bin/env bash
# Monta o sdist e o wheel em dist/ e roda o que o pip instala, num venv e
# fora do checkout (de dentro dele, o import pegaria a cópia local). Roda no
# testes.yml a cada push e no pypi.yml antes de publicar. A conta e a CNAE
# conferem um valor do README; a CNAE lê o cnae_subclasses.tsv, que só vai
# no wheel pelo package-data.
set -euo pipefail
python -m pip install --quiet "build==1.6.1"
python -m build
venv="$RUNNER_TEMP/instalado"
python -m venv "$venv"
"$venv/bin/pip" install --quiet dist/*.whl
cd "$RUNNER_TEMP"
"$venv/bin/simples-nacional" --version
"$venv/bin/simples-nacional" --ano 2026 --anexo I --rbt12 4500000 --receita-mes 375000 \
  | grep -F "Valor do mês: R\$ 39.750,00"
"$venv/bin/simples-nacional-cnae" 6920-6/01 --ano 2027 | grep -F "ATIVIDADES DE CONTABILIDADE"
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"ci","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | "$venv/bin/simples-nacional-mcp" | grep -c '"name": "enquadrar_cnae"'
