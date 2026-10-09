"""Alíquota efetiva, valor do mês, Fator R e limites (LC 123/2006, art. 18).

Decimal do começo ao fim; o único arredondamento é o do valor do mês, em
centavos com ROUND_HALF_UP (a lei não fixa regra: convenção da biblioteca).
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .formato import CENTAVO, reais
from .tabelas import FATOR_R_MINIMO, LIMITE_RECEITA, SUBLIMITE_ICMS_ISS, vigencia

# A partir deste ano-calendário o RBT12 é o dos 12 meses antecedentes ao mês
# anterior ao de apuração (LC 214, art. 517, nova redação da LC 123, art. 18,
# § 1º; efeitos em 01/01/2027, art. 544, III; Res. CGSN 190/2026).
DEFASAGEM_DESDE = 2027


class LimiteExcedido(ValueError):
    """RBT12 acima de R$ 4,8 milhões: nenhuma alíquota do Simples se aplica."""


def para_decimal(valor, nome):
    """Decimal exato a partir de Decimal, int ou str; float e bool são recusados.

    `nome` abre a mensagem de erro (`rbt12: não é número: 'abc'`).
    """
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


_decimal = para_decimal  # nome da 0.3.0, mantido para quem já o importava


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
    `rbt12` é a receita dos 12 meses anteriores ao de apuração; a partir de
    2027, dos 12 antecedentes ao mês anterior (LC 123, art. 18, § 1º, na
    redação da LC 214): para apurar março, de fevereiro do ano anterior a
    janeiro.
    """
    faixas = _anexo(anexo, ano)
    rbt12 = _decimal(rbt12, "rbt12")
    if rbt12 <= 0:
        raise ValueError(
            "rbt12 tem de ser positivo; nos primeiros meses de atividade use "
            "aliquota_inicio_atividade (LC 123, art. 18, § 2º; Res. CGSN 140, art. 22)")
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
    """Folha dos últimos 12 meses ÷ RBT12 (art. 18, §§ 5º-K e 24).

    A partir de 2027 a folha também é a dos 12 meses antecedentes ao mês
    anterior ao de apuração (§ 24, redação da LC 214).
    """
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
    que entram na média (1 a 11): até 2026, os anteriores ao de apuração; a
    partir de 2027, os antecedentes ao mês anterior. Para o mês a mês,
    inclusive o primeiro, use aliquota_inicio_atividade.
    """
    receita_acumulada = _decimal(receita_acumulada, "receita_acumulada")
    if isinstance(meses, bool) or not isinstance(meses, int) or not 1 <= meses <= 11:
        raise ValueError("meses tem de ser int de 1 a 11; com 12 ou mais use o RBT12 real")
    if receita_acumulada < 0:
        raise ValueError("receita_acumulada não pode ser negativa")
    return receita_acumulada * 12 / meses


def _rbt12_primeiros_meses(receitas, ano):
    """(RBT12, regra) do mês de apuração, o último de `receitas`.

    RBT12 None quer dizer alíquota nominal da 1ª faixa.
    """
    vigencia(ano)
    if isinstance(receitas, (str, bytes)) or not hasattr(receitas, "__len__"):
        raise TypeError("receitas: lista com a receita de cada mês, do 1º de atividade ao de apuração")
    receitas = [_decimal(r, "receitas") for r in receitas]
    if any(r < 0 for r in receitas):
        raise ValueError("receitas: nenhum mês pode ser negativo")
    mes = len(receitas)
    if ano < DEFASAGEM_DESDE:
        ultimo, anteriores = 12, receitas[:-1] or receitas
        regra = ("receita do próprio mês × 12 (Res. CGSN 140, art. 22, § 2º)" if mes == 1 else
                 "média dos meses anteriores × 12 (Res. CGSN 140, art. 22, § 3º)")
    else:
        ultimo, anteriores = 13, receitas[:-2]
        regra = "média dos meses antes do mês anterior × 12 (Res. CGSN 140, art. 22, § 2º, II, redação da Res. CGSN 190/2026)"
    if not 1 <= mes <= ultimo:
        raise ValueError(f"receitas: de 1 a {ultimo} meses de atividade em {ano}; depois use o RBT12 real")
    if not anteriores:
        return None, "1º e 2º mês: alíquota da 1ª faixa (Res. CGSN 140, art. 22, § 2º, I, redação da Res. CGSN 190/2026)"
    rbt12 = sum(anteriores) * 12 / len(anteriores)
    if rbt12 == 0:
        return None, "receita zero na média: alíquota da 1ª faixa (convenção da biblioteca)"
    return rbt12, regra


def aliquota_inicio_atividade(anexo, receitas, *, ano):
    """Alíquota efetiva nos primeiros meses de atividade (Res. CGSN 140, art. 22).

    `receitas` traz a receita de cada mês, do 1º de atividade até o de
    apuração, inclusive. Até 2026: 1º mês, receita do próprio mês × 12; do 2º
    ao 12º, média dos meses anteriores × 12. A partir de 2027 (Res. CGSN
    190/2026): 1º e 2º mês, alíquota da 1ª faixa; do 3º ao 13º, média dos
    meses antecedentes ao mês anterior × 12. Média zero: 1ª faixa (a fórmula
    não se define com RBT12 zero; convenção da biblioteca).
    """
    faixas = _anexo(anexo, ano)
    rbt12, _ = _rbt12_primeiros_meses(receitas, ano)
    if rbt12 is None:
        return faixas[0].aliquota
    return aliquota_efetiva(anexo, rbt12, ano=ano)


def valor_devido_inicio_atividade(anexo, receitas, *, ano):
    """Receita do mês de apuração (a última) × aliquota_inicio_atividade, em centavos."""
    efetiva = aliquota_inicio_atividade(anexo, receitas, ano=ano)
    return (_decimal(receitas[-1], "receitas") * efetiva).quantize(CENTAVO, ROUND_HALF_UP)


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
