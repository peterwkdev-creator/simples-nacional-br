"""Simples Nacional: effective rate, monthly amount and Fator R, checked
against the official tables of LC 123/2006 (wording of LC 155/2016).

The result is an estimate: it does not replace the PGDAS-D or an accountant.
"""

from .calculo import (
    LimiteExcedido,
    aliquota_efetiva,
    anexo_por_fator_r,
    avisos,
    faixa,
    fator_r,
    rbt12_inicio_atividade,
    valor_devido,
)
from .tabelas import ANEXOS, FATOR_R_MINIMO, LIMITE_RECEITA, SUBLIMITE_ICMS_ISS, Faixa

__version__ = "0.1.0"

__all__ = [
    "ANEXOS",
    "FATOR_R_MINIMO",
    "LIMITE_RECEITA",
    "SUBLIMITE_ICMS_ISS",
    "Faixa",
    "LimiteExcedido",
    "aliquota_efetiva",
    "anexo_por_fator_r",
    "avisos",
    "faixa",
    "fator_r",
    "rbt12_inicio_atividade",
    "valor_devido",
]
