"""Linha de comando: python -m simples_nacional --ano 2026 --anexo I --rbt12 4500000 --receita-mes 375000"""

import argparse
import re
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .calculo import (
    LimiteExcedido,
    _rbt12_primeiros_meses,
    aliquota_efetiva,
    aliquota_inicio_atividade,
    anexo_por_fator_r,
    avisos,
    faixa,
    fator_r,
    reais,
    valor_devido,
    valor_devido_inicio_atividade,
)
from .tabelas import vigencia


_MILHAR = re.compile(r"-?\d{1,3}(\.\d{3})+(,\d+)?")  # 360.000 e 1.000,50
_VIRGULA = re.compile(r"-?\d+(,\d+)?")                # 1000,50
_PONTO = re.compile(r"-?\d+(\.\d{1,2})?")             # 4500000.00


def _numero(texto):
    """Aceita 4500000, 4500000.00, 1000,50, 1.000,50 e 360.000 (milhar).

    Ponto seguido de três dígitos é milhar, como se escreve no Brasil; o que
    não casa com nenhum formato (1,000.50, 1.0000) é recusado, não adivinhado.
    """
    if _MILHAR.fullmatch(texto) or _VIRGULA.fullmatch(texto):
        normal = texto.replace(".", "").replace(",", ".")
    elif _PONTO.fullmatch(texto):
        normal = texto
    else:
        raise argparse.ArgumentTypeError(
            f"número inválido: {texto!r} (use 1.000,50 ou 1000.50)")
    return Decimal(normal)


def _receitas(texto):
    """Receitas mensais separadas por ponto e vírgula: 30.000;50.000,00."""
    return [_numero(parte.strip()) for parte in texto.split(";")]


def _porcentagem(fracao):
    texto = f"{(fracao * 100).quantize(Decimal('0.0001'), ROUND_HALF_UP)}"
    return texto.replace(".", ",") + "%"


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m simples_nacional",
        description="Alíquota efetiva e valor do mês no Simples Nacional "
                    "(LC 123/2006, redação da LC 155/2016). Estimativa: não "
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
    p.add_argument("--folha12", type=_numero,
                   help="folha de salários dos 12 meses do RBT12 (art. 18, § 24), "
                        "obrigatória com --anexo fator-r")
    p.add_argument("--ano", type=int, default=date.today().year,
                   help="ano-calendário do mês de apuração (padrão: o ano corrente); "
                        "a tabela de 2027 e 2028 tem a 6ª faixa 0,1 ponto menor")
    a = p.parse_args(argv)
    if a.receitas is not None:
        if a.rbt12 is not None or a.receita_mes is not None:
            p.error("--receitas substitui --rbt12 e --receita-mes: use um ou outro")
    elif a.rbt12 is None or a.receita_mes is None:
        p.error("informe --rbt12 e --receita-mes, ou --receitas no início de atividade")

    linhas = []
    anexo = a.anexo.upper()
    try:
        linhas.append(f"Tabela do ano-calendário {a.ano}: {vigencia(a.ano).fonte} "
                      "(para outro ano de apuração, use --ano)")
        if anexo == "FATOR-R":
            if a.receitas is not None:
                p.error("--anexo fator-r com --receitas não é calculado: informe o anexo (III ou V)")
            if a.folha12 is None:
                p.error("--anexo fator-r exige --folha12")
            anexo = anexo_por_fator_r(a.folha12, a.rbt12)
            linhas.append(
                f"Fator R: {_porcentagem(fator_r(a.folha12, a.rbt12))} "
                f"-> Anexo {anexo} (LC 123, art. 18, § 5º-J: III se >= 28%)")
        if a.receitas is None:
            rbt12, receita_mes = a.rbt12, a.receita_mes
            f = faixa(anexo, rbt12, ano=a.ano)
            efetiva = aliquota_efetiva(anexo, rbt12, ano=a.ano)
            valor = valor_devido(anexo, rbt12, receita_mes, ano=a.ano)
        else:
            rbt12, regra = _rbt12_primeiros_meses(a.receitas, a.ano)
            receita_mes = a.receitas[-1]
            f = faixa(anexo, rbt12 or 1, ano=a.ano)  # sem RBT12: a 1ª faixa
            efetiva = aliquota_inicio_atividade(anexo, a.receitas, ano=a.ano)
            valor = valor_devido_inicio_atividade(anexo, a.receitas, ano=a.ano)
            linhas.append(f"Início de atividade, {len(a.receitas)}º mês de atividade: {regra}"
                          + (f" = R$ {reais(rbt12)}" if rbt12 is not None else ""))
    except LimiteExcedido as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2
    except (ValueError, TypeError) as erro:
        p.error(str(erro))

    linhas += [
        f"Anexo {anexo}, {f.numero}ª faixa (até R$ {reais(f.teto)}): "
        f"alíquota nominal {_porcentagem(f.aliquota)}, "
        f"parcela a deduzir R$ {reais(f.parcela_deduzir)}",
        f"Alíquota efetiva: {_porcentagem(efetiva)} "
        + ("= (RBT12 × Aliq - PD) / RBT12 (LC 123, art. 18, § 1º-A)" if rbt12 is not None
           else "= nominal da 1ª faixa"),
        f"Valor do mês: R$ {reais(valor)} "
        f"= R$ {reais(receita_mes)} × {_porcentagem(efetiva)}",
    ]
    if rbt12 is not None:
        linhas += [f"Aviso: {texto}" for texto in avisos(rbt12)]
    linhas.append("Estimativa conferida contra a tabela da lei: não substitui o PGDAS-D nem o contador.")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
