# simples-nacional-br

[![testes](https://github.com/peterwkdev-creator/simples-nacional-br/actions/workflows/testes.yml/badge.svg)](https://github.com/peterwkdev-creator/simples-nacional-br/actions/workflows/testes.yml)

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

Os dois rodam do checkout limpo, sem instalar nada. Testado a cada push com Python 3.9 a 3.13 (Linux) e
3.13 (Windows).
Sem `--ano`, a linha de comando usa o ano corrente e diz qual tabela usou.

> **É estimativa, não consultoria tributária.** Não substitui o PGDAS-D nem o
> contador. Todos os exemplos usam números inventados.

## Por quê

A alíquota efetiva não é a alíquota impressa no anexo. LC 123, art. 18,
§ 1º-A:

```
alíquota efetiva = (RBT12 × alíquota nominal − parcela a deduzir) / RBT12
```

RBT12 é a receita bruta dos 12 meses anteriores ao período de apuração (a
partir de 2027, dos 12 meses antecedentes ao mês anterior: para apurar março,
de fevereiro do ano anterior a janeiro; LC 123, art. 18, § 1º, na redação da
LC 214/2025). Um
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
| Sublimite de R$ 3,6 milhões: aviso de que o valor é só a parte federal e de que ICMS e ISS (e o IBS, desde 2027) saem do DAS ou seguem nele conforme a receita acumulada no ano | art. 13-A; Res. CGSN 140/2018, arts. 21, III, b, e 24; LC 214/2025, arts. 517 e 518 |
| Início de atividade, mês a mês: até 2026, 1º mês com a receita do próprio mês × 12 e do 2º ao 12º com a média dos anteriores × 12; a partir de 2027, 1º e 2º mês na 1ª faixa e do 3º ao 13º com a média dos meses antes do mês anterior × 12 | art. 18, § 2º; Res. CGSN 140/2018, art. 22, e Res. CGSN 190/2026 |
| Ano de início de atividade: limite de R$ 400.000,00 e sublimite de R$ 300.000,00 vezes os meses do início a dezembro (fração conta como mês), com aviso de exclusão desde o início, se o excesso passa de 20%, ou a partir do ano seguinte | art. 3º, §§ 2º e 10 a 13; art. 31, III; Res. CGSN 140/2018, arts. 3º e 9º, § 2º |
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
sublimites estaduais, o ano em que o sublimite é ultrapassado depois do de
início de atividade (art. 3º, §§ 11 a 15), as receitas de exportação, que
têm limite próprio (art. 3º, § 14), o ICMS e o ISS que seguem no DAS com RBT12 acima de R$ 3,6
milhões e receita do ano abaixo dele (Res. CGSN 140, art. 21, III, b), a empresa aberta no ano anterior ao da opção (Res. CGSN 140,
art. 22, § 4º) e o MEI.

## Como é testado

- Um caso por faixa de cada anexo (30), com a conta à mão escrita no teste e
  refeita a partir dos números da própria linha.
- O teto de cada faixa fica na faixa de baixo (o anexo diz "até"); um
  centavo acima sobe de faixa.
- Fator R em 27,99%, 28% e 28,01%.
- A 6ª faixa de 2027 e 2028 nos cinco anexos, com a conta à mão; as faixas 1
  a 5 iguais às de hoje; 2018, 2026, 2029 e depois com a tabela de hoje.
- Início de atividade: 1º, 2º, 4º e 12º mês até 2026; 1º, 2º, 3º, 5º e 13º
  a partir de 2027, com o mês anterior ao de apuração fora da média.
- Teste de mutação: trocar qualquer um dos 90 valores da tabela, uma das
  cinco nominais de 2027, uma fronteira de ano ou uma regra do início de
  atividade, um de cada vez, derruba pelo menos um teste.

As regras do início de atividade foram lidas em 09/10/2026 no portal de
normas da Receita:
[Res. CGSN 140/2018](https://normasinternet2.receita.fazenda.gov.br/#/consulta/externa/92278)
e [Res. CGSN 190/2026](https://normasinternet2.receita.fazenda.gov.br/#/consulta/externa/152832).
Média zero no início de atividade (nenhuma venda ainda) dá a alíquota da
1ª faixa: a fórmula não se define com RBT12 zero, e essa é uma convenção da
biblioteca.

Arredondamento: a lei não fixa regra. A alíquota efetiva guarda todos os
dígitos; o valor do mês é arredondado em centavos com `ROUND_HALF_UP`. As
contas usam um contexto `Decimal` próprio (28 dígitos): um
`getcontext().prec` mudado no programa de quem usa a biblioteca não muda o
resultado. Na linha de comando, a efetiva da linha "Valor do mês" sai com
as casas (4 ou mais) que fecham a conta no centavo, e o Fator R é cortado,
não arredondado, na 4ª casa: 27,99999% aparece 27,9999%, ao lado do Anexo V.

## Como biblioteca

```python
from simples_nacional import (aliquota_efetiva, anexo_por_fator_r, avisos, valor_devido,
                              valor_devido_inicio_atividade)

aliquota_efetiva("I", 4_500_000, ano=2026)      # Decimal('0.106')
aliquota_efetiva("I", 4_500_000, ano=2027)      # Decimal('0.105')
valor_devido("I", 4_500_000, "375000", ano=2026) # Decimal('39750.00')
anexo_por_fator_r(280_000, 1_000_000)           # 'III'
avisos(4_500_000, ano=2026)                     # ['RBT12 acima do sublimite ...']

# início de atividade: receita de cada mês, do 1º até o de apuração
valor_devido_inicio_atividade("I", [30_000, 50_000], ano=2026)  # Decimal('2825.00')
valor_devido_inicio_atividade("I", [400_000], ano=2027)         # Decimal('16000.00'), 1ª faixa
```

Na linha de comando, o início de atividade vai em `--receitas`, separadas
por ponto e vírgula, no lugar de `--rbt12` e `--receita-mes`:

```bash
python -m simples_nacional --ano 2026 --anexo I --receitas "30.000;50.000"
```

Com `--mes-inicio` (o mês do calendário em que a atividade começou, de 1 a
12), a saída confere a receita do ano de início contra o limite e o
sublimite proporcionais; sem ele, avisa quando a receita passa de
R$ 300.000,00 por mês e pede o mês. Na API, o mesmo vem de
`avisos_inicio_atividade(receitas, mes_inicio, ano=...)`, desde a 0.4.0:

```python
from simples_nacional import avisos_inicio_atividade

# aberta em novembro: 2 meses até dezembro, limite 800.000 e sublimite 600.000
avisos_inicio_atividade([300_000, 400_000], 11, ano=2026)
# ['Receita acumulada no ano de início de atividade (2026) de R$ 700.000,00,
#   acima do sublimite proporcional de R$ 600.000,00 ...']
```

Na linha de comando e em `ler_numero`, números aceitos: `4500000`,
`4500000.00`, `1000,50`, `1.000,50` e
`360.000` (ponto seguido de três dígitos é milhar), com ou sem `R$` na
frente e espaço nas pontas, como o Excel copia a célula (`R$ 1.000,50`). O
que é ambíguo, como `1,000.50` ou `100 000`, dá erro em vez de virar outro
número. `--version` mostra a versão instalada.

A mesma leitura e a saída no formato brasileiro são públicas desde a 0.3.1,
para quem integra a biblioteca num sistema:

```python
from decimal import Decimal
from simples_nacional import ler_numero, para_decimal, porcentagem, reais

ler_numero("360.000")                 # Decimal('360000'); ambíguo: ValueError
para_decimal("1000.50", "receita")    # Decimal('1000.50'); float: TypeError
para_decimal("360.000", "receita")    # Decimal('360.000'): ponto decimal, como no Decimal
porcentagem(Decimal("0.0565"))        # '5,6500%'
reais(Decimal("4800000"))             # '4.800.000,00'
```

Na API, valores em `Decimal`, `int` ou `str` (o texto com ponto decimal,
como no `Decimal`: `"360.000"` é 360); `float` é recusado, porque erra
centavo. RBT12 acima de R$ 4,8 milhões levanta `LimiteExcedido` (um
`ValueError`).

`ano` é o ano-calendário do **mês de apuração**, não o de hoje: o DAS de
dezembro de 2026, calculado em janeiro de 2027, usa a tabela de 2026. Por
isso ele é obrigatório desde a 0.2.0: quem vinha da 0.1.0 acrescenta
`ano=` às chamadas de `faixa`, `aliquota_efetiva` e `valor_devido`.

## Licença

[MIT](LICENSE).
