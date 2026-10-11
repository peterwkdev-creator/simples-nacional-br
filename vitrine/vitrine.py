"""Adaptador da vitrine: liga a biblioteca à página.

É o único Python que muda por projeto; roda igual aqui e no navegador (Pyodide), e
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
    LIMITE_RECEITA,
    SUBLIMITE_ICMS_ISS,
    aliquota_efetiva,
    aliquota_inicio_atividade,
    aliquotas_por_tributo,
    avisos,
    avisos_inicio_atividade,
    faixa,
    ler_numero,
    parcelas_das,
    planejar_fator_r,
    porcentagem,
    reais,
    valor_devido,
    valor_devido_inicio_atividade,
    vigencia,
)
from simples_nacional.calculo import _meses, _rbt12_primeiros_meses

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


def _mes_inicio(texto):
    texto = texto.strip()
    if not (texto.isascii() and texto.isdigit() and 1 <= int(texto) <= 12):
        raise ValueError(f"mês de início: {texto!r} não é mês (use de 1 a 12)")
    return int(texto)


def _calcular_inicio(entradas, ano, anexo):
    """Empresa com menos de 12 meses: a mesma conta do MCP e da linha de comando."""
    if anexo.replace(" ", "").replace("-", "") == "FATORR":
        return {"resumo": "Com as receitas de cada mês, o Fator R não é calculado: "
                          "informe o anexo, III ou V.", "aviso": AVISO}
    receitas = [_numero(parte, "receitas") for parte in entradas["receitas"].split(";")]
    rbt12, regra = _rbt12_primeiros_meses(receitas, ano)
    f = faixa(anexo, rbt12 or 1, ano=ano)  # sem RBT12: a 1ª faixa
    efetiva = aliquota_inicio_atividade(anexo, receitas, ano=ano)
    valor = valor_devido_inicio_atividade(anexo, receitas, ano=ano)
    mes = len(receitas)
    linhas = [
        ["Mês de atividade", f"{mes}º"],
        ["Regra do início", regra + ("" if rbt12 is None else f" = R$ {reais(rbt12)}")],
        ["Tabela", vigencia(ano).fonte],
        ["Faixa", f"{f.numero}ª do Anexo {anexo}"
         + ("" if rbt12 is None else f", RBT12 até R$ {reais(f.teto)}")],
        ["Alíquota nominal", porcentagem(f.aliquota)],
        ["Parcela a deduzir", f"R$ {reais(f.parcela_deduzir)}"],
        ["Alíquota efetiva", f"{porcentagem(efetiva)} = "
         + ("nominal da 1ª faixa" if rbt12 is None
            else "(RBT12 × nominal − parcela) ÷ RBT12")],
        ["Valor do mês", f"R$ {reais(valor)} = receita do mês (a última da lista) × efetiva, "
                         "arredondado no centavo"],
    ]
    # na 1ª faixa a efetiva é a nominal para qualquer RBT12 dela: o teto reparte igual
    base = f.teto if rbt12 is None else rbt12
    taxas = aliquotas_por_tributo(anexo, base, ano=ano)
    linhas += [[f"No DAS: {tributo}", f"R$ {reais(parcela)} ({porcentagem(taxas[tributo])} da receita)"]
               for tributo, parcela in parcelas_das(anexo, base, receitas[-1], ano=ano).items()]
    texto_mes = entradas.get("mes_inicio", "").strip()
    ano_inicial = receitas[:12]
    if texto_mes:
        achados = avisos_inicio_atividade(receitas, _mes_inicio(texto_mes), ano=ano)
    elif sum(ano_inicial) > SUBLIMITE_ICMS_ISS / 12 * len(ano_inicial):
        achados = [f"R$ {reais(sum(ano_inicial))} em {_meses(len(ano_inicial))} passa de "
                   f"R$ {reais(SUBLIMITE_ICMS_ISS / 12)} por mês. No ano de início de "
                   f"atividade, o limite é R$ {reais(LIMITE_RECEITA / 12)} e o sublimite "
                   f"R$ {reais(SUBLIMITE_ICMS_ISS / 12)}, vezes os meses do início até "
                   "dezembro (LC 123, art. 3º, §§ 2º e 11): informe o mês de início "
                   "para conferir."]
    else:
        achados = []
    linhas += [["Aviso", a] for a in achados]
    resumo = (f"Alíquota efetiva de {porcentagem(efetiva)} na {f.numero}ª faixa do "
              f"Anexo {anexo}: R$ {reais(valor)} no {mes}º mês de atividade, pela tabela de {ano}.")
    if achados:
        resumo += " Há aviso na tabela."
    return {
        "resumo": resumo,
        "aviso": AVISO,
        "tabela": {"titulo": "A conta, passo a passo", "colunas": ["Passo", "Valor"], "linhas": linhas},
    }


def _calcular(entradas):
    ano = _ano(entradas["ano"])
    anexo = entradas["anexo"].strip().upper()
    if entradas.get("receitas", "").strip():
        if entradas.get("rbt12", "").strip() or entradas.get("receita_mes", "").strip():
            return {"resumo": "Com as receitas de cada mês, deixe em branco o RBT12 e a "
                              "receita do mês: a conta sai das receitas.", "aviso": AVISO}
        return _calcular_inicio(entradas, ano, anexo)
    if entradas.get("mes_inicio", "").strip():
        return {"resumo": "O mês de início só vale com as receitas de cada mês.", "aviso": AVISO}
    rbt12 = _numero(entradas["rbt12"], "RBT12")
    receita = _numero(entradas["receita_mes"], "receita do mês")
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
    base = OBRIGATORIOS if not entradas.get("receitas", "").strip() else {
        campo: OBRIGATORIOS[campo] for campo in ("anexo", "ano")}
    faltam = [nome for campo, nome in base.items() if not entradas.get(campo, "").strip()]
    if faltam:
        return {"resumo": f"{'Falta' if len(faltam) == 1 else 'Faltam'} {_lista(faltam)}.", "aviso": AVISO}
    try:
        return _calcular(entradas)
    except (ValueError, TypeError) as erro:  # LimiteExcedido também é ValueError
        return {"resumo": f"Não deu para calcular. {erro}", "aviso": AVISO}
