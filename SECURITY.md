# Segurança

## Como avisar

Falha de segurança não vai em issue pública: use o aviso privado do GitHub,
em [Security → Report a vulnerability](https://github.com/peterwkdev-creator/simples-nacional-br/security/advisories/new).
Diga a versão, o passo a passo para reproduzir e o efeito.

## O que esperar

- Primeira resposta em até 14 dias.
- A correção sai na última versão publicada; versões antigas não recebem
  correção.
- Crédito no [CHANGELOG.md](CHANGELOG.md) e no aviso, se você quiser.

## O que não é falha de segurança

Resultado diferente do esperado (um valor, uma regra, um caso que falta) é
issue comum, pelo modelo "Valor diferente do esperado".

## O que a biblioteca faz e não faz

- Só conta: não acessa a rede, não grava arquivo e não tem dependência fora
  da biblioteca padrão do Python. O único arquivo que lê é a lista da CNAE
  que vem dentro do pacote.
- O servidor MCP conversa só pela entrada e saída padrão do processo que o
  abriu; não abre porta nem conexão.
- A página "Experimente" roda a biblioteca no seu navegador (Pyodide):
  nenhum número digitado sai do seu computador.

## Como conferir o pacote do PyPI

Cada versão vai ao PyPI só pelo `.github/workflows/pypi.yml` deste
repositório, por publicação confiável (sem senha nem token guardado), e
depois da aprovação do dono. Cada arquivo publicado leva um atestado de
procedência (PEP 740) que o liga a este repositório e a esse workflow: no
PyPI, em "Download files", nos detalhes de cada arquivo, em "Provenance".
