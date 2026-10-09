# simples-nacional-br

Alíquota efetiva, valor do mês e Fator R do **Simples Nacional**, conferidos
faixa a faixa contra as tabelas oficiais da Lei Complementar 123/2006
(redação da LC 155/2016) e, para 2027 e 2028, da LC 214/2025. Python puro,
só a biblioteca padrão, `Decimal` do começo ao fim.

```bash
python -m unittest
```

```bash
python -m simples_nacional --ano 2026 --anexo I --rbt12 4500000 --receita-mes 375000
```

Os dois rodam do checkout limpo, sem instalar nada. Testado com Python 3.12.
Sem `--ano`, a linha de comando usa o ano corrente e diz qual tabela usou.

> **É estimativa, não consultoria tributária.** Não substitui o PGDAS-D nem o
> contador. Todos os exemplos usam números inventados.

## Por quê

A alíquota efetiva não é a alíquota impressa no anexo. LC 123, art. 18,
§ 1º-A:

```
alíquota efetiva = (RBT12 × alíquota nominal − parcela a deduzir) / RBT12
```

RBT12 é a receita bruta dos 12 meses anteriores ao período de apuração. Um
comércio com RBT12 de R$ 4.500.000,00 está na 6ª faixa do Anexo I (nominal
19%, parcela a deduzir R$ 378.000,00):

```
(4.500.000 × 19% − 378.000) / 4.500.000 = 477.000 / 4.500.000 = 10,60%
```

Aplicar a nominal de 19% dá R$ 855.000,00 no ano, onde a lei dá
R$ 477.000,00. É o erro relatado em
[mcp-fiscal-brasil#146](https://github.com/DeHor-Labs/mcp-fiscal-brasil/issues/146).

## O que cobre

| | Fonte (LC 123/2006, redação da LC 155/2016) |
|---|---|
| Anexos I a V, seis faixas cada: teto, alíquota nominal, parcela a deduzir | Anexos I a V |
| Alíquota efetiva | art. 18, § 1º-A |
| Valor do mês: receita do mês × alíquota efetiva | art. 18, § 3º |
| Fator R: folha de 12 meses ÷ RBT12; 28% ou mais → Anexo III, senão V | art. 18, §§ 5º-J, 5º-K, 5º-M e 24 |
| Teto de R$ 4,8 milhões: erro explicado, nunca número | art. 3º, II |
| Sublimite de R$ 3,6 milhões (ICMS e ISS fora do DAS): aviso | art. 13-A |
| Início de atividade: receita anualizada | art. 18, § 2º |
| Tabela do ano de apuração: em 2027 e 2028 a 6ª faixa tem nominal 0,1 ponto menor; a partir de 2029 volta a de hoje | LC 214/2025, art. 519 e Anexos XVIII a XXII |

Cada valor de tabela foi lido no site da Câmara dos Deputados em 09/10/2026
([LC 155/2016, texto atualizado](https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html));
a fonte fica ao lado da tabela em `simples_nacional/tabelas.py`. A tabela de
2027 e 2028 foi lida no mesmo dia no
[texto atualizado da LC 214/2025](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html).

A partir de 2027, o valor do mês é o DAS cheio, já com as parcelas de CBS e
IBS. Quem optar por pagar esses dois tributos pelo regime regular (LC 123,
art. 13, § 9º) os recolhe fora, e o DAS fica menor: esse cálculo não está
aqui.

Fora do escopo: enquadramento CNAE → anexo, repartição do valor por tributo,
sublimites estaduais, o ano em que o sublimite é ultrapassado (art. 3º,
§§ 11 a 15), o primeiro mês de atividade (regido por resolução do CGSN) e o
MEI.

## Como é testado

- Um caso por faixa de cada anexo (30), com a conta à mão escrita no teste e
  refeita a partir dos números da própria linha.
- O teto de cada faixa fica na faixa de baixo (o anexo diz "até"); um
  centavo acima sobe de faixa.
- Fator R em 27,99%, 28% e 28,01%.
- A 6ª faixa de 2027 e 2028 nos cinco anexos, com a conta à mão; as faixas 1
  a 5 iguais às de hoje; 2018, 2026, 2029 e depois com a tabela de hoje.
- Teste de mutação: trocar qualquer um dos 90 valores da tabela, uma das
  cinco nominais de 2027 ou uma fronteira de ano, um de cada vez, derruba
  pelo menos um teste.

Arredondamento: a lei não fixa regra. A alíquota efetiva guarda todos os
dígitos; o valor do mês é arredondado em centavos com `ROUND_HALF_UP`.

## Como biblioteca

```python
from simples_nacional import aliquota_efetiva, valor_devido, anexo_por_fator_r, avisos

aliquota_efetiva("I", 4_500_000, ano=2026)      # Decimal('0.106')
aliquota_efetiva("I", 4_500_000, ano=2027)      # Decimal('0.105')
valor_devido("I", 4_500_000, "375000", ano=2026) # Decimal('39750.00')
anexo_por_fator_r(280_000, 1_000_000)           # 'III'
avisos(4_500_000)                               # ['RBT12 acima do sublimite ...']
```

Valores em `Decimal`, `int` ou `str`; `float` é recusado, porque erra
centavo. RBT12 acima de R$ 4,8 milhões levanta `LimiteExcedido` (um
`ValueError`).

`ano` é o ano-calendário do **mês de apuração**, não o de hoje: o DAS de
dezembro de 2026, calculado em janeiro de 2027, usa a tabela de 2026. Por
isso ele é obrigatório desde a 0.2.0: quem vinha da 0.1.0 acrescenta
`ano=` às chamadas de `faixa`, `aliquota_efetiva` e `valor_devido`.

## Licença

[MIT](LICENSE).
