"""Alíquota efetiva, valor do mês, Fator R e limites (LC 123/2006, art. 18).

Decimal do começo ao fim; o único arredondamento é o do valor do mês, em
centavos com ROUND_HALF_UP (a lei não fixa regra: convenção da biblioteca).
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .tabelas import FATOR_R_MINIMO, LIMITE_RECEITA, SUBLIMITE_ICMS_ISS, vigencia

CENTAVO = Decimal("0.01")


class LimiteExcedido(ValueError):
    """RBT12 acima de R$ 4,8 milhões: nenhuma alíquota do Simples se aplica."""


def reais(valor):
    """Formato brasileiro: 4800000 -> '4.800.000,00'."""
    texto = f"{Decimal(valor).quantize(CENTAVO, ROUND_HALF_UP):,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _decimal(valor, nome):
    if isinstance(valor, float):
        raise TypeError(f"{nome}: use Decimal, int ou str, não float (float erra centavo)")
    if isinstance(valor, bool) or not isinstance(valor, (Decimal, int, str)):
        raise TypeError(f"{nome}: esperado Decimal, int ou str, veio {type(valor).__name__}")
    try:
        numero = Decimal(valor)
    except InvalidOperation:
        raise ValueError(f"{nome}: não é número: {valor!r}") from None
    if not numero.is_finite():
        raise ValueError(f"{nome}: não é número finito: {valor!r}")
    return numero


def _anexo(anexo, ano):
    anexos = vigencia(ano).anexos
    chave = anexo.upper() if isinstance(anexo, str) else anexo
    if chave not in anexos:
        raise ValueError(f"anexo: esperado I, II, III, IV ou V, veio {anexo!r}")
    return anexos[chave]


def faixa(anexo, rbt12, *, ano):
    """Faixa do anexo para a receita bruta de 12 meses (o teto é da faixa).

    `ano` é o ano-calendário do mês de apuração, não o de hoje: o DAS de
    dezembro de 2026, pago em janeiro de 2027, usa a tabela de 2026.
    """
    faixas = _anexo(anexo, ano)
    rbt12 = _decimal(rbt12, "rbt12")
    if rbt12 <= 0:
        raise ValueError(
            "rbt12 tem de ser positivo; nos primeiros meses de atividade use "
            "rbt12_inicio_atividade (LC 123, art. 18, § 2º)")
    if rbt12 > LIMITE_RECEITA:
        raise LimiteExcedido(
            f"RBT12 de R$ {reais(rbt12)} acima do limite de R$ {reais(LIMITE_RECEITA)} "
            "(LC 123, art. 3º, II): não há alíquota do Simples Nacional para essa "
            "receita; a empresa fica sujeita à exclusão do regime.")
    for f in faixas:
        if rbt12 <= f.teto:
            return f
    raise AssertionError("inalcançável: a última faixa termina no limite")


def aliquota_efetiva(anexo, rbt12, *, ano):
    """(RBT12 × Aliq − PD) / RBT12, LC 123, art. 18, § 1º-A. Sem arredondar."""
    f = faixa(anexo, rbt12, ano=ano)
    rbt12 = Decimal(rbt12)
    return (rbt12 * f.aliquota - f.parcela_deduzir) / rbt12


def valor_devido(anexo, rbt12, receita_mes, *, ano):
    """Receita do mês × alíquota efetiva (art. 18, § 3º), em centavos.

    Acima do sublimite de R$ 3,6 milhões é só o DAS federal: ICMS e ISS são
    recolhidos fora dele (ver avisos). A partir de 2027 é o DAS cheio, com
    as parcelas de CBS e IBS; quem optar pelo regime regular desses tributos
    (LC 123, art. 13, § 9º) as paga fora e o DAS fica menor.
    """
    receita_mes = _decimal(receita_mes, "receita_mes")
    if receita_mes < 0:
        raise ValueError("receita_mes não pode ser negativa")
    efetiva = aliquota_efetiva(anexo, rbt12, ano=ano)
    return (receita_mes * efetiva).quantize(CENTAVO, ROUND_HALF_UP)


def fator_r(folha12, rbt12):
    """Folha dos últimos 12 meses ÷ RBT12 (art. 18, §§ 5º-K e 24)."""
    folha12 = _decimal(folha12, "folha12")
    rbt12 = _decimal(rbt12, "rbt12")
    if folha12 < 0:
        raise ValueError("folha12 não pode ser negativa")
    if rbt12 <= 0:
        raise ValueError("rbt12 tem de ser positivo")
    return folha12 / rbt12


def anexo_por_fator_r(folha12, rbt12):
    """'III' se o Fator R for 28% ou mais (art. 18, § 5º-J), senão 'V'. Sem arredondar."""
    return "III" if fator_r(folha12, rbt12) >= FATOR_R_MINIMO else "V"


def rbt12_inicio_atividade(receita_acumulada, meses):
    """RBT12 de empresa com menos de 12 meses de atividade.

    O art. 18, § 2º proporcionaliza as faixas por meses/12; anualizar a
    receita por 12/meses dá a mesma alíquota efetiva. `meses` conta os meses
    anteriores ao de apuração (1 a 11). O primeiro mês é regido por
    resolução do CGSN e não é coberto aqui.
    """
    receita_acumulada = _decimal(receita_acumulada, "receita_acumulada")
    if isinstance(meses, bool) or not isinstance(meses, int) or not 1 <= meses <= 11:
        raise ValueError("meses tem de ser int de 1 a 11; com 12 ou mais use o RBT12 real")
    if receita_acumulada < 0:
        raise ValueError("receita_acumulada não pode ser negativa")
    return receita_acumulada * 12 / meses


def avisos(rbt12):
    """Avisos sobre os limites."""
    rbt12 = _decimal(rbt12, "rbt12")
    saida = []
    if rbt12 > LIMITE_RECEITA:
        saida.append(
            f"RBT12 acima de R$ {reais(LIMITE_RECEITA)}: fora do Simples Nacional "
            "(LC 123, art. 3º, II).")
    elif rbt12 > SUBLIMITE_ICMS_ISS:
        saida.append(
            f"RBT12 acima do sublimite de R$ {reais(SUBLIMITE_ICMS_ISS)} (LC 123, "
            "art. 13-A): ICMS e ISS são recolhidos fora do DAS, pelas regras do "
            "estado e do município; o valor acima é só a parte federal (na 6ª "
            "faixa a repartição da lei já dá 0% a ICMS e ISS). A regra do ano em "
            "que o sublimite é ultrapassado (art. 3º, §§ 11 a 15) não é calculada aqui.")
    return saida
