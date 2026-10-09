"""Command line: python -m simples_nacional --anexo I --rbt12 4500000 --receita-mes 375000"""

import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP

from .calculo import (
    LimiteExcedido,
    aliquota_efetiva,
    anexo_por_fator_r,
    avisos,
    faixa,
    fator_r,
    reais,
    valor_devido,
)


def _numero(texto):
    """Accepts 4500000, 4500000.00, 1000,50 and 1.000,50."""
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        numero = Decimal(texto)
    except ArithmeticError:
        raise argparse.ArgumentTypeError(f"numero invalido: {texto!r}") from None
    if not numero.is_finite():
        raise argparse.ArgumentTypeError(f"numero invalido: {texto!r}")
    return numero


def _porcentagem(fracao):
    texto = f"{(fracao * 100).quantize(Decimal('0.0001'), ROUND_HALF_UP)}"
    return texto.replace(".", ",") + "%"


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m simples_nacional",
        description="Aliquota efetiva e valor do mes no Simples Nacional "
                    "(LC 123/2006, redacao da LC 155/2016). Estimativa: nao "
                    "substitui o PGDAS-D nem o contador.")
    p.add_argument("--anexo", required=True,
                   help="I, II, III, IV, V, ou fator-r (escolhe III ou V pela folha)")
    p.add_argument("--rbt12", required=True, type=_numero,
                   help="receita bruta dos 12 meses anteriores, em R$")
    p.add_argument("--receita-mes", required=True, type=_numero,
                   help="receita bruta do mes de apuracao, em R$")
    p.add_argument("--folha12", type=_numero,
                   help="folha de salarios dos 12 meses anteriores (art. 18, par. 24), "
                        "obrigatoria com --anexo fator-r")
    a = p.parse_args(argv)

    linhas = []
    anexo = a.anexo.upper()
    try:
        if anexo == "FATOR-R":
            if a.folha12 is None:
                p.error("--anexo fator-r exige --folha12")
            anexo = anexo_por_fator_r(a.folha12, a.rbt12)
            linhas.append(
                f"Fator R: {_porcentagem(fator_r(a.folha12, a.rbt12))} "
                f"-> Anexo {anexo} (LC 123, art. 18, par. 5-J: III se >= 28%)")
        f = faixa(anexo, a.rbt12)
        efetiva = aliquota_efetiva(anexo, a.rbt12)
        valor = valor_devido(anexo, a.rbt12, a.receita_mes)
    except LimiteExcedido as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2
    except (ValueError, TypeError) as erro:
        p.error(str(erro))

    linhas += [
        f"Anexo {anexo}, {f.numero}a faixa (ate R$ {reais(f.teto)}): "
        f"aliquota nominal {_porcentagem(f.aliquota)}, "
        f"parcela a deduzir R$ {reais(f.parcela_deduzir)}",
        f"Aliquota efetiva: {_porcentagem(efetiva)} "
        "= (RBT12 x Aliq - PD) / RBT12 (LC 123, art. 18, par. 1-A)",
        f"Valor do mes: R$ {reais(valor)} "
        f"= R$ {reais(a.receita_mes)} x {_porcentagem(efetiva)}",
    ]
    linhas += [f"Aviso: {texto}" for texto in avisos(a.rbt12)]
    linhas.append("Estimativa conferida contra a tabela da lei: nao substitui o PGDAS-D nem o contador.")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
