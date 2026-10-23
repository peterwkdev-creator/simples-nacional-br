"""Repartição do DAS do mês por tributo, de 2018 em diante.

As tabelas e a fonte legal de cada uma estão em `tabelas_reparticao.py`:
2018 a 2026 (LC 123, redação da LC 155/2016); 2027 e 2028, cada ano de 2029
a 2032 e de 2033 em diante (LC 214/2025, Anexos XVIII a XXII).

- Cada tributo leva receita do mês x alíquota efetiva x percentual da faixa.
- 5ª faixa dos Anexos III e IV: se o ISS passar do teto da nota (*) do anexo
  (5% da receita até 2028; 4,5%, 4%, 3,5% e 3% de 2029 a 2032), o ISS fica no
  teto e cada outro tributo leva (efetiva - teto) x o percentual da nota.
  Três dessas notas da LC 214 somam 100,01% ou 99,99% (IV em 2029 e 2031,
  III em 2030): os percentuais se aplicam na proporção deles, para a soma
  bater com o DAS.
- 6ª faixa (RBT12 acima do sublimite de R$ 3,6 milhões): o DAS é só federal
  (e a CBS, de 2027 em diante); ICMS, ISS e IBS se pagam fora dele. Com
  `icms_iss_no_das=True` em `parcelas_das`, eles seguem no DAS pela 5ª faixa,
  como em `aliquota_efetiva`; o ISS acima do teto da nota (*) passa aos
  outros tributos pelos percentuais dela (leitura da biblioteca, Res. CGSN
  140, art. 21, III, a), e o total fica o mesmo.

Arredondamento (convenção, a lei não fixa): o DAS é o `valor_devido`, em
centavos com ROUND_HALF_UP. As parcelas somam o DAS pelo maior resto: cada
uma começa truncada no centavo e o centavo que falta vai para as de maior
fração descartada (empate: a ordem da linha da lei).
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal
from typing import Dict

from .calculo import aliquota_efetiva, faixa, valor_devido
from .formato import CENTAVO, Numero, _contexto_fixo, para_decimal
from .tabelas import SUBLIMITE_ICMS_ISS, TETO_ISS, vigencia
from .tabelas_reparticao import (PARTILHA_2027_2028, PARTILHA_ATE_2026, PARTILHA_DESDE_2029,
                                 TETO_ISS_2027_2028, TETO_ISS_ATE_2026, TETO_ISS_DESDE_2029)


def _tabelas(ano):
    """Partilha, percentuais da nota (*) e teto do ISS do ano-calendário."""
    if ano <= 2026:
        return PARTILHA_ATE_2026, TETO_ISS_ATE_2026, TETO_ISS
    if ano <= 2028:
        return PARTILHA_2027_2028, TETO_ISS_2027_2028, TETO_ISS
    if ano <= 2032:
        teto, nota = TETO_ISS_DESDE_2029[ano]
        return PARTILHA_DESDE_2029[ano], nota, teto
    return PARTILHA_DESDE_2029[2033], {}, TETO_ISS  # sem ISS: a nota não se aplica


def _taxas(anexo, f, efetiva, partilha, nota, teto):
    """Parte da receita que vai a cada tributo: efetiva x percentual da faixa."""
    linha = partilha[anexo][f.numero - 1]
    if f.numero == 5 and anexo in nota and efetiva * linha["ISS"] > teto:
        soma = sum(nota[anexo].values())
        taxas = {t: (efetiva - teto) * p / soma for t, p in nota[anexo].items()}
        taxas["ISS"] = teto
        return {t: taxas[t] for t in linha if t in taxas}  # ordem das colunas da lei
    return {t: efetiva * p for t, p in linha.items()}


def _quinta_faixa_no_das(anexo, rbt12, ano, partilha, nota, teto):
    """ICMS ou ISS (e IBS) pela 5ª faixa com RBT12 acima do sublimite, por tributo.

    {[(RBT12 × nominal da 5ª) − PD da 5ª] / RBT12} × percentual da 5ª faixa,
    como em aliquota_efetiva com icms_iss_no_das=True. ISS acima do teto da
    nota (*) do anexo: fica no teto e o que passa vai aos outros tributos
    pelos percentuais da nota, na proporção deles.
    """
    quinta = vigencia(ano).anexos[anexo][4]
    efetiva = (rbt12 * quinta.aliquota - quinta.parcela_deduzir) / rbt12
    linha = partilha[anexo][4]
    taxas = {t: efetiva * linha[t] for t in ("ICMS", "ISS", "IBS") if t in linha}
    if "ISS" in taxas and anexo in nota and taxas["ISS"] > teto:
        excesso, taxas["ISS"] = taxas["ISS"] - teto, teto
        soma = sum(nota[anexo].values())
        for t, p in nota[anexo].items():
            taxas[t] = taxas.get(t, Decimal(0)) + excesso * p / soma
    return taxas


def _repartir(das, exatos):
    """Parcelas em centavos que somam `das`, pelo maior resto (docstring do módulo)."""
    parcelas = {t: v.quantize(CENTAVO, ROUND_DOWN) for t, v in exatos.items()}
    faltam = int((das - sum(parcelas.values())) / CENTAVO)
    if not 0 <= faltam <= len(parcelas):
        raise AssertionError(f"inalcançável: {faltam} centavos para {len(parcelas)} parcelas")
    # sorted é estável: no empate, a ordem da linha da repartição
    for t in sorted(exatos, key=lambda t: exatos[t] - parcelas[t], reverse=True)[:faltam]:
        parcelas[t] += CENTAVO
    return parcelas


@_contexto_fixo
def aliquotas_por_tributo(anexo: str, rbt12: Numero, *, ano: int) -> Dict[str, Decimal]:
    """Alíquota efetiva de cada tributo no DAS, em fração da receita, sem arredondar.

    Somam a `aliquota_efetiva` (na precisão do Decimal). Mesmo `ano` e mesma
    ordem de `parcelas_das`; acima do sublimite, só o que fica no DAS.
    """
    efetiva = aliquota_efetiva(anexo, rbt12, ano=ano)  # confere anexo, ano e RBT12
    f = faixa(anexo, rbt12, ano=ano)
    return _taxas(anexo.upper(), f, efetiva, *_tabelas(ano))


@_contexto_fixo
def parcelas_das(anexo: str, rbt12: Numero, receita_mes: Numero, *, ano: int,
                 icms_iss_no_das: bool = False) -> Dict[str, Decimal]:
    """Valor de cada tributo dentro do DAS do mês, em centavos; a soma é o DAS.

    `ano` é o ano-calendário do mês de apuração, de 2018 em diante: a tabela
    é a do período. Devolve um dict na ordem das colunas da lei, como
    {"IRPJ": ..., "CSLL": ..., "COFINS": ..., ...}. Acima do sublimite, só o
    que fica no DAS (ver `valor_devido`); com `icms_iss_no_das=True`, como em
    `valor_devido`, ICMS ou ISS (e o IBS, desde 2027; de 2033 em diante, só
    o IBS) seguem no DAS pela 5ª faixa e entram como parcelas (docstring do
    módulo). Até o sublimite a opção não muda nada. O resultado é
    estimativa: não substitui o PGDAS-D nem o contador.
    """
    # confere anexo, ano, RBT12, receita e icms_iss_no_das
    das = valor_devido(anexo, rbt12, receita_mes, ano=ano, icms_iss_no_das=icms_iss_no_das)
    receita = para_decimal(receita_mes, "receita_mes")
    taxas = aliquotas_por_tributo(anexo, rbt12, ano=ano)
    rbt12 = para_decimal(rbt12, "rbt12")
    if icms_iss_no_das and rbt12 > SUBLIMITE_ICMS_ISS:
        tabelas = _tabelas(ano)
        for t, x in _quinta_faixa_no_das(anexo.upper(), rbt12, ano, *tabelas).items():
            taxas[t] = taxas.get(t, Decimal(0)) + x
        # na ordem das colunas da lei (a da 5ª faixa, que tem todos os tributos)
        colunas = [t for t in tabelas[0][anexo.upper()][4] if t in taxas]
        taxas = {t: taxas[t] for t in colunas + [t for t in taxas if t not in colunas]}
    return _repartir(das, {t: receita * x for t, x in taxas.items()})


__all__ = ["aliquotas_por_tributo", "parcelas_das"]
