"""Simples Nacional: alíquota efetiva, valor do mês e Fator R, conferidos
contra as tabelas oficiais da LC 123/2006 (redação da LC 155/2016) e, para
2027 e 2028, da LC 214/2025. A tabela é a do ano-calendário de apuração
(argumento `ano`, obrigatório).

O resultado é estimativa: não substitui o PGDAS-D nem o contador.
"""

from .calculo import (
    DEFASAGEM_DESDE,
    LimiteExcedido,
    aliquota_efetiva,
    aliquota_inicio_atividade,
    anexo_por_fator_r,
    avisos,
    avisos_inicio_atividade,
    faixa,
    fator_r,
    para_decimal,
    rbt12_inicio_atividade,
    valor_devido,
    valor_devido_inicio_atividade,
)
from .formato import ler_numero, porcentagem, reais
from .tabelas import (
    ANEXOS,
    ANEXOS_2027_2028,
    FATOR_R_MINIMO,
    ICMS_ISS_QUINTA_FAIXA,
    LIMITE_RECEITA,
    SUBLIMITE_ICMS_ISS,
    Faixa,
    Vigencia,
    vigencia,
)

__version__ = "0.5.0"

__all__ = [
    "ANEXOS",
    "ANEXOS_2027_2028",
    "FATOR_R_MINIMO",
    "ICMS_ISS_QUINTA_FAIXA",
    "LIMITE_RECEITA",
    "SUBLIMITE_ICMS_ISS",
    "Faixa",
    "Vigencia",
    "LimiteExcedido",
    "DEFASAGEM_DESDE",
    "aliquota_efetiva",
    "aliquota_inicio_atividade",
    "anexo_por_fator_r",
    "avisos",
    "avisos_inicio_atividade",
    "faixa",
    "fator_r",
    "ler_numero",
    "para_decimal",
    "porcentagem",
    "rbt12_inicio_atividade",
    "reais",
    "valor_devido",
    "valor_devido_inicio_atividade",
    "vigencia",
]
