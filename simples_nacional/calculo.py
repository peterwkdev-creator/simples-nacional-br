"""Effective rate, monthly amount, Fator R and limits (LC 123/2006, art. 18).

Decimal from end to end; the only rounding is the monthly amount, to cents
with ROUND_HALF_UP (the law sets no rounding rule: library convention).
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .tabelas import ANEXOS, FATOR_R_MINIMO, LIMITE_RECEITA, SUBLIMITE_ICMS_ISS

CENTAVO = Decimal("0.01")


class LimiteExcedido(ValueError):
    """RBT12 above R$ 4.8 million: no Simples Nacional rate applies."""


def reais(valor):
    """Brazilian currency format: 4800000 -> '4.800.000,00'."""
    texto = f"{Decimal(valor).quantize(CENTAVO, ROUND_HALF_UP):,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _decimal(valor, nome):
    if isinstance(valor, float):
        raise TypeError(f"{nome}: use Decimal, int or str, not float (float misses cents)")
    if isinstance(valor, bool) or not isinstance(valor, (Decimal, int, str)):
        raise TypeError(f"{nome}: expected Decimal, int or str, got {type(valor).__name__}")
    try:
        numero = Decimal(valor)
    except InvalidOperation:
        raise ValueError(f"{nome}: not a number: {valor!r}") from None
    if not numero.is_finite():
        raise ValueError(f"{nome}: not a finite number: {valor!r}")
    return numero


def _anexo(anexo):
    chave = anexo.upper() if isinstance(anexo, str) else anexo
    if chave not in ANEXOS:
        raise ValueError(f"anexo: expected one of I, II, III, IV, V, got {anexo!r}")
    return ANEXOS[chave]


def faixa(anexo, rbt12):
    """Band of the annex for the 12-month gross revenue (ceiling included)."""
    faixas = _anexo(anexo)
    rbt12 = _decimal(rbt12, "rbt12")
    if rbt12 <= 0:
        raise ValueError(
            "rbt12 must be positive; for the first months of activity use "
            "rbt12_inicio_atividade (LC 123, art. 18, par. 2)")
    if rbt12 > LIMITE_RECEITA:
        raise LimiteExcedido(
            f"RBT12 de R$ {reais(rbt12)} acima do limite de R$ {reais(LIMITE_RECEITA)} "
            "(LC 123, art. 3, II): nao ha aliquota do Simples Nacional para essa "
            "receita; a empresa fica sujeita a exclusao do regime.")
    for f in faixas:
        if rbt12 <= f.teto:
            return f
    raise AssertionError("unreachable: the last band ends at the limit")


def aliquota_efetiva(anexo, rbt12):
    """(RBT12 x Aliq - PD) / RBT12, LC 123, art. 18, par. 1-A. Not rounded."""
    f = faixa(anexo, rbt12)
    rbt12 = Decimal(rbt12)
    return (rbt12 * f.aliquota - f.parcela_deduzir) / rbt12


def valor_devido(anexo, rbt12, receita_mes):
    """Revenue of the month x effective rate (art. 18, par. 3), in cents.

    Above the R$ 3.6 mi sublimit this is the federal DAS only: ICMS/ISS are
    paid outside it (see avisos).
    """
    receita_mes = _decimal(receita_mes, "receita_mes")
    if receita_mes < 0:
        raise ValueError("receita_mes must not be negative")
    efetiva = aliquota_efetiva(anexo, rbt12)
    return (receita_mes * efetiva).quantize(CENTAVO, ROUND_HALF_UP)


def fator_r(folha12, rbt12):
    """Payroll of the last 12 months / RBT12 (art. 18, par. 5-K and 24)."""
    folha12 = _decimal(folha12, "folha12")
    rbt12 = _decimal(rbt12, "rbt12")
    if folha12 < 0:
        raise ValueError("folha12 must not be negative")
    if rbt12 <= 0:
        raise ValueError("rbt12 must be positive")
    return folha12 / rbt12


def anexo_por_fator_r(folha12, rbt12):
    """'III' if Fator R >= 28% (art. 18, par. 5-J), else 'V'. No rounding."""
    return "III" if fator_r(folha12, rbt12) >= FATOR_R_MINIMO else "V"


def rbt12_inicio_atividade(receita_acumulada, meses):
    """RBT12 for a company with fewer than 12 months of activity.

    Art. 18, par. 2 scales the bands by meses/12; annualizing the revenue by
    12/meses gives the same effective rate. `meses` counts the months before
    the one being calculated (1 to 11). The first month itself is ruled by a
    CGSN resolution, not covered here.
    """
    receita_acumulada = _decimal(receita_acumulada, "receita_acumulada")
    if isinstance(meses, bool) or not isinstance(meses, int) or not 1 <= meses <= 11:
        raise ValueError("meses must be an int from 1 to 11; with 12 or more use the actual RBT12")
    if receita_acumulada < 0:
        raise ValueError("receita_acumulada must not be negative")
    return receita_acumulada * 12 / meses


def avisos(rbt12):
    """Warnings about the limits, in Portuguese (the users' language)."""
    rbt12 = _decimal(rbt12, "rbt12")
    saida = []
    if rbt12 > LIMITE_RECEITA:
        saida.append(
            f"RBT12 acima de R$ {reais(LIMITE_RECEITA)}: fora do Simples Nacional "
            "(LC 123, art. 3, II).")
    elif rbt12 > SUBLIMITE_ICMS_ISS:
        saida.append(
            f"RBT12 acima do sublimite de R$ {reais(SUBLIMITE_ICMS_ISS)} (LC 123, "
            "art. 13-A): ICMS e ISS sao recolhidos fora do DAS, pelas regras do "
            "estado e do municipio; o valor acima e so a parte federal (na 6a "
            "faixa a reparticao da lei ja da 0% a ICMS e ISS). A regra do ano em "
            "que o sublimite e ultrapassado (art. 3, par. 11 a 15) nao e calculada aqui.")
    return saida
