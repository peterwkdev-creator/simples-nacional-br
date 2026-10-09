"""Official tables of the Simples Nacional (Brazilian simplified tax regime).

Source: Lei Complementar 123/2006, Annexes I to V, as worded by Lei
Complementar 155/2016, art. 2 (in force since 01/01/2018). Read at the
Chamber of Deputies (consolidated LC 155 text) on 09/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html

Each row: (ceiling of the 12-month gross revenue, nominal rate, deduction),
all in R$. The ceiling belongs to its own band ("Ate 180.000,00").
"""

from decimal import Decimal
from typing import NamedTuple


class Faixa(NamedTuple):
    numero: int
    teto: Decimal
    aliquota: Decimal
    parcela_deduzir: Decimal


def _anexo(*linhas):
    return tuple(
        Faixa(n, Decimal(teto), Decimal(aliquota) / 100, Decimal(pd))
        for n, (teto, aliquota, pd) in enumerate(linhas, 1)
    )


ANEXOS = {
    # Anexo I - Comercio
    "I": _anexo(
        ("180000.00", "4.00", "0"),
        ("360000.00", "7.30", "5940.00"),
        ("720000.00", "9.50", "13860.00"),
        ("1800000.00", "10.70", "22500.00"),
        ("3600000.00", "14.30", "87300.00"),
        ("4800000.00", "19.00", "378000.00"),
    ),
    # Anexo II - Industria
    "II": _anexo(
        ("180000.00", "4.50", "0"),
        ("360000.00", "7.80", "5940.00"),
        ("720000.00", "10.00", "13860.00"),
        ("1800000.00", "11.20", "22500.00"),
        ("3600000.00", "14.70", "85500.00"),
        ("4800000.00", "30.00", "720000.00"),
    ),
    # Anexo III - locacao de bens moveis e servicos fora do art. 18, par. 5-C
    "III": _anexo(
        ("180000.00", "6.00", "0"),
        ("360000.00", "11.20", "9360.00"),
        ("720000.00", "13.50", "17640.00"),
        ("1800000.00", "16.00", "35640.00"),
        ("3600000.00", "21.00", "125640.00"),
        ("4800000.00", "33.00", "648000.00"),
    ),
    # Anexo IV - servicos do art. 18, par. 5-C
    "IV": _anexo(
        ("180000.00", "4.50", "0"),
        ("360000.00", "9.00", "8100.00"),
        ("720000.00", "10.20", "12420.00"),
        ("1800000.00", "14.00", "39780.00"),
        ("3600000.00", "22.00", "183780.00"),
        ("4800000.00", "33.00", "828000.00"),
    ),
    # Anexo V - servicos do art. 18, par. 5-I
    "V": _anexo(
        ("180000.00", "15.50", "0"),
        ("360000.00", "18.00", "4500.00"),
        ("720000.00", "19.50", "9900.00"),
        ("1800000.00", "20.50", "17100.00"),
        ("3600000.00", "23.00", "62100.00"),
        ("4800000.00", "30.50", "540000.00"),
    ),
}

# LC 123, art. 3, II (wording of LC 155/2016): small business up to R$ 4.8 mi.
LIMITE_RECEITA = Decimal("4800000.00")

# LC 123, art. 13-A (wording of LC 155/2016): above R$ 3.6 mi, ICMS and ISS
# are paid outside the DAS. In every annex the 6th band's tax split gives 0%
# to ICMS/ISS (the "-" in the "Percentual de Reparticao" tables).
SUBLIMITE_ICMS_ISS = Decimal("3600000.00")

# LC 123, art. 18, par. 5-J: Annex III when payroll / revenue is "igual ou
# superior a 28%"; otherwise Annex V (par. 5-M). Payroll per par. 24.
FATOR_R_MINIMO = Decimal("0.28")
