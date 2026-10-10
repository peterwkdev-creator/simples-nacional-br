"""Alíquota efetiva, valor do mês, Fator R e limites (LC 123/2006, art. 18).

Decimal do começo ao fim; o único arredondamento é o do valor do mês, em
centavos com ROUND_HALF_UP (a lei não fixa regra: convenção da biblioteca).
As contas correm num contexto Decimal fixo (28 dígitos), o mesmo seja qual
for o getcontext() de quem chama.
"""

from collections.abc import Sequence
from decimal import Decimal, ROUND_HALF_UP

from .formato import CENTAVO, _contexto_fixo, para_decimal, reais
from .tabelas import (FATOR_R_MINIMO, ICMS_ISS_POR_FAIXA, LIMITE_RECEITA, SUBLIMITE_ICMS_ISS,
                      TETO_ISS, quinta_faixa_icms_iss_ibs, vigencia)

# A partir deste ano-calendário o RBT12 é o dos 12 meses antecedentes ao mês
# anterior ao de apuração (LC 214, art. 517, nova redação da LC 123, art. 18,
# § 1º; efeitos em 01/01/2027, art. 544, III; Res. CGSN 190/2026).
DEFASAGEM_DESDE = 2027


class LimiteExcedido(ValueError):
    """RBT12 acima de R$ 4,8 milhões: nenhuma alíquota do Simples se aplica."""




def _anexo(anexo, ano):
    anexos = vigencia(ano).anexos
    chave = anexo.upper() if isinstance(anexo, str) else None
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
    rbt12 = para_decimal(rbt12, "rbt12")
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


def _icms_iss_quinta_faixa(anexo, rbt12, ano):
    """Percentual efetivo do ICMS ou do ISS (e do IBS) com RBT12 acima do sublimite.

    {[(RBT12 × nominal da 5ª faixa) − PD da 5ª faixa] / RBT12} × repartição
    da 5ª faixa: até 2026, a do ICMS ou do ISS (Res. CGSN 140, art. 21, III,
    b); desde 2027, a do ICMS ou do ISS mais a do IBS, da tabela do ano na
    LC 214 (art. 21, IV, redação da Res. CGSN 190/2026). O teto de 5% do ISS
    (inciso III, a) só muda a repartição: a diferença passa aos outros
    tributos e o total fica o mesmo.
    """
    quinta = _anexo(anexo, ano)[4]
    efetiva = (rbt12 * quinta.aliquota - quinta.parcela_deduzir) / rbt12
    icms_iss, ibs = quinta_faixa_icms_iss_ibs(anexo, ano=ano)
    return efetiva * (icms_iss + ibs)


@_contexto_fixo
def aliquota_efetiva(anexo, rbt12, *, ano, icms_iss_no_das=False):
    """(RBT12 × Aliq − PD) / RBT12, LC 123, art. 18, § 1º-A. Sem arredondar.

    Acima do sublimite de R$ 3,6 milhões (6ª faixa) a repartição da lei dá
    0% a ICMS e ISS (e, desde 2027, ao IBS): o resultado é só a parte
    federal. Com `icms_iss_no_das=True` soma ICMS ou ISS pela 5ª faixa (Res.
    CGSN 140, art. 21, III, b) e, desde 2027, também o IBS (art. 21, IV,
    redação da Res. CGSN 190/2026); de 2033 em diante, só o IBS. Isso vale
    enquanto a receita acumulada no ano não passar do sublimite e a empresa
    não estiver impedida (art. 12; ver avisos). Até o sublimite a opção não
    muda nada: esses tributos já estão na alíquota.
    """
    if not isinstance(icms_iss_no_das, bool):
        raise TypeError(f"icms_iss_no_das: esperado bool, veio {type(icms_iss_no_das).__name__}")
    f = faixa(anexo, rbt12, ano=ano)
    rbt12 = Decimal(rbt12)
    efetiva = (rbt12 * f.aliquota - f.parcela_deduzir) / rbt12
    if icms_iss_no_das and rbt12 > SUBLIMITE_ICMS_ISS:
        efetiva += _icms_iss_quinta_faixa(anexo, rbt12, ano)
    return efetiva


@_contexto_fixo
def valor_devido(anexo, rbt12, receita_mes, *, ano, icms_iss_no_das=False):
    """Receita do mês × alíquota efetiva (art. 18, § 3º), em centavos.

    Com RBT12 acima do sublimite de R$ 3,6 milhões é só a parte federal: se
    ICMS e ISS (e o IBS, desde 2027) saem do DAS ou seguem nele depende da
    receita acumulada no ano (ver avisos). `icms_iss_no_das=True` os soma
    pela 5ª faixa, como em aliquota_efetiva; o mês em que a receita do ano
    passa do sublimite é valor_devido_acima_do_sublimite. Abaixo do
    sublimite, a partir de 2027 é o DAS cheio, com
    as parcelas de CBS e IBS; quem optar pelo regime regular desses tributos
    (LC 123, art. 13, § 9º) as paga fora e o DAS fica menor.
    """
    receita_mes = para_decimal(receita_mes, "receita_mes")
    if receita_mes < 0:
        raise ValueError("receita_mes não pode ser negativa")
    efetiva = aliquota_efetiva(anexo, rbt12, ano=ano, icms_iss_no_das=icms_iss_no_das)
    return (receita_mes * efetiva).quantize(CENTAVO, ROUND_HALF_UP)


def _icms_iss_da_faixa(anexo, rbt12, ano):
    """ICMS ou ISS dentro da alíquota efetiva da faixa do RBT12, até 2026.

    Repartição da faixa (LC 123, Anexos I a V); nos Anexos III e IV, até o
    teto de 5% do ISS (nota dos anexos; Res. CGSN 140, art. 21, III, a). Na
    6ª faixa, zero.
    """
    f = faixa(anexo, rbt12, ano=ano)
    if f.numero == 6:
        return Decimal(0)
    parte = aliquota_efetiva(anexo, rbt12, ano=ano) * ICMS_ISS_POR_FAIXA[anexo.upper()][f.numero - 1]
    if anexo.upper() in ("III", "IV"):
        parte = min(parte, TETO_ISS)
    return parte


@_contexto_fixo
def valor_devido_acima_do_sublimite(anexo, rbt12, receita_mes, receita_ano, *, ano):
    """Valor do mês em que a receita do ano passa do sublimite, em centavos, até 2026.

    Res. CGSN 140, art. 24. `receita_ano` é a receita bruta acumulada no
    ano-calendário antes do mês de apuração. A receita do mês se divide em:

    - a parcela dentro do sublimite de R$ 3,6 milhões: alíquota efetiva do
      art. 21, com ICMS ou ISS (§ 5º);
    - a que passa do sublimite sem passar de R$ 4,8 milhões: tributos
      federais pelo art. 21 mais ICMS ou ISS de {[(3.600.000 × nominal da 5ª
      faixa) − PD da 5ª] / 3.600.000} × repartição do ICMS ou ISS da 5ª
      (inciso I; § 6º);
    - a que passa de R$ 4,8 milhões: tributos federais de {[(4.800.000 ×
      nominal da 6ª) − PD da 6ª] / 4.800.000} (a 6ª faixa é toda federal)
      mais o mesmo ICMS ou ISS (inciso II; § 7º).

    Os tributos federais pelo art. 21 são a alíquota efetiva menos o ICMS ou
    ISS da faixa do RBT12, que nos Anexos III e IV vai até 5% (leitura da
    biblioteca: a diferença é federal, art. 21, III, a); na 6ª faixa, a
    alíquota inteira. Se a receita do ano antes do mês já passou do
    sublimite em mais de 20%, o impedimento vale desde este mês (LC 123,
    art. 20, §§ 1º e 1º-A; Res. CGSN 140, art. 12) e não há ICMS nem ISS;
    se passou do limite em mais de 20%, a exclusão vale desde este mês
    (art. 3º, § 9º-A) e é LimiteExcedido. Fora do escopo: o ano de início de
    atividade (§ 1º) e a receita de exportação em separado (§ 8º). Um só
    arredondamento, em centavos, ROUND_HALF_UP.
    """
    partes = _parcelas_acima_do_sublimite(anexo, rbt12, receita_mes, receita_ano, ano)
    return sum((p * a for p, a in partes), Decimal(0)).quantize(CENTAVO, ROUND_HALF_UP)


@_contexto_fixo
def _parcelas_acima_do_sublimite(anexo, rbt12, receita_mes, receita_ano, ano):
    """(parcela, alíquota) dentro do sublimite, entre ele e o limite e acima do limite."""
    vigencia(ano)
    if ano > 2026:
        raise ValueError(
            "o mês em que a receita do ano passa do sublimite (Res. CGSN 140, art. 24) "
            "só é calculado até 2026: a partir de 2027 o IBS entra na conta e a "
            "redação da Res. CGSN 190/2026 não é calculada aqui")
    receita_mes = para_decimal(receita_mes, "receita_mes")
    receita_ano = para_decimal(receita_ano, "receita_ano")
    if receita_mes < 0 or receita_ano < 0:
        raise ValueError("receita_mes e receita_ano não podem ser negativas")
    if receita_ano > LIMITE_RECEITA * Decimal("1.2"):
        raise LimiteExcedido(
            f"receita do ano antes do mês de R$ {reais(receita_ano)}, mais de 20% acima do "
            f"limite de R$ {reais(LIMITE_RECEITA)}: a exclusão do Simples Nacional já vale "
            "neste mês (LC 123, art. 3º, §§ 9º e 9º-A).")
    total = receita_ano + receita_mes
    acima_sub = min(max(total - SUBLIMITE_ICMS_ISS, Decimal(0)), receita_mes)
    acima_lim = min(max(total - LIMITE_RECEITA, Decimal(0)), receita_mes)
    dentro = receita_mes - acima_sub
    rbt12 = para_decimal(rbt12, "rbt12")
    quinta, sexta = _anexo(anexo, ano)[4], _anexo(anexo, ano)[5]
    if receita_ano > SUBLIMITE_ICMS_ISS * Decimal("1.2"):
        icms_iss = Decimal(0)
    else:
        icms_iss = ((SUBLIMITE_ICMS_ISS * quinta.aliquota - quinta.parcela_deduzir)
                    / SUBLIMITE_ICMS_ISS * ICMS_ISS_POR_FAIXA[anexo.upper()][4])
    federal = aliquota_efetiva(anexo, rbt12, ano=ano) - _icms_iss_da_faixa(anexo, rbt12, ano)
    federal_limite = (LIMITE_RECEITA * sexta.aliquota - sexta.parcela_deduzir) / LIMITE_RECEITA
    return [(dentro, aliquota_efetiva(anexo, rbt12, ano=ano, icms_iss_no_das=True)),
            (acima_sub - acima_lim, federal + icms_iss),
            (acima_lim, federal_limite + icms_iss)]


def _avisos_receita_do_ano(receita_mes, receita_ano):
    """Efeito do sublimite e do limite nos meses seguintes (LC 123, arts. 3º e 20)."""
    total = receita_ano + receita_mes
    receita = f"Receita do ano com este mês de R$ {reais(total)}"
    saida = []
    if receita_ano > SUBLIMITE_ICMS_ISS * Decimal("1.2"):
        saida.append(
            f"Receita do ano antes do mês de R$ {reais(receita_ano)}, mais de 20% acima do "
            f"sublimite de R$ {reais(SUBLIMITE_ICMS_ISS)}: o impedimento já vale neste mês e o "
            "valor acima não tem ICMS nem ISS (LC 123, art. 20, § 1º; Res. CGSN 140, art. 12).")
    elif total > SUBLIMITE_ICMS_ISS * Decimal("1.2"):
        saida.append(
            f"{receita}, mais de 20% acima do sublimite de R$ {reais(SUBLIMITE_ICMS_ISS)}: "
            "a partir do mês seguinte, ICMS e ISS saem do DAS e são recolhidos fora, pelas "
            "regras de cada ente (LC 123, art. 20, § 1º; Res. CGSN 140, art. 12).")
    elif total > SUBLIMITE_ICMS_ISS:
        saida.append(
            f"{receita}, até 20% acima do sublimite de R$ {reais(SUBLIMITE_ICMS_ISS)}: ICMS e "
            "ISS saem do DAS a partir de janeiro do ano seguinte (LC 123, art. 20, § 1º-A; "
            "Res. CGSN 140, art. 12); até lá, os meses seguintes também seguem o art. 24.")
    if total > LIMITE_RECEITA * Decimal("1.2"):
        saida.append(
            f"{receita}, mais de 20% acima do limite de R$ {reais(LIMITE_RECEITA)}: exclusão "
            "do Simples Nacional a partir do mês seguinte (LC 123, art. 3º, § 9º).")
    elif total > LIMITE_RECEITA:
        saida.append(
            f"{receita}, até 20% acima do limite de R$ {reais(LIMITE_RECEITA)}: exclusão do "
            "Simples Nacional a partir de janeiro do ano seguinte (LC 123, art. 3º, § 9º-A).")
    return saida


@_contexto_fixo
def fator_r(folha12, rbt12):
    """Folha dos últimos 12 meses ÷ RBT12 (art. 18, §§ 5º-K e 24).

    A partir de 2027 a folha também é a dos 12 meses antecedentes ao mês
    anterior ao de apuração (§ 24, redação da LC 214).
    """
    folha12 = para_decimal(folha12, "folha12")
    rbt12 = para_decimal(rbt12, "rbt12")
    if folha12 < 0:
        raise ValueError("folha12 não pode ser negativa")
    if rbt12 <= 0:
        raise ValueError("rbt12 tem de ser positivo")
    return folha12 / rbt12


def anexo_por_fator_r(folha12, rbt12):
    """'III' se o Fator R for 28% ou mais (art. 18, § 5º-J), senão 'V'. Sem arredondar."""
    return "III" if fator_r(folha12, rbt12) >= FATOR_R_MINIMO else "V"


@_contexto_fixo
def rbt12_inicio_atividade(receita_acumulada, meses):
    """RBT12 de empresa com menos de 12 meses de atividade.

    O art. 18, § 2º proporcionaliza as faixas por meses/12; anualizar a
    receita por 12/meses dá a mesma alíquota efetiva. `meses` conta os meses
    que entram na média (1 a 11): até 2026, os anteriores ao de apuração; a
    partir de 2027, os antecedentes ao mês anterior. Para o mês a mês,
    inclusive o primeiro, use aliquota_inicio_atividade.
    """
    receita_acumulada = para_decimal(receita_acumulada, "receita_acumulada")
    if isinstance(meses, bool) or not isinstance(meses, int) or not 1 <= meses <= 11:
        raise ValueError("meses tem de ser int de 1 a 11; com 12 ou mais use o RBT12 real")
    if receita_acumulada < 0:
        raise ValueError("receita_acumulada não pode ser negativa")
    return receita_acumulada * 12 / meses


@_contexto_fixo
def _rbt12_primeiros_meses(receitas, ano):
    """(RBT12, regra) do mês de apuração, o último de `receitas`.

    RBT12 None quer dizer alíquota nominal da 1ª faixa.
    """
    vigencia(ano)
    if isinstance(receitas, (str, bytes)) or not isinstance(receitas, Sequence):
        raise TypeError("receitas: lista com a receita de cada mês, do 1º de atividade ao de apuração")
    receitas = [para_decimal(r, "receitas") for r in receitas]
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


@_contexto_fixo
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


@_contexto_fixo
def valor_devido_inicio_atividade(anexo, receitas, *, ano):
    """Receita do mês de apuração (a última) × aliquota_inicio_atividade, em centavos."""
    efetiva = aliquota_inicio_atividade(anexo, receitas, ano=ano)
    return (para_decimal(receitas[-1], "receitas") * efetiva).quantize(CENTAVO, ROUND_HALF_UP)


def _aviso_sublimite(ano, icms_iss_no_das=False):
    limite = f"R$ {reais(SUBLIMITE_ICMS_ISS)}"
    if ano <= 2026:
        lei, regra = "LC 123, art. 13-A", "Res. CGSN 140, art. 21, III, b"
        quais, seguem, saem = "ICMS e ISS", "seguem", "ICMS e ISS saem"
        soma = "ICMS ou ISS"
        federal = "só a parte federal (na 6ª faixa a repartição da lei dá 0% a ICMS e ISS)"
        mes = ("o mês em que a receita do ano passa do sublimite (art. 24) é "
               "valor_devido_acima_do_sublimite (na linha de comando, --receita-ano)")
    else:
        if ano <= 2032:
            lei = "LC 123, art. 13-A, na redação da LC 214/2025, art. 517"
            quais, seguem, saem = "ICMS, ISS e IBS", "seguem", "ICMS, ISS e IBS saem"
            soma = "ICMS ou ISS e IBS"
        else:
            lei = "LC 123, art. 13-A, na redação da LC 214/2025, art. 518"
            quais, seguem, saem = "o IBS", "segue", "o IBS sai"
            soma = "o IBS"
        regra = "Res. CGSN 140, art. 21, IV, redação da Res. CGSN 190/2026"
        federal = "só a parte federal, com a CBS"
        mes = "o mês em que a receita do ano passa do sublimite (art. 24) não é calculado aqui"
    pronome = "lo" if seguem == "segue" else "los"
    if icms_iss_no_das:
        return (
            f"RBT12 acima do sublimite de {limite} ({lei}): o valor acima soma à parte "
            f"federal {soma} pela 5ª faixa "
            f"({regra}), como pedido. Isso só vale enquanto a receita acumulada no "
            f"ano-calendário não passar de {limite} e a empresa não estiver impedida de "
            f"recolhê-{pronome} pelo Simples (art. 12); senão, {saem} do DAS e o DAS é só a "
            f"parte federal. {mes[0].upper()}{mes[1:]}.")
    return (
        f"RBT12 acima do sublimite de {limite} ({lei}): o valor acima é {federal}. "
        f"{quais[0].upper()}{quais[1:]} {seguem} no DAS pela 5ª faixa ({regra}) enquanto a "
        f"receita acumulada no ano-calendário não passar de {limite} e a empresa não "
        f"estiver impedida de recolhê-{pronome} pelo Simples (art. 12): aí o DAS é maior que o "
        "valor acima, e icms_iss_no_das=True (na linha de comando, --icms-iss-no-das) o "
        f"calcula. Se passou, {saem} do DAS e "
        f"{'é recolhido' if seguem == 'segue' else 'são recolhidos'} fora, pelas regras de cada "
        f"ente; {mes}.")


def avisos(rbt12, *, ano, icms_iss_no_das=False):
    """Avisos sobre os limites.

    O texto do sublimite muda com o ano-calendário de apuração: até 2026, ICMS e
    ISS; de 2027 a 2032, também o IBS (LC 214/2025, art. 517); de 2033 em
    diante, só o IBS (art. 518).
    `icms_iss_no_das=True` troca o texto pelo do valor com eles pela 5ª faixa.
    RBT12 zero ou negativo é ValueError, como em faixa.
    """
    rbt12 = para_decimal(rbt12, "rbt12")
    if rbt12 <= 0:
        raise ValueError("rbt12 tem de ser positivo")
    vigencia(ano)  # mesma validação do ano dos cálculos
    saida = []
    if rbt12 > LIMITE_RECEITA:
        saida.append(
            f"RBT12 acima de R$ {reais(LIMITE_RECEITA)}: fora do Simples Nacional "
            "(LC 123, art. 3º, II).")
    elif rbt12 > SUBLIMITE_ICMS_ISS:
        saida.append(_aviso_sublimite(ano, icms_iss_no_das))
    return saida


def _meses(n):
    return "1 mês" if n == 1 else f"{n} meses"


def _efeito_do_excesso(acumulada, teto, nome):
    """LC 123, art. 3º, §§ 10, 12 e 13: mais de 20% acima retroage ao início."""
    if acumulada - teto > teto * Decimal("0.2"):
        return f"desde o início de atividade, porque o excesso passa de 20% do {nome}"
    return f"a partir de 1º de janeiro do ano seguinte, porque o excesso não passa de 20% do {nome}"


@_contexto_fixo
def avisos_inicio_atividade(receitas, mes_inicio, *, ano):
    """Avisos do limite e do sublimite proporcionais no ano de início de atividade.

    No ano-calendário em que a atividade começa, o limite é R$ 400.000,00 e o
    sublimite R$ 300.000,00, multiplicados pelos meses do início até
    dezembro, fração de mês como mês inteiro (LC 123, art. 3º, §§ 2º e 11;
    Res. CGSN 140, arts. 3º e 9º, § 2º). `receitas` e `ano` são os de
    aliquota_inicio_atividade; `mes_inicio` é o mês do calendário (1 a 12) em
    que a atividade começou. Somam-se só as receitas desse ano: as
    13 - mes_inicio primeiras. Excesso de mais de 20% retroage ao início; de
    até 20%, vale a partir do ano seguinte (art. 3º, §§ 10, 12 e 13).
    """
    if isinstance(mes_inicio, bool) or not isinstance(mes_inicio, int) or not 1 <= mes_inicio <= 12:
        raise ValueError("mes_inicio tem de ser int de 1 a 12 (o mês do calendário)")
    _rbt12_primeiros_meses(receitas, ano)  # mesma validação da lista e do ano
    meses = 13 - mes_inicio
    ano_inicio = ano if len(receitas) <= meses else ano - 1
    acumulada = sum((para_decimal(r, "receitas") for r in receitas[:meses]), Decimal(0))
    limite, sublimite = LIMITE_RECEITA / 12 * meses, SUBLIMITE_ICMS_ISS / 12 * meses
    receita = (f"Receita acumulada no ano de início de atividade ({ano_inicio}) de "
               f"R$ {reais(acumulada)}")
    if acumulada > limite:
        return [
            f"{receita}, acima do limite proporcional de R$ {reais(limite)} "
            f"(R$ {reais(LIMITE_RECEITA / 12)} × {_meses(meses)}, do início a dezembro; "
            "LC 123, art. 3º, § 2º): fora do Simples Nacional "
            f"{_efeito_do_excesso(acumulada, limite, 'limite')} "
            "(art. 3º, §§ 10 e 12; art. 31, III)."]
    if acumulada > sublimite:
        if ano_inicio <= 2026:
            tributos, fora = "ICMS e ISS saem", "são recolhidos"
        elif ano_inicio <= 2032:
            tributos, fora = "ICMS, ISS e IBS saem", "são recolhidos"
        else:
            tributos, fora = "o IBS sai", "é recolhido"
        return [
            f"{receita}, acima do sublimite proporcional de R$ {reais(sublimite)} "
            f"(R$ {reais(SUBLIMITE_ICMS_ISS / 12)} × {_meses(meses)}, do início a "
            f"dezembro; LC 123, art. 3º, § 11): {tributos} do DAS "
            f"{_efeito_do_excesso(acumulada, sublimite, 'sublimite')} "
            f"(art. 3º, § 13) e {fora} pelas regras de cada ente; isso não é "
            "calculado aqui."]
    return []
