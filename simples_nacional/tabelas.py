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
