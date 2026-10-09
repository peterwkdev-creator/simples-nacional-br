"""Número e valor no formato brasileiro: ler o que se digita e mostrar o resultado.

Públicos desde a 0.3.1, para quem integra a biblioteca não reescrever a
regra do ponto de milhar.
"""

import re
from decimal import Decimal, ROUND_HALF_UP

CENTAVO = Decimal("0.01")

_MILHAR = re.compile(r"-?\d{1,3}(\.\d{3})+(,\d+)?")  # 360.000 e 1.000,50
_VIRGULA = re.compile(r"-?\d+(,\d+)?")                # 1000,50
_PONTO = re.compile(r"-?\d+(\.\d{1,2})?")             # 4500000.00


def ler_numero(texto):
    """Aceita 4500000, 4500000.00, 1000,50, 1.000,50 e 360.000 (milhar).

    Ponto seguido de três dígitos é milhar, como se escreve no Brasil; o que
    não casa com nenhum formato (1,000.50, 1.0000) é recusado com ValueError,
    não adivinhado.
    """
    if _MILHAR.fullmatch(texto) or _VIRGULA.fullmatch(texto):
        normal = texto.replace(".", "").replace(",", ".")
    elif _PONTO.fullmatch(texto):
        normal = texto
    else:
        raise ValueError(f"número inválido: {texto!r} (use 1.000,50 ou 1000.50)")
    return Decimal(normal)


def reais(valor):
    """Formato brasileiro: 4800000 -> '4.800.000,00'."""
    texto = f"{Decimal(valor).quantize(CENTAVO, ROUND_HALF_UP):,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def porcentagem(fracao):
    """Fração em porcentagem com quatro casas: Decimal("0.0565") -> '5,6500%'."""
    texto = f"{(fracao * 100).quantize(Decimal('0.0001'), ROUND_HALF_UP)}"
    return texto.replace(".", ",") + "%"
