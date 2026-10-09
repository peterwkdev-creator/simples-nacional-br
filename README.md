# simples-nacional

Effective rate, monthly amount and Fator R for Brazil's **Simples Nacional**,
checked band by band against the official tables of Lei Complementar 123/2006
(wording of LC 155/2016). Pure Python, standard library only, `Decimal` from
end to end.

```bash
python -m unittest
```

```bash
python -m simples_nacional --anexo I --rbt12 4500000 --receita-mes 375000
```

Both run from a clean checkout, no install. Tested with Python 3.12.

> **This is an estimate, not tax advice.** It does not replace the PGDAS-D or
> an accountant. All examples use made-up numbers.

## Why

The effective rate is not the rate printed in the annex. LC 123, art. 18,
§ 1º-A:

```
effective rate = (RBT12 × nominal rate − deduction) / RBT12
```

RBT12 is the gross revenue of the 12 months before the one being calculated.
A trading company with RBT12 of R$ 4,500,000 is in the 6th band of Annex I
(nominal 19%, deduction R$ 378,000):

```
(4,500,000 × 19% − 378,000) / 4,500,000 = 477,000 / 4,500,000 = 10.60%
```

Applying the nominal 19% instead gives R$ 855,000 a year where the law gives
R$ 477,000. This is the error reported in
[mcp-fiscal-brasil#146](https://github.com/DeHor-Labs/mcp-fiscal-brasil/issues/146).

## What it covers

| | Source (LC 123/2006, wording of LC 155/2016) |
|---|---|
| Annexes I to V, six bands each: ceiling, nominal rate, deduction | Annexes I to V |
| Effective rate | art. 18, § 1º-A |
| Monthly amount: monthly revenue × effective rate | art. 18, § 3º |
| Fator R: 12-month payroll ÷ RBT12; ≥ 28% → Annex III, else V | art. 18, §§ 5º-J, 5º-K, 5º-M, 24 |
| R$ 4.8 million ceiling: an explained error, never a number | art. 3º, II |
| R$ 3.6 million sublimit (ICMS and ISS paid outside the DAS): a warning | art. 13-A |
| First months of activity: revenue annualized | art. 18, § 2º |

Every table value was read at the Brazilian Chamber of Deputies on
09/10/2026 ([consolidated LC 155/2016](https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html));
the source sits next to the table in `simples_nacional/tabelas.py`.

Not covered: CNAE → annex mapping, the split of the amount by tax, state
sublimits, the year in which the sublimit is crossed (art. 3º, §§ 11 to 15),
the very first month of activity (ruled by a CGSN resolution), and MEI.

## How it is tested

- One case per band of each annex (30), with the hand calculation written in
  the test and re-done from the row's own numbers.
- Every band ceiling stays in the lower band (the annex says "up to"); one
  cent above moves up.
- Fator R at 27.99%, 28% and 28.01%.
- Mutation check: changing any of the 90 table values, one at a time, makes
  at least one test fail.

Rounding: the law sets no rule. The effective rate keeps every digit; the
monthly amount is rounded to cents with `ROUND_HALF_UP`.

## As a library

```python
from decimal import Decimal
from simples_nacional import aliquota_efetiva, valor_devido, anexo_por_fator_r, avisos

aliquota_efetiva("I", 4_500_000)               # Decimal('0.106')
valor_devido("I", 4_500_000, "375000")          # Decimal('39750.00')
anexo_por_fator_r(280_000, 1_000_000)           # 'III'
avisos(4_500_000)                               # ['RBT12 acima do sublimite ...']
```

Amounts are `Decimal`, `int` or `str`; `float` is refused, because it misses
cents. RBT12 above R$ 4.8 million raises `LimiteExcedido` (a `ValueError`).
Messages are in Portuguese, the language of the people who use the numbers.

## License

[MIT](LICENSE).
