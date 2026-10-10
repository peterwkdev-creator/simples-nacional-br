"""Tabelas oficiais do Simples Nacional.

Fonte: Lei Complementar 123/2006, Anexos I a V, na redação da Lei
Complementar 155/2016, art. 2º (vigência desde 01/01/2018). Lido no site da
Câmara dos Deputados (texto atualizado da LC 155) em 09/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html

Cada linha: (teto da receita bruta de 12 meses, alíquota nominal, parcela a
deduzir), tudo em R$. O teto pertence à própria faixa ("Até 180.000,00").

A tabela depende do ano-calendário de apuração. LC 214/2025, art. 519 e
Anexos XVIII a XXII (efeitos a partir de 01/01/2027, art. 544, III), texto
atualizado lido no site da Câmara em 09/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html
- "Para os anos-calendário 2027 e 2028": nominal da 6ª faixa 0,1 ponto
  abaixo, mesma parcela a deduzir; faixas 1 a 5 iguais;
- "A partir do ano-calendário 2029": as mesmas alíquotas e parcelas de ANEXOS.
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

# Repartição do ICMS (Anexos I e II) e do ISS (III, IV e V) da 1ª à 5ª faixa,
# da tabela "Percentual de Repartição dos Tributos" de cada anexo (mesma fonte
# do cabeçalho, conferida no HTML da Câmara em 09/10/2026 e 10/10/2026). Na
# 6ª faixa é 0%. Vale até 2026.
_ICMS_ISS_POR_FAIXA = {
    "I": ("34.00", "34.00", "33.50", "33.50", "33.50"),
    "II": ("32.00", "32.00", "32.00", "32.00", "32.00"),
    "III": ("33.50", "32.00", "32.50", "32.50", "33.50"),
    "IV": ("44.50", "40.00", "40.00", "40.00", "40.00"),
    "V": ("14.00", "17.00", "19.00", "21.00", "23.50"),
}
ICMS_ISS_POR_FAIXA = {
    anexo: tuple(Decimal(p) / 100 for p in partes) for anexo, partes in _ICMS_ISS_POR_FAIXA.items()
}

# Nota (*) dos Anexos III e IV: o percentual efetivo do ISS vai até 5%, e a
# diferença passa aos tributos federais da mesma faixa (Res. CGSN 140,
# art. 21, III, a, até 2026).
TETO_ISS = Decimal("0.05")

# LC 214/2025, Anexos XVIII a XXII, tabelas "Percentual de Repartição dos
# Tributos" de cada período (texto compilado do Planalto,
# https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm, já com a LC
# 227/2026, salvo em 09/10/2026 e conferido em 10/10/2026): na 5ª faixa, ICMS ou ISS e IBS, por
# ano de início do período. De 2033 em diante, só o IBS. Acima do sublimite,
# sem impedimento no ano, seguem no DAS por ela (Res. CGSN 140, art. 21, IV,
# redação da Res. CGSN 190/2026, desde 01/01/2027).
_QUINTA_FAIXA_DESDE_2027 = {
    2027: {"I": ("33.50", "0.17"), "II": ("32.00", "0.15"), "III": ("33.50", "0.17"),
           "IV": ("40.00", "0.24"), "V": ("23.50", "0.19")},
    2029: {"I": ("30.15", "3.35"), "II": ("28.80", "3.20"), "III": ("30.15", "3.35"),
           "IV": ("36.00", "4.00"), "V": ("21.15", "2.35")},
    2030: {"I": ("26.80", "6.70"), "II": ("25.60", "6.40"), "III": ("26.80", "6.70"),
           "IV": ("32.00", "8.00"), "V": ("18.80", "4.70")},
    2031: {"I": ("23.45", "10.05"), "II": ("22.40", "9.60"), "III": ("23.45", "10.05"),
           "IV": ("28.00", "12.00"), "V": ("16.45", "7.05")},
    2032: {"I": ("20.10", "13.40"), "II": ("19.20", "12.80"), "III": ("20.10", "13.40"),
           "IV": ("24.00", "16.00"), "V": ("14.10", "9.40")},
    2033: {"I": ("0", "33.50"), "II": ("0", "32.00"), "III": ("0", "33.50"),
           "IV": ("0", "40.00"), "V": ("0", "23.50")},
}


def quinta_faixa_icms_iss_ibs(anexo, *, ano):
    """(ICMS ou ISS, IBS) da repartição da 5ª faixa no ano-calendário, em fração.

    Até 2026, a 5ª faixa de ICMS_ISS_POR_FAIXA (I 33,50%, II 32,00%, III
    33,50%, IV 40,00%, V 23,50%): acima do sublimite, sem impedimento no ano,
    ICMS e ISS seguem no DAS por ela (Res. CGSN 140, art. 21, III, b, até
    31/12/2026); o IBS é zero. `ano` se confere como nos cálculos.
    """
    vigencia(ano)
    chave = anexo.upper() if isinstance(anexo, str) else None
    if chave not in ICMS_ISS_POR_FAIXA:
        raise ValueError(f"anexo: esperado I, II, III, IV ou V, veio {anexo!r}")
    if ano <= 2026:
        return ICMS_ISS_POR_FAIXA[chave][4], Decimal(0)
    inicio = max(a for a in _QUINTA_FAIXA_DESDE_2027 if a <= ano)
    icms_iss, ibs = _QUINTA_FAIXA_DESDE_2027[inicio][chave]
    return Decimal(icms_iss) / 100, Decimal(ibs) / 100

# LC 123, art. 18, § 5º-J: Anexo III quando folha / receita for "igual ou
# superior a 28%"; senão Anexo V (§ 5º-M). Folha conforme o § 24.
FATOR_R_MINIMO = Decimal("0.28")

# LC 214/2025, Anexos XVIII a XXII, "Para os anos-calendário 2027 e 2028":
# nominal da 6ª faixa (I 18,90%, II 29,90%, III 32,90%, IV 32,90%, V 30,40%).
_SEXTA_FAIXA_2027 = {"I": "18.90", "II": "29.90", "III": "32.90", "IV": "32.90", "V": "30.40"}

ANEXOS_2027_2028 = {
    anexo: faixas[:5] + (faixas[5]._replace(aliquota=Decimal(_SEXTA_FAIXA_2027[anexo]) / 100),)
    for anexo, faixas in ANEXOS.items()
}

PRIMEIRO_ANO = 2018  # LC 155/2016: a tabela de ANEXOS vale desde 01/01/2018


class Vigencia(NamedTuple):
    anexos: dict
    fonte: str


def vigencia(ano):
    """Tabela e fonte legal do ano-calendário de apuração."""
    if isinstance(ano, bool) or not isinstance(ano, int):
        raise TypeError(f"ano: esperado int (ano-calendário de apuração), veio {type(ano).__name__}")
    if ano < PRIMEIRO_ANO:
        raise ValueError(f"ano {ano}: a biblioteca cobre a tabela vigente desde {PRIMEIRO_ANO} (LC 155/2016)")
    if ano <= 2026:
        return Vigencia(ANEXOS, "LC 123/2006, Anexos I a V, redação da LC 155/2016")
    if ano <= 2028:
        return Vigencia(ANEXOS_2027_2028,
                        "LC 214/2025, Anexos XVIII a XXII, anos-calendário 2027 e 2028")
    return Vigencia(ANEXOS, "LC 214/2025, Anexos XVIII a XXII, a partir do ano-calendário 2029")
