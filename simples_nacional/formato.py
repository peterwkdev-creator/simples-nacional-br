"""Número e valor no formato brasileiro: ler o que se digita e mostrar o resultado.

Públicos para quem integra a biblioteca não reescrever a regra do ponto
de milhar.
"""

import functools
import re
from decimal import (Context, Decimal, DivisionByZero, InvalidOperation, Overflow,
                     ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext)

CENTAVO = Decimal("0.01")

# Precisão e arredondamento fixos nas contas da biblioteca: um
# getcontext().prec = 6 no programa de quem a usa faria o quantize do
# centavo soltar InvalidOperation, e outro arredondamento mudaria o resultado.
_CONTEXTO = Context(prec=28, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
                    capitals=1, clamp=0, flags=[],
                    traps=[InvalidOperation, DivisionByZero, Overflow])


def _contexto_fixo(funcao):
    @functools.wraps(funcao)
    def envolvida(*args, **kwargs):
        with localcontext(_CONTEXTO):
            return funcao(*args, **kwargs)
    return envolvida


_MILHAR = re.compile(r"-?[1-9]\d{0,2}(\.\d{3})+(,\d+)?")  # 360.000 e 1.000,50
_VIRGULA = re.compile(r"-?\d+(,\d+)?")                # 1000,50
_PONTO = re.compile(r"-?\d+(\.\d{1,2})?")             # 4500000.00
_REAIS = re.compile(r"R\$\s*")                        # R$ 1.000,50, como o Excel copia


def ler_numero(texto):
    """Aceita 4500000, 4500000.00, 1000,50, 1.000,50 e 360.000 (milhar), com
    ou sem "R$" na frente e espaço nas pontas.

    Ponto seguido de três dígitos é milhar, como se escreve no Brasil; o que
    não casa com nenhum formato (1,000.50, 1.0000, 100 000) é recusado com
    ValueError, não adivinhado.
    """
    numero = texto.strip()
    sem_rs = _REAIS.match(numero)
    if sem_rs:
        numero = numero[sem_rs.end():]
    if _MILHAR.fullmatch(numero) or _VIRGULA.fullmatch(numero):
        normal = numero.replace(".", "").replace(",", ".")
    elif _PONTO.fullmatch(numero):
        normal = numero
    else:
        raise ValueError(f"número inválido: {texto!r} (use 1.000,50 ou 1000.50)")
    return Decimal(normal)


def para_decimal(valor, nome):
    """Decimal exato a partir de Decimal, int ou str; float e bool são recusados.

    `nome` abre a mensagem de erro (`rbt12: não é número: 'abc'`). O texto se
    lê como no Decimal, com ponto decimal ("12.625"); o que o usuário digita
    no formato brasileiro ("360.000") passa antes por ler_numero.
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


@_contexto_fixo
def reais(valor):
    """Formato brasileiro: 4800000 -> '4.800.000,00'."""
    texto = f"{para_decimal(valor, 'valor').quantize(CENTAVO, ROUND_HALF_UP):,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


@_contexto_fixo
def porcentagem(fracao):
    """Fração em porcentagem com quatro casas: Decimal("0.0565") -> '5,6500%'."""
    fracao = para_decimal(fracao, "fracao")
    texto = f"{(fracao * 100).quantize(Decimal('0.0001'), ROUND_HALF_UP)}"
    return texto.replace(".", ",") + "%"
