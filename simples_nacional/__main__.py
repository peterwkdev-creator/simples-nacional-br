"""Linha de comando: python -m simples_nacional --anexo I --rbt12 4500000 --receita-mes 375000"""

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
    """Aceita 4500000, 4500000.00, 1000,50 e 1.000,50."""
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        numero = Decimal(texto)
    except ArithmeticError:
        raise argparse.ArgumentTypeError(f"número inválido: {texto!r}") from None
    if not numero.is_finite():
        raise argparse.ArgumentTypeError(f"número inválido: {texto!r}")
    return numero


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
    p.add_argument("--rbt12", required=True, type=_numero,
                   help="receita bruta dos 12 meses anteriores, em R$")
    p.add_argument("--receita-mes", required=True, type=_numero,
                   help="receita bruta do mês de apuração, em R$")
    p.add_argument("--folha12", type=_numero,
                   help="folha de salários dos 12 meses anteriores (art. 18, § 24), "
                        "obrigatória com --anexo fator-r")
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
                f"-> Anexo {anexo} (LC 123, art. 18, § 5º-J: III se >= 28%)")
        f = faixa(anexo, a.rbt12)
        efetiva = aliquota_efetiva(anexo, a.rbt12)
        valor = valor_devido(anexo, a.rbt12, a.receita_mes)
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
        "= (RBT12 × Aliq - PD) / RBT12 (LC 123, art. 18, § 1º-A)",
        f"Valor do mês: R$ {reais(valor)} "
        f"= R$ {reais(a.receita_mes)} × {_porcentagem(efetiva)}",
    ]
    linhas += [f"Aviso: {texto}" for texto in avisos(a.rbt12)]
    linhas.append("Estimativa conferida contra a tabela da lei: não substitui o PGDAS-D nem o contador.")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
