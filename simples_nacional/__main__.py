"""Linha de comando: python -m simples_nacional --ano 2026 --anexo I --rbt12 4500000 --receita-mes 375000"""

import argparse
import sys
from datetime import date
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from . import __version__
from .calculo import (
    LimiteExcedido,
    _avisos_receita_do_ano,
    _meses,
    _parcelas_acima_do_sublimite,
    _rbt12_primeiros_meses,
    aliquota_efetiva,
    aliquota_inicio_atividade,
    anexo_por_fator_r,
    avisos,
    avisos_inicio_atividade,
    faixa,
    fator_r,
    valor_devido,
    valor_devido_acima_do_sublimite,
    valor_devido_inicio_atividade,
)
from .formato import CENTAVO, ler_numero, porcentagem, reais
from .planejamento import planejar_fator_r
from .tabelas import LIMITE_RECEITA, SUBLIMITE_ICMS_ISS, vigencia


def _texto(percentual):
    return f"{percentual}".replace(".", ",") + "%"


def _efetiva_da_conta(efetiva, receita, valor):
    """A efetiva com as casas (4 ou mais) que fecham a conta da linha no centavo:
    R$ 1.000.000,00 × 13,1132% daria 131.132,00, não os 131.131,58 do mês."""
    for casas in range(4, 27):
        percentual = (efetiva * 100).quantize(Decimal(1).scaleb(-casas), ROUND_HALF_UP)
        if (receita * percentual / 100).quantize(CENTAVO, ROUND_HALF_UP) == valor:
            return _texto(percentual)
    return porcentagem(efetiva)


def _quinta_faixa(ano):
    """O que --icms-iss-no-das soma pela 5ª faixa no ano, com a regra."""
    if ano <= 2026:
        return "ICMS ou ISS pela 5ª faixa (Res. CGSN 140, art. 21, III, b)"
    tributos = "ICMS ou ISS e IBS" if ano <= 2032 else "IBS"
    return f"{tributos} pela 5ª faixa (Res. CGSN 140, art. 21, IV, redação da Res. CGSN 190/2026)"


def _fator_r_truncado(fator):
    """Fator R cortado na 4ª casa: 27,99999% arredondado mostraria 28,0000% ao
    lado do Anexo V."""
    return _texto((fator * 100).quantize(Decimal("0.0001"), ROUND_DOWN))


def _numero(texto):
    """ler_numero com o erro que o argparse mostra (uso: código 2)."""
    try:
        return ler_numero(texto)
    except ValueError as erro:
        raise argparse.ArgumentTypeError(str(erro)) from None


def _receitas(texto):
    """Receitas mensais separadas por ponto e vírgula: 30.000;50.000,00."""
    return [_numero(parte.strip()) for parte in texto.split(";")]


def _mes(texto):
    """Mês do calendário, 1 a 12, com o erro em português."""
    if not texto.strip().isdigit() or not 1 <= int(texto) <= 12:
        raise argparse.ArgumentTypeError(f"mês inválido: {texto!r} (de 1 a 12)")
    return int(texto)


_porcentagem = porcentagem  # nome da 0.3.0, mantido para quem já o importava


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m simples_nacional",
        description="Alíquota efetiva e valor do mês no Simples Nacional "
                    "(LC 123/2006, redação da LC 155/2016; de 2027 em diante, tabelas "
                    "da LC 214/2025). Estimativa: não "
                    "substitui o PGDAS-D nem o contador.")
    p.add_argument("--anexo", required=True,
                   help="I, II, III, IV, V, ou fator-r (escolhe III ou V pela folha)")
    p.add_argument("--rbt12", type=_numero,
                   help="receita bruta dos 12 meses anteriores ao de apuração, em R$ "
                        "(a partir de 2027, dos 12 antecedentes ao mês anterior)")
    p.add_argument("--receita-mes", type=_numero,
                   help="receita bruta do mês de apuração, em R$")
    p.add_argument("--receitas", type=_receitas,
                   help="início de atividade, no lugar de --rbt12 e --receita-mes: "
                        "receita de cada mês, do 1º de atividade até o de apuração, "
                        "separadas por ponto e vírgula (30.000;50.000)")
    p.add_argument("--mes-inicio", type=_mes, metavar="1-12",
                   help="com --receitas: mês do calendário em que a atividade começou, "
                        "para conferir o limite e o sublimite proporcionais do ano "
                        "(LC 123, art. 3º, §§ 2º e 11)")
    p.add_argument("--icms-iss-no-das", action="store_true",
                   help="com RBT12 acima de R$ 3,6 milhões e a receita do ano dentro do "
                        "sublimite: soma ICMS ou ISS pela 5ª faixa (Res. CGSN 140, art. 21, "
                        "III, b); desde 2027, também o IBS, e desde 2033 só o IBS (art. 21, "
                        "IV, redação da Res. CGSN 190/2026)")
    p.add_argument("--receita-ano", type=_numero,
                   help="até 2026, com --rbt12: receita bruta acumulada no ano-calendário "
                        "antes do mês de apuração, para o mês em que a receita do ano passa "
                        "do sublimite de R$ 3,6 milhões (Res. CGSN 140, art. 24)")
    p.add_argument("--folha12", type=_numero,
                   help="folha de salários dos 12 meses do RBT12 (art. 18, § 24), "
                        "obrigatória com --anexo fator-r")
    p.add_argument("--ano", type=int, default=date.today().year,
                   help="ano-calendário do mês de apuração (padrão: o ano corrente); "
                        "a tabela de 2027 e 2028 tem a 6ª faixa 0,1 ponto menor")
    p.add_argument("--version", action="version", version=f"simples-nacional {__version__}")
    a = p.parse_args(argv)
    if a.receitas is not None:
        if a.rbt12 is not None or a.receita_mes is not None:
            p.error("--receitas substitui --rbt12 e --receita-mes: use um ou outro")
    elif a.rbt12 is None or a.receita_mes is None:
        p.error("informe --rbt12 e --receita-mes, ou --receitas no início de atividade")
    elif a.mes_inicio is not None:
        p.error("--mes-inicio só vale com --receitas")
    if a.receitas is not None and a.icms_iss_no_das:
        p.error("--icms-iss-no-das só vale com --rbt12")
    if a.receitas is not None and a.receita_ano is not None:
        p.error("--receita-ano só vale com --rbt12")
    if a.receita_ano is not None and a.icms_iss_no_das:
        p.error("--receita-ano já decide o ICMS e o ISS pela receita do ano: "
                "não use --icms-iss-no-das junto")

    linhas = []
    anexo = a.anexo.upper()
    plano = None
    try:
        linhas.append(f"Tabela do ano-calendário {a.ano}: {vigencia(a.ano).fonte} "
                      "(para outro ano de apuração, use --ano)")
        if anexo != "FATOR-R" and a.folha12 is not None:
            p.error("--folha12 só vale com --anexo fator-r")
        if anexo == "FATOR-R":
            if a.receitas is not None:
                p.error("--anexo fator-r com --receitas não é calculado: informe o anexo (III ou V)")
            if a.folha12 is None:
                p.error("--anexo fator-r exige --folha12")
            anexo = anexo_por_fator_r(a.folha12, a.rbt12)
            linhas.append(
                f"Fator R: {_fator_r_truncado(fator_r(a.folha12, a.rbt12))} "
                f"-> Anexo {anexo} (LC 123, art. 18, § 5º-J: III se >= 28%)")
            if a.receita_ano is None:
                plano = planejar_fator_r(a.folha12, a.rbt12, a.receita_mes, ano=a.ano,
                                         icms_iss_no_das=a.icms_iss_no_das)
        if a.receitas is None:
            rbt12, receita_mes = a.rbt12, a.receita_mes
            f = faixa(anexo, rbt12, ano=a.ano)
            federal = aliquota_efetiva(anexo, rbt12, ano=a.ano)
            efetiva = aliquota_efetiva(anexo, rbt12, ano=a.ano, icms_iss_no_das=a.icms_iss_no_das)
            if a.receita_ano is None:
                valor = valor_devido(anexo, rbt12, receita_mes, ano=a.ano,
                                     icms_iss_no_das=a.icms_iss_no_das)
            else:
                valor = valor_devido_acima_do_sublimite(anexo, rbt12, receita_mes,
                                                        a.receita_ano, ano=a.ano)
                parcelas = _parcelas_acima_do_sublimite(anexo, rbt12, receita_mes,
                                                        a.receita_ano, a.ano)
        else:
            rbt12, regra = _rbt12_primeiros_meses(a.receitas, a.ano)
            receita_mes = a.receitas[-1]
            f = faixa(anexo, rbt12 or 1, ano=a.ano)  # sem RBT12: a 1ª faixa
            efetiva = federal = aliquota_inicio_atividade(anexo, a.receitas, ano=a.ano)
            valor = valor_devido_inicio_atividade(anexo, a.receitas, ano=a.ano)
            linhas.append(f"Início de atividade, {len(a.receitas)}º mês de atividade: {regra}"
                          + (f" = R$ {reais(rbt12)}" if rbt12 is not None else ""))
            if a.mes_inicio is not None:
                limites = avisos_inicio_atividade(a.receitas, a.mes_inicio, ano=a.ano)
            elif sum(a.receitas[:12]) > SUBLIMITE_ICMS_ISS / 12 * len(a.receitas[:12]):
                limites = [
                    f"R$ {reais(sum(a.receitas[:12]))} em {_meses(len(a.receitas[:12]))} passa "
                    f"de R$ {reais(SUBLIMITE_ICMS_ISS / 12)} por mês. No ano de início de "
                    f"atividade, o limite é R$ {reais(LIMITE_RECEITA / 12)} e o sublimite "
                    f"R$ {reais(SUBLIMITE_ICMS_ISS / 12)}, vezes os meses do início até "
                    "dezembro (LC 123, art. 3º, §§ 2º e 11): informe --mes-inicio para "
                    "conferir."]
            else:
                limites = []
    except LimiteExcedido as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2
    except (ValueError, TypeError) as erro:
        p.error(str(erro))

    linhas += [
        f"Anexo {anexo}, {f.numero}ª faixa (até R$ {reais(f.teto)}): "
        f"alíquota nominal {porcentagem(f.aliquota)}, "
        f"parcela a deduzir R$ {reais(f.parcela_deduzir)}",
        f"Alíquota efetiva: {porcentagem(efetiva)} "
        + ("= nominal da 1ª faixa" if rbt12 is None
           else "= (RBT12 × Aliq - PD) / RBT12 (LC 123, art. 18, § 1º-A)" if efetiva == federal
           else f"= {porcentagem(federal)} da 6ª faixa, só federal, + "
                f"{porcentagem(efetiva - federal)} de {_quinta_faixa(a.ano)}"),
    ]
    if a.receita_ano is None:
        linhas.append(f"Valor do mês: R$ {reais(valor)} "
                      f"= R$ {reais(receita_mes)} × {_efetiva_da_conta(efetiva, receita_mes, valor)}")
    else:
        linhas.append(f"Receita do ano antes do mês: R$ {reais(a.receita_ano)}; o mês se divide "
                      "pelo sublimite e pelo limite (Res. CGSN 140, art. 24):")
        icms_iss = ("" if a.receita_ano > SUBLIMITE_ICMS_ISS * Decimal("1.2")
                    else " + ICMS ou ISS pela 5ª faixa em R$ 3.600.000,00")
        for (parcela, aliquota), nome in zip(parcelas, (
                "dentro do sublimite, pela alíquota efetiva (§ 5º)",
                f"acima do sublimite: federais pelo art. 21{icms_iss} (inciso I; § 6º)",
                "acima de R$ 4.800.000,00: federais da 6ª faixa em R$ 4.800.000,00"
                f"{icms_iss} (inciso II; § 7º)")):
            if parcela:
                linhas.append(f"  R$ {reais(parcela)} {nome}: × {porcentagem(aliquota)}")
        linhas.append(f"Valor do mês: R$ {reais(valor)} = soma das parcelas, "
                      "arredondada no centavo")
    if plano is not None:
        diferenca = plano.diferenca_das
        linhas += [
            f"Folha de 12 meses para 28%: R$ {reais(plano.folha_minima)}; "
            + ("a de hoje já chega" if plano.anexo == "III"
               else f"faltam R$ {reais(plano.folha_que_falta)}"),
            f"Valor do mês no Anexo V: R$ {reais(plano.das_anexo_v)}; no Anexo III: "
            f"R$ {reais(plano.das_anexo_iii)}; "
            + (f"o III sai R$ {reais(diferenca)} mais barato" if diferenca > 0
               else f"o V sai R$ {reais(-diferenca)} mais barato" if diferenca < 0
               else "o mesmo valor"),
            "Aviso: a diferença é só no DAS. O pró-labore a mais paga a contribuição "
            "previdenciária do sócio e pode pagar IRPF, que dependem da pessoa: nada "
            "disso está descontado.",
        ]
    if rbt12 is not None and a.receita_ano is not None:
        linhas += [f"Aviso: {texto}"
                   for texto in _avisos_receita_do_ano(receita_mes, a.receita_ano)]
    elif rbt12 is not None:
        linhas += [f"Aviso: {texto}"
                   for texto in avisos(rbt12, ano=a.ano, icms_iss_no_das=a.icms_iss_no_das)]
    if a.receitas is not None:
        linhas += [f"Aviso: {texto}" for texto in limites]
    linhas.append("Estimativa conferida contra a tabela da lei: não substitui o PGDAS-D nem o contador.")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
