"""Simples Nacional: alíquota efetiva, valor do mês e Fator R, conferidos
contra as tabelas oficiais da LC 123/2006 (redação da LC 155/2016) e, para
2027 e 2028, da LC 214/2025. A tabela é a do ano-calendário de apuração
(argumento `ano`, obrigatório).

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
from .tabelas import (
    ANEXOS,
    ANEXOS_2027_2028,
    FATOR_R_MINIMO,
    LIMITE_RECEITA,
    SUBLIMITE_ICMS_ISS,
    Faixa,
    Vigencia,
    vigencia,
)

__version__ = "0.2.0"

__all__ = [
    "ANEXOS",
    "ANEXOS_2027_2028",
    "FATOR_R_MINIMO",
    "LIMITE_RECEITA",
    "SUBLIMITE_ICMS_ISS",
    "Faixa",
    "Vigencia",
    "LimiteExcedido",
    "aliquota_efetiva",
    "anexo_por_fator_r",
    "avisos",
    "faixa",
    "fator_r",
    "rbt12_inicio_atividade",
    "valor_devido",
    "vigencia",
]
