# Histórico de versões

Todas as datas são de 2026. A versão segue `simples_nacional.__version__`;
cada uma tem uma tag `vX.Y.Z` no commit que a publicou.

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
