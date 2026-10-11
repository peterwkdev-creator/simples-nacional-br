# Histórico de versões

Todas as datas são de 2026. A versão segue `simples_nacional.__version__`;
cada uma tem uma tag `vX.Y.Z` no commit que a publicou.

## 1.5.2 — 11/10

- Linha de comando em português: `--help` com "uso:", "opções:" e "mostra
  esta ajuda e sai", e os erros de digitação ("faltam argumentos
  obrigatórios", "valor inválido", "opção inválida"...) no lugar do inglês
  do argparse. Módulo novo, `simples_nacional.argumentos`, para quem monta
  um comando em cima da biblioteca; o argparse de quem importa não muda.
- `simples-nacional --rbt12 0` explica que o RBT12 tem de ser maior que
  zero e indica `--receitas` para o início de atividade (antes citava uma
  função da API, que quem usa o comando não tem).
- `simples_nacional.cnae.main(prog=...)`: quem reexporta o comando mostra o
  próprio nome na ajuda.

## 1.5.1 — 11/10

- Página do PyPI: o GIF e os links do README apontam para o GitHub (na
  1.5.0, relativos, não abriam lá); um teste barra link relativo.
- `--help` dos comandos instalados mostra o nome digitado
  (`simples-nacional`, `simples-nacional-cnae`), não `python -m ...`.
- README: "Instalar" com a primeira conta e a saída que ela dá (testada) e
  a tabela dos três comandos; "Servidor MCP" com três jeitos de ligar, do
  mais simples ao mais manual (pacote MCPB, uv, pip).
- PyPI, GitHub e catálogo MCP com a mesma descrição (um teste confere) e
  as mesmas palavras-chave; no PyPI, "Homepage" abre a vitrine e
  "Source", o repositório, como no GitHub.
- `SECURITY.md`: como avisar uma falha pelo aviso privado do GitHub, o que
  a biblioteca faz e não faz (sem rede, sem gravar arquivo) e como conferir
  o atestado de procedência do pacote no PyPI.
- Workflows: toda action fixada pelo SHA do commit, como já era no da
  publicação no PyPI (uma tag movida não muda o que roda aqui).

## 1.5.0 — 11/10

- PyPI: `pip install simples-nacional-br` (o nome do pacote passa de
  `simples-nacional` a `simples-nacional-br`, o do repositório; o `import
  simples_nacional` não muda). Publicado a cada Release pela publicação
  confiável, sem token.
- Três comandos na instalação: `simples-nacional`, `simples-nacional-cnae`
  e `simples-nacional-mcp`; com o uv, `uvx --from simples-nacional-br
  simples-nacional-mcp` roda o servidor MCP sem instalar antes.
- CI: a cada push, monta o wheel e roda os três comandos num venv, fora do
  checkout, e confere a descrição com `twine check --strict`.

## 1.4.3 — 10/10

- Fontes: limite, sublimite, Fator R e a 6ª faixa de 2027 e 2028 com a URL
  e a data de consulta (texto atualizado da Câmara, 10/10/2026).
- Um lugar só: `ICMS_ISS_POR_FAIXA` e `quinta_faixa_icms_iss_ibs` passam a
  ler a repartição de `tabelas_reparticao.py`, em vez de repetir os
  números; valores e API iguais. Os testes seguem com os números da lei à
  parte, e trocar um deles na repartição derruba teste.
- Testes: o texto da conta à mão de cada faixa é conferido contra a linha
  (um erro de digitação nele derruba o teste).
- Vitrine: "Usar o exemplo" com os mesmos valores não esconde mais o
  resultado.
- Pacote MCPB: os arquivos entram no zip pela ordem do texto do nome (o
  Windows ordena sem caixa); o hash de hoje não muda.
- Testes: o package-data e o `packages` do `pyproject.toml` conferidos em
  toda subpasta do pacote (antes, só o primeiro nível); a tag do README
  aceita ponto final e repetição, e exige pelo menos uma.
- Limpeza: saem `calculo._decimal` e `__main__._porcentagem`, nomes
  privados da 0.3.0 (fora da API pública; use `para_decimal` e
  `porcentagem`); `.venv/` e `*.mcpb` no `.gitignore`.

## 1.4.2 — 10/10

- Servidor MCP: valor acima de R$ 1 trilhão (inclusive `1E+999999999`, que é
  JSON válido) e RBT12 zero ou negativo voltam como erro da ferramenta, com
  o nome do argumento, em vez de erro interno; mensagens de erro do
  protocolo em português.
- Pacote MCPB: o mesmo hash no Windows e no Linux (`create_system` fixo).
- Workflows: testes e montagem só com leitura; escrita e OIDC só no job que
  publica; checkout sem guardar a credencial; o `mcp-publisher` baixado é
  conferido pelo sha256.
- Vitrine: `index.html`, `montar.py` e `test_vitrine.py` do modelo atual.

## 1.4.1 — 10/10

- Novo: o servidor MCP também como pacote MCPB, anexado a cada Release
  (`simples-nacional-br-<versão>.mcpb`), e publicado no catálogo oficial de
  servidores MCP como `io.github.peterwkdev-creator/simples-nacional-br`.
  O código da biblioteca não muda.
- `mcpb/montar.py` monta o pacote, reprodutível, só com a biblioteca padrão.
  Um teste roda o servidor de dentro do zip, pelo comando do manifest, fora
  do checkout. O workflow `catalogo-mcp.yml` anexa o pacote, confere o hash
  do que o GitHub serve e publica.

## 1.4.0 — 10/10

- Novo: servidor MCP (Model Context Protocol), `python -m
  simples_nacional.mcp`, por stdio e só com a biblioteca padrão. Quatro
  ferramentas, todas cálculo puro e com `ano` obrigatório: `calcular_das`,
  `repartir_das`, `planejar_fator_r` e `enquadrar_cnae`.
- Atende a forma com `initialize` (revisões 2025-06-18 e 2025-11-25) e a
  sem estado, com `server/discover` (2026-07-28), no mesmo processo.
  Especificação consultada em 10/10/2026.
- Valores como número JSON ou texto no formato brasileiro, lidos em
  `Decimal`; a resposta traz texto e `structuredContent`, com o aviso de
  estimativa. Entrada errada e RBT12 acima do limite voltam como erro da
  ferramenta (`isError`).
- README: como ligar no Claude Code e no Claude Desktop.
- Sem quebra: nada da 1.3.0 mudou.

## 1.3.0 — 10/10

- Novo: enquadramento CNAE → anexo, no módulo `simples_nacional.cnae`.
  `enquadrar(cnae, *, ano, folha12=None, rbt12=None)` devolve um
  `Enquadramento` com a situação (impeditiva, ambígua, anexo, Fator R ou
  sem classificação), o anexo, o fundamento legal e uma observação; com a
  folha e o RBT12, resolve o Fator R.
- Fontes: Res. CGSN 140/2018, art. 8º e Anexos VI e VII (conferidos em
  10/10/2026 no portal de normas da Receita, sem mudança até a Res. CGSN
  191); LC 123, art. 18; nomes das 1.332 subclasses da CNAE 2.3 (IBGE).
- A indústria vai ao Anexo II até 2026 e ao Anexo I de 2027 em diante (LC
  214/2025, art. 517), com o aviso de que o II fica para o produto da Zona
  Franca de Manaus.
- A ligação da subclasse ao anexo é leitura da biblioteca, não tabela
  oficial; a saída diz isso.
- Linha de comando: `python -m simples_nacional.cnae 6920-6/01 --ano 2026`,
  com `--folha12` e `--rbt12` para o Fator R.
- O pacote instalado leva `cnae_subclasses.tsv` (`package-data`).
- Sem quebra: nada da 1.2.0 mudou.

## 1.2.0 — 10/10

- Novo: planejamento do Fator R. `planejar_fator_r(folha12, rbt12,
  receita_mes, *, ano, icms_iss_no_das=False)` devolve um `PlanoFatorR`
  com o Fator R, o anexo de hoje, a folha de 12 meses que leva a 28%
  (arredondada para cima no centavo), quanto falta e o valor do mês no
  Anexo V e no III, com a diferença.
- A diferença é só no DAS: a contribuição previdenciária e o IRPF do
  pró-labore a mais não estão descontados.
- Linha de comando: `--anexo fator-r` mostra o planejamento (fora do mês
  do art. 24, `--receita-ano`).
- Sem quebra: nada da 1.1.0 mudou.

## 1.1.0 — 10/10

- Novo: repartição do DAS por tributo. `parcelas_das(anexo, rbt12,
  receita_mes, *, ano)` dá o valor de cada tributo em centavos, somando o
  `valor_devido`; `aliquotas_por_tributo(anexo, rbt12, *, ano)` dá a fração
  da receita de cada um, sem arredondar.
- Tabelas de repartição de cada período em `tabelas_reparticao.py`, com a
  fonte: 2018 a 2026 (LC 123, redação da LC 155/2016), 2027 e 2028, 2029,
  2030, 2031, 2032 e de 2033 em diante (LC 214/2025, Anexos XVIII a XXII),
  com o teto do ISS da 5ª faixa dos Anexos III e IV.
- Testes por faixa de cada anexo e período, e de coerência com
  `ICMS_ISS_POR_FAIXA` e `quinta_faixa_icms_iss_ibs`.
- Sem quebra: nada da 1.0.0 mudou.

## 1.0.0 — 10/10

- API estável: o que está em `simples_nacional.__all__` só muda de forma
  incompatível numa versão maior (seção "Compatibilidade" do README).
- Quebra: `avisos` pede `ano=`, como os cálculos desde a 0.2.0. Sem ele, o
  texto do sublimite saía o de até 2026 mesmo numa conta de 2027 ou depois.
- Quebra: `quinta_faixa_icms_iss_ibs(anexo, *, ano)`: `ano` só por nome e
  conferido como nos cálculos (antes de 2018, ou que não seja `int`, dá
  erro); anexo em minúscula aceito; anexo inválido dá `ValueError` em
  português.
- Quebra: sai `ICMS_ISS_QUINTA_FAIXA`, que repetia
  `ICMS_ISS_POR_FAIXA[anexo][4]`; use esse ou
  `quinta_faixa_icms_iss_ibs(anexo, ano=2026)[0]`.
- README reordenado (instalar, uso curto, fontes no fim), CONTRIBUTING,
  código de conduta e modelo de issue "Valor diferente do esperado".

## 0.6.0 — 10/10

- `icms_iss_no_das=True` vale também de 2027 em diante: soma à 6ª faixa,
  só federal, ICMS ou ISS e IBS pela 5ª faixa, com a repartição de cada
  período na LC 214/2025, Anexos XVIII a XXII (2027-2028, 2029, 2030, 2031,
  2032); de 2033 em diante, só o IBS (Res. CGSN 140, art. 21, IV, redação
  da Res. CGSN 190/2026). Antes dava erro.
- `valor_devido_acima_do_sublimite` e, na linha de comando, `--receita-ano`
  (até 2026): o mês em que a receita do ano passa do sublimite, dividido em
  parcelas dentro do sublimite, entre ele e R$ 4,8 milhões e acima disso
  (Res. CGSN 140, art. 24), com o aviso de quando o impedimento e a exclusão
  valem. De 2027 em diante dá erro.
- Novos na API: `ICMS_ISS_POR_FAIXA` (repartição do ICMS ou ISS da 1ª à 5ª
  faixa até 2026), `TETO_ISS` e `quinta_faixa_icms_iss_ibs(anexo, ano)`.
- Avisos do sublimite de 2027 em diante citam a opção e a regra nova.

## 0.5.0 — 09/10

- `icms_iss_no_das=True` (na linha de comando, `--icms-iss-no-das`): com
  RBT12 acima de R$ 3,6 milhões e a receita do ano dentro do sublimite, soma
  à 6ª faixa o ICMS ou ISS pela 5ª faixa (Res. CGSN 140, art. 21, III, b),
  até 2026.

## 0.4.0 — 09/10

- `avisos_inicio_atividade` e `--mes-inicio`: limite e sublimite
  proporcionais no ano de início de atividade (LC 123, art. 3º, §§ 2º e 10
  a 13).
- Contas num contexto `Decimal` fixo: o `getcontext()` de quem chama não
  muda o resultado.
- `ler_numero` aceita `R$` na frente; `avisos(0)` é `ValueError`;
  `--version`. Na linha de comando, a conta do valor do mês fecha no
  centavo e o Fator R é cortado na 4ª casa.

## 0.3.3 — 09/10

- O aviso do sublimite passa a dizer que quem decide se ICMS e ISS saem do
  DAS é a receita acumulada no ano, não o RBT12. `avisos()` ganha `ano`: de
  2027 a 2032 cita também o IBS e, de 2033 em diante, só o IBS.

## 0.3.2 — 09/10

- Exemplos do README rodam como estão e são testados.
- `ler_numero("0.500")` é recusado; tipos errados dão erro em PT-BR.
- `--folha12` sem `--anexo fator-r` é erro de uso.
- Metadados do pacote (licença MIT, autor, links).

## 0.3.1 — 09/10

- `ler_numero`, `para_decimal`, `porcentagem` e `reais` públicos, no módulo
  `formato`. Os nomes antigos seguem valendo.

## 0.3.0 — 09/10

- `aliquota_inicio_atividade` e `valor_devido_inicio_atividade` (Res. CGSN
  140, art. 22), com a regra de 2027 da Res. CGSN 190/2026.
- Na linha de comando, `--receitas`; `150.000` é milhar e `1,000.50` dá
  erro.

## 0.2.0 — 09/10

- Tabela do ano de apuração: em 2027 e 2028, a 6ª faixa tem nominal 0,1
  ponto menor (LC 214/2025, art. 519).
- Quebra de API: `faixa`, `aliquota_efetiva` e `valor_devido` pedem `ano=`.
  A linha de comando ganha `--ano`.

## 0.1.0 — 09/10

- Alíquota efetiva, valor do mês e Fator R pelos Anexos I a V da LC 123/2006
  (redação da LC 155/2016), com o teto de R$ 4,8 milhões como erro e o
  sublimite de R$ 3,6 milhões como aviso. Linha de comando em
  `python -m simples_nacional`. Documentação e mensagens em português.
