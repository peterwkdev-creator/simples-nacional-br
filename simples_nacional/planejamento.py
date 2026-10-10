"""Planejamento do Fator R: a folha que leva ao Anexo III e a diferença no DAS.

LC 123/2006, art. 18: Anexo III quando a folha de salários dos 12 meses
dividida pelo RBT12 for igual ou superior a 28% (§ 5º-J), Anexo V abaixo
disso (§ 5º-M); folha como no § 24, com o pró-labore e os encargos.

A diferença é só no DAS. O pró-labore a mais paga a contribuição
previdenciária do sócio e pode pagar IRPF, que dependem da pessoa: nada
disso está descontado. O Fator R olha os 12 meses da folha, então o que
falta pode entrar aos poucos ou de uma vez; a biblioteca não escolhe.
"""

from decimal import Decimal, ROUND_CEILING
from typing import NamedTuple

from .calculo import anexo_por_fator_r, fator_r, valor_devido
from .formato import CENTAVO, _contexto_fixo, para_decimal
from .tabelas import FATOR_R_MINIMO


class PlanoFatorR(NamedTuple):
    """Resultado de `planejar_fator_r`. Valores em reais; o Fator R em fração."""

    fator: Decimal            # folha12 / rbt12, sem arredondar
    anexo: str                # 'III' ou 'V' com a folha de hoje
    folha_minima: Decimal     # folha de 12 meses que dá 28%, em centavos, para cima
    folha_que_falta: Decimal  # o que falta para chegar lá; 0 no Anexo III
    das_anexo_v: Decimal      # valor do mês no Anexo V
    das_anexo_iii: Decimal    # valor do mês no Anexo III
    diferenca_das: Decimal    # V - III; negativa se o V sair mais barato


@_contexto_fixo
def planejar_fator_r(folha12, rbt12, receita_mes, *, ano, icms_iss_no_das=False):
    """Folha de 12 meses que leva o Fator R a 28% e o DAS do mês no Anexo V e no III.

    `folha12`, `rbt12`, `ano` e `icms_iss_no_das` como em `fator_r` e
    `valor_devido`. A folha mínima é 28% do RBT12 arredondada para cima no
    centavo, para que dê 28% ou mais. Na 6ª faixa o Anexo V pode sair mais
    barato que o III (diferença negativa). O resultado é estimativa: não
    substitui o PGDAS-D nem o contador.
    """
    fator = fator_r(folha12, rbt12)  # confere folha12 e rbt12
    anexo = anexo_por_fator_r(folha12, rbt12)
    das_v = valor_devido("V", rbt12, receita_mes, ano=ano, icms_iss_no_das=icms_iss_no_das)
    das_iii = valor_devido("III", rbt12, receita_mes, ano=ano, icms_iss_no_das=icms_iss_no_das)
    minima = (para_decimal(rbt12, "rbt12") * FATOR_R_MINIMO).quantize(CENTAVO, ROUND_CEILING)
    falta = Decimal(0) if anexo == "III" else minima - para_decimal(folha12, "folha12")
    return PlanoFatorR(fator, anexo, minima, falta, das_v, das_iii, das_v - das_iii)


__all__ = ["PlanoFatorR", "planejar_fator_r"]
