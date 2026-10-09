"""Simples Nacional: alíquota efetiva, valor do mês e Fator R, conferidos
contra as tabelas oficiais da LC 123/2006 (redação da LC 155/2016).

O resultado é estimativa: não substitui o PGDAS-D nem o contador.
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
