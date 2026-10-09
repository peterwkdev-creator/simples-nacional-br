"""Tabelas oficiais do Simples Nacional.

Fonte: Lei Complementar 123/2006, Anexos I a V, na redação da Lei
Complementar 155/2016, art. 2º (vigência desde 01/01/2018). Lido no site da
Câmara dos Deputados (texto atualizado da LC 155) em 09/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html

Cada linha: (teto da receita bruta de 12 meses, alíquota nominal, parcela a
deduzir), tudo em R$. O teto pertence à própria faixa ("Até 180.000,00").
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
    # Anexo I - Comércio
    "I": _anexo(
        ("180000.00", "4.00", "0"),
        ("360000.00", "7.30", "5940.00"),
        ("720000.00", "9.50", "13860.00"),
        ("1800000.00", "10.70", "22500.00"),
        ("3600000.00", "14.30", "87300.00"),
        ("4800000.00", "19.00", "378000.00"),
    ),
    # Anexo II - Indústria
    "II": _anexo(
        ("180000.00", "4.50", "0"),
        ("360000.00", "7.80", "5940.00"),
        ("720000.00", "10.00", "13860.00"),
        ("1800000.00", "11.20", "22500.00"),
        ("3600000.00", "14.70", "85500.00"),
        ("4800000.00", "30.00", "720000.00"),
    ),
    # Anexo III - locação de bens móveis e serviços fora do art. 18, § 5º-C
    "III": _anexo(
        ("180000.00", "6.00", "0"),
        ("360000.00", "11.20", "9360.00"),
        ("720000.00", "13.50", "17640.00"),
        ("1800000.00", "16.00", "35640.00"),
        ("3600000.00", "21.00", "125640.00"),
        ("4800000.00", "33.00", "648000.00"),
    ),
    # Anexo IV - serviços do art. 18, § 5º-C
    "IV": _anexo(
        ("180000.00", "4.50", "0"),
        ("360000.00", "9.00", "8100.00"),
        ("720000.00", "10.20", "12420.00"),
        ("1800000.00", "14.00", "39780.00"),
        ("3600000.00", "22.00", "183780.00"),
        ("4800000.00", "33.00", "828000.00"),
    ),
    # Anexo V - serviços do art. 18, § 5º-I
    "V": _anexo(
        ("180000.00", "15.50", "0"),
        ("360000.00", "18.00", "4500.00"),
        ("720000.00", "19.50", "9900.00"),
        ("1800000.00", "20.50", "17100.00"),
        ("3600000.00", "23.00", "62100.00"),
        ("4800000.00", "30.50", "540000.00"),
    ),
}

# LC 123, art. 3º, II (redação da LC 155/2016): EPP até R$ 4,8 milhões.
LIMITE_RECEITA = Decimal("4800000.00")

# LC 123, art. 13-A (redação da LC 155/2016): acima de R$ 3,6 milhões, ICMS e
# ISS são recolhidos fora do DAS. Em todos os anexos a repartição da 6ª faixa
# dá 0% a ICMS/ISS (o "-" nas tabelas de "Percentual de Repartição").
SUBLIMITE_ICMS_ISS = Decimal("3600000.00")

# LC 123, art. 18, § 5º-J: Anexo III quando folha / receita for "igual ou
# superior a 28%"; senão Anexo V (§ 5º-M). Folha conforme o § 24.
FATOR_R_MINIMO = Decimal("0.28")
