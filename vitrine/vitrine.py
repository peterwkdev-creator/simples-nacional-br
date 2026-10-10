"""Adaptador da vitrine: liga a biblioteca à página.

Modelo da Coordenação (`modelo/vitrine/LEIA-ME.md`). É o único Python que
muda por projeto; roda igual aqui e no navegador (Pyodide), e
`vitrine/montar.py` o confere com o exemplo antes de montar.

Contrato: `executar(entradas)` recebe {nome do campo: texto} e devolve
"resumo" (o que o leitor de tela anuncia), "aviso" (o limite do resultado)
e, quando a conta sai, "tabela" com cada passo dela. Não há texto para
marcar. Campo vazio ou número inválido não levanta exceção: o "resumo" diz
o que falta ou o que está errado.
"""
from decimal import ROUND_DOWN, Decimal

from simples_nacional import (
    FATOR_R_MINIMO,
    aliquota_efetiva,
    aliquotas_por_tributo,
    avisos,
    faixa,
    ler_numero,
    parcelas_das,
    planejar_fator_r,
    porcentagem,
    reais,
    valor_devido,
    vigencia,
)

AVISO = "Estimativa pela tabela da lei: não substitui o PGDAS-D nem o contador."

ATENCAO_FATOR_R = ("A diferença é só no DAS. O pró-labore a mais paga a contribuição "
                   "previdenciária do sócio e pode pagar IRPF, que dependem da pessoa: "
                   "nada disso está descontado.")

OBRIGATORIOS = {
    "anexo": "o anexo",
    "ano": "o ano de apuração",
    "rbt12": "a receita dos 12 meses (RBT12)",
    "receita_mes": "a receita do mês",
}


def _lista(itens):
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _numero(texto, nome):
    try:
        return ler_numero(texto)
    except ValueError:
        raise ValueError(f"{nome}: {texto.strip()!r} não é número (use 1.500.000,00 ou 1500000.00)") from None


def _ano(texto):
    texto = texto.strip()
    if not (texto.isascii() and texto.isdigit() and len(texto) == 4):
        raise ValueError(f"ano: {texto!r} não é um ano (use quatro dígitos, como 2026)")
    ano = int(texto)
    vigencia(ano)
    return ano


def _percentual_cortado(fracao):
    """Fator R cortado na 4ª casa: 27,99999% arredondado mostraria 28,0000%
    ao lado do Anexo V."""
    return f"{(fracao * 100).quantize(Decimal('0.0001'), ROUND_DOWN)}".replace(".", ",") + "%"


def _calcular(entradas):
    ano = _ano(entradas["ano"])
    rbt12 = _numero(entradas["rbt12"], "RBT12")
    receita = _numero(entradas["receita_mes"], "receita do mês")
    anexo = entradas["anexo"].strip().upper()
    linhas = []
    plano = None
    if anexo.replace(" ", "").replace("-", "") == "FATORR":
        folha_texto = entradas.get("folha12", "")
        if not folha_texto.strip():
            return {"resumo": "Falta a folha dos 12 meses: com Fator R, é ela que "
                              "decide entre o Anexo III e o V.", "aviso": AVISO}
        folha = _numero(folha_texto, "folha dos 12 meses")
        plano = planejar_fator_r(folha, rbt12, receita, ano=ano)
        anexo = plano.anexo
        lado = "28% ou mais" if plano.fator >= FATOR_R_MINIMO else "abaixo de 28%"
        linhas.append(["Fator R (folha ÷ RBT12)", f"{_percentual_cortado(plano.fator)}: {lado}, Anexo {anexo}"])
    f = faixa(anexo, rbt12, ano=ano)
    efetiva = aliquota_efetiva(anexo, rbt12, ano=ano)
    valor = valor_devido(anexo, rbt12, receita, ano=ano)
    linhas += [
        ["Tabela", vigencia(ano).fonte],
        ["Faixa", f"{f.numero}ª do Anexo {anexo}, RBT12 até R$ {reais(f.teto)}"],
        ["Alíquota nominal", porcentagem(f.aliquota)],
        ["Parcela a deduzir", f"R$ {reais(f.parcela_deduzir)}"],
        ["Alíquota efetiva", f"{porcentagem(efetiva)} = (RBT12 × nominal − parcela) ÷ RBT12"],
        ["Valor do mês", f"R$ {reais(valor)} = receita do mês × efetiva, arredondado no centavo"],
    ]
    taxas = aliquotas_por_tributo(anexo, rbt12, ano=ano)
    linhas += [[f"No DAS: {tributo}", f"R$ {reais(parcela)} ({porcentagem(taxas[tributo])} da receita)"]
               for tributo, parcela in parcelas_das(anexo, rbt12, receita, ano=ano).items()]
    if plano is not None:
        diferenca = plano.diferenca_das
        linhas += [
            ["Folha para 28%", f"R$ {reais(plano.folha_minima)}: "
             + ("a de hoje já chega" if plano.anexo == "III"
                else f"faltam R$ {reais(plano.folha_que_falta)}")],
            ["Valor no Anexo V", f"R$ {reais(plano.das_anexo_v)}"],
            ["Valor no Anexo III", f"R$ {reais(plano.das_anexo_iii)}"],
            ["Diferença", f"o III sai R$ {reais(diferenca)} mais barato" if diferenca > 0
             else f"o V sai R$ {reais(-diferenca)} mais barato" if diferenca < 0
             else "o mesmo valor"],
            ["Atenção", ATENCAO_FATOR_R],
        ]
    achados = avisos(rbt12, ano=ano)
    linhas += [["Aviso", a] for a in achados]
    resumo = (f"Alíquota efetiva de {porcentagem(efetiva)} na {f.numero}ª faixa do "
              f"Anexo {anexo}: R$ {reais(valor)} no mês, pela tabela de {ano}.")
    if plano is not None and plano.anexo == "V" and diferenca > 0:
        resumo += (f" Com mais R$ {reais(plano.folha_que_falta)} de folha em 12 meses, "
                   f"o Anexo III sairia R$ {reais(diferenca)} mais barato no DAS.")
    if achados:
        resumo += " Há aviso na tabela."
    return {
        "resumo": resumo,
        "aviso": AVISO,
        "tabela": {"titulo": "A conta, passo a passo", "colunas": ["Passo", "Valor"], "linhas": linhas},
    }


def executar(entradas):
    faltam = [nome for campo, nome in OBRIGATORIOS.items() if not entradas.get(campo, "").strip()]
    if faltam:
        return {"resumo": f"{'Falta' if len(faltam) == 1 else 'Faltam'} {_lista(faltam)}.", "aviso": AVISO}
    try:
        return _calcular(entradas)
    except (ValueError, TypeError) as erro:  # LimiteExcedido também é ValueError
        return {"resumo": f"Não deu para calcular. {erro}", "aviso": AVISO}
