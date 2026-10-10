"""Simples Nacional: alíquota efetiva, valor do mês e Fator R, conferidos
contra as tabelas oficiais da LC 123/2006 (redação da LC 155/2016) e, para
2027 em diante, da LC 214/2025. A tabela é a do ano-calendário de apuração
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
    rbt12_inicio_atividade,
    valor_devido,
    valor_devido_acima_do_sublimite,
    valor_devido_inicio_atividade,
)
from .formato import ler_numero, para_decimal, porcentagem, reais
from .tabelas import (
    ANEXOS,
    ANEXOS_2027_2028,
    FATOR_R_MINIMO,
    ICMS_ISS_POR_FAIXA,
    LIMITE_RECEITA,
    SUBLIMITE_ICMS_ISS,
    TETO_ISS,
    Faixa,
    Vigencia,
    quinta_faixa_icms_iss_ibs,
    vigencia,
)

__version__ = "1.0.0"

__all__ = [
    "ANEXOS",
    "ANEXOS_2027_2028",
    "FATOR_R_MINIMO",
    "ICMS_ISS_POR_FAIXA",
    "LIMITE_RECEITA",
    "SUBLIMITE_ICMS_ISS",
    "TETO_ISS",
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
    "quinta_faixa_icms_iss_ibs",
    "rbt12_inicio_atividade",
    "reais",
    "valor_devido",
    "valor_devido_acima_do_sublimite",
    "valor_devido_inicio_atividade",
    "vigencia",
]
