"""CNAE -> situação no Simples Nacional: impeditiva, ambígua, anexo ou sem classificação.

Precedência: Anexo VI da Res. CGSN 140 (impeditiva) > Anexo VII (ambígua) >
tabela própria pela LC 123, art. 18 (cnae_dados) > sem classificação. As
listas da Res. 140 são oficiais; a ligação da subclasse ao anexo é
interpretação desta biblioteca, declarada na saída. A indústria vai ao
Anexo II até 2026 e ao Anexo I de 2027 em diante (LC 214/2025). Fontes e
datas em cnae_dados.py.

    python -m simples_nacional.cnae 6920-6/01 7112000 --ano 2026
    python -m simples_nacional.cnae 7112000 --ano 2026 --folha12 300000 --rbt12 1000000
"""

import argparse
import re
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from . import cnae_dados
from .calculo import anexo_por_fator_r, fator_r
from .formato import ler_numero, porcentagem
from .tabelas import vigencia

IMPEDITIVA = "impeditiva"
AMBIGUA = "ambígua"
ANEXO = "anexo"
FATOR_R = "fator_r"
SEM_CLASSIFICACAO = "sem_classificacao"

AVISO_INTERPRETACAO = ("Não há tabela oficial CNAE -> anexo: a ligação acima é interpretação "
                       "desta biblioteca sobre a LC 123, art. 18. Estimativa, não substitui o "
                       "PGDAS-D nem o contador.")

LEI = "LC 123, art. 18, "
RES_140 = "Res. CGSN 140/2018, art. 8º, "

# primeiro ano em que a indústria vai ao Anexo I (LC 214, art. 517 e art. 544, III)
INDUSTRIA_NO_ANEXO_I_DESDE = 2027

# o que muda no cálculo além do anexo (LC 123, art. 13, VI; art. 18, §§ 4º, V e 5º-E)
NOTAS = {
    "IV": "Anexo IV: a CPP é paga fora do DAS (LC 123, art. 13, VI).",
    "§ 4º, V": "Sem a parcela do ISS (§ 4º, V).",
    "§ 5º-E": "Sem a parcela do ISS e com a do ICMS do Anexo I (§ 5º-E).",
    "§ 5º": ("Desde 2027, o Anexo II fica só para produto com IPI mantido, o da Zona "
             "Franca de Manaus (§ 4º, II, redação da LC 214/2025)."),
}

DIGITOS = re.compile(r"\d{7}")


class Enquadramento(NamedTuple):
    subclasse: str
    denominacao: str
    situacao: str
    anexo: object  # "I" a "V"; None se impeditiva, ambígua, sem classificação ou Fator R sem folha
    fundamento: str
    observacao: str
    fator_r: object = None  # Decimal, só se a folha foi informada num caso de Fator R


@lru_cache(maxsize=None)
def subclasses():
    """Código -> nome oficial das 1.332 subclasses do IBGE."""
    caminho = Path(__file__).with_name("cnae_subclasses.tsv")
    with open(caminho, encoding="utf-8") as arquivo:
        return dict(linha.rstrip("\n").split("\t") for linha in arquivo)


def _tabela():
    tabela = {}
    for codigo in cnae_dados.REVENDA:
        tabela[codigo] = ("I", "§ 4º, I", "revenda de mercadorias")
    for codigo in cnae_dados.INDUSTRIA:
        tabela[codigo] = ("II", "§ 4º, II", "industrialização")
    for anexo, fundamento, atividade, codigos in cnae_dados.SERVICOS:
        for codigo in codigos:
            tabela[codigo] = (anexo, fundamento, atividade)
    return tabela


TABELA = _tabela()


def normalizar(texto):
    """'6920601', '6920-6/01' ou '6920.6-01' -> '6920-6/01'."""
    digitos = re.sub(r"[\s./-]", "", str(texto))
    if not DIGITOS.fullmatch(digitos):
        raise ValueError(f"{texto!r}: a subclasse da CNAE tem 7 dígitos (ex.: 6920-6/01)")
    return f"{digitos[:4]}-{digitos[4]}/{digitos[5:]}"


def enquadrar(cnae, *, ano, folha12=None, rbt12=None):
    """Situação da subclasse no Simples no ano-calendário `ano`; com folha12 e
    rbt12, resolve o Fator R.

    Interpretação declarada, não tabela oficial: não substitui o PGDAS-D nem
    o contador.
    """
    vigencia(ano)  # mesmo tipo e mesmo piso de ano do resto da biblioteca
    if (folha12 is None) != (rbt12 is None):
        raise ValueError("informe folha12 e rbt12 juntos")
    codigo = normalizar(cnae)
    nome = subclasses().get(codigo)
    if nome is None:
        raise ValueError(f"{codigo} não existe na CNAE 2.3 (lista do IBGE)")
    if codigo in cnae_dados.IMPEDITIVOS:
        return Enquadramento(codigo, nome, IMPEDITIVA, None, RES_140 + "§ 1º, Anexo VI",
                             "Atividade impeditiva: com esta subclasse no CNPJ, a empresa "
                             "não pode optar pelo Simples Nacional.")
    if codigo in cnae_dados.AMBIGUOS:
        return Enquadramento(codigo, nome, AMBIGUA, None, RES_140 + "§ 2º, Anexo VII",
                             "A subclasse abrange atividade impeditiva e permitida: só a "
                             "permitida cabe no Simples. Confira com o contador qual a "
                             "empresa exerce.")
    if codigo not in TABELA:
        return Enquadramento(codigo, nome, SEM_CLASSIFICACAO, None, "",
                             "A LC 123 não descreve esta atividade sem margem de dúvida: "
                             "confira o anexo com o contador.")
    anexo, fundamento, atividade = TABELA[codigo]
    if anexo == "II" and ano >= INDUSTRIA_NO_ANEXO_I_DESDE:
        anexo, fundamento = "I", "§ 5º"
    observacao = [atividade[0].upper() + atividade[1:] + "."]
    observacao += [NOTAS[chave] for chave in (anexo, fundamento) if chave in NOTAS]
    if anexo != "III ou V":
        return Enquadramento(codigo, nome, ANEXO, anexo, LEI + fundamento, " ".join(observacao))
    paragrafo = "§ 5º-J" if fundamento.startswith("§ 5º-I") else "§ 5º-M"
    observacao.append(f"Anexo III com Fator R (folha ÷ RBT12) de 28% ou mais; abaixo, "
                      f"Anexo V ({paragrafo}).")
    if folha12 is None:
        return Enquadramento(codigo, nome, FATOR_R, None, LEI + fundamento, " ".join(observacao))
    return Enquadramento(codigo, nome, FATOR_R, anexo_por_fator_r(folha12, rbt12),
                         LEI + fundamento, " ".join(observacao), fator_r(folha12, rbt12))


def _linhas(e):
    linhas = [f"{e.subclasse} {e.denominacao}"]
    if e.situacao == IMPEDITIVA:
        linhas.append(f"  Situação: impede o Simples Nacional ({e.fundamento})")
    elif e.situacao == AMBIGUA:
        linhas.append(f"  Situação: ambígua ({e.fundamento})")
    elif e.situacao == SEM_CLASSIFICACAO:
        linhas.append("  Situação: sem classificação")
    elif e.fator_r is not None:
        linhas.append(f"  Fator R: {porcentagem(e.fator_r)}, Anexo {e.anexo} ({e.fundamento})")
    elif e.situacao == FATOR_R:
        linhas.append(f"  Anexo III ou V, pelo Fator R ({e.fundamento})")
    else:
        linhas.append(f"  Anexo {e.anexo} ({e.fundamento})")
    linhas.append(f"  {e.observacao}")
    return linhas


def _numero(texto):
    """ler_numero com o erro que o argparse mostra (uso: código 2)."""
    try:
        return ler_numero(texto)
    except ValueError as erro:
        raise argparse.ArgumentTypeError(str(erro)) from None


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m simples_nacional.cnae",
        description="Situação de subclasses da CNAE no Simples Nacional (Res. CGSN 140, "
                    "Anexos VI e VII, e LC 123, art. 18).")
    p.add_argument("cnae", nargs="+", help="subclasse com 7 dígitos (6920-6/01 ou 6920601)")
    p.add_argument("--ano", type=int, default=date.today().year,
                   help="ano-calendário de apuração (padrão: o atual); a indústria vai ao "
                        "Anexo I de 2027 em diante")
    p.add_argument("--folha12", type=_numero, help="folha dos 12 meses, para o Fator R")
    p.add_argument("--rbt12", type=_numero, help="receita bruta dos 12 meses, para o Fator R")
    args = p.parse_args(argv)
    linhas = []
    for cnae in args.cnae:
        try:
            e = enquadrar(cnae, ano=args.ano, folha12=args.folha12, rbt12=args.rbt12)
        except ValueError as erro:
            p.error(str(erro))
        linhas += _linhas(e) + [""]
    # redirecionada no Windows, a saída é cp1252: o que ficar fora dele sai "?"
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if reconfigurar:
        reconfigurar(errors="replace")
    print("\n".join(linhas + [AVISO_INTERPRETACAO]))


__all__ = [
    "AMBIGUA",
    "ANEXO",
    "AVISO_INTERPRETACAO",
    "FATOR_R",
    "IMPEDITIVA",
    "INDUSTRIA_NO_ANEXO_I_DESDE",
    "SEM_CLASSIFICACAO",
    "Enquadramento",
    "enquadrar",
    "main",
    "normalizar",
    "subclasses",
]


if __name__ == "__main__":
    main()
