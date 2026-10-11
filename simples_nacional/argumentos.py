"""Linha de comando em português: a ajuda e os erros do argparse.

O argparse escreve "usage:", "options:" e os erros em inglês. `Argumentos`
troca só o que ele mesmo escreve; o argparse de quem importa a biblioteca não
muda. Erro que o argparse monte e não esteja na lista abaixo sai como veio.

    p = Argumentos(prog=nome_do_comando("simples-nacional", "simples_nacional"))
"""

import argparse
import re
import sys
from pathlib import Path

# os erros que o argparse monta, do Python 3.9 ao 3.14
_ERROS = [
    (r"the following arguments are required: (.*)", r"faltam argumentos obrigatórios: \1"),
    (r"one of the arguments (.*) is required", r"falta um destes argumentos: \1"),
    (r"unrecognized arguments: (.*)", r"argumentos desconhecidos: \1"),
    (r"invalid choice: (.*?) \(choose from (.*)\)", r"opção inválida: \1 (escolha entre \2)"),
    (r"invalid \S+ value: (.*)", r"valor inválido: \1"),
    (r"expected one argument", "falta o valor"),
    (r"expected at most one argument", "aceita no máximo um valor"),
    (r"expected at least one argument", "falta ao menos um valor"),
    (r"expected (\d+) arguments?", r"espera \1 valor(es)"),
    (r"not allowed with argument (.*)", r"não pode vir junto com \1"),
    (r"ignored explicit argument (.*)", r"valor não aceito: \1"),
    (r"ambiguous option: (\S+) could match (.*)", r"opção ambígua: \1 pode ser \2"),
]


def traduzir_erro(mensagem):
    """O erro do argparse em português; o que não está na lista sai como veio."""
    m = re.fullmatch(r"argument (\S+?): (.*)", mensagem, re.S)
    if m:
        return f"argumento {m.group(1)}: {traduzir_erro(m.group(2))}"
    for padrao, troca in _ERROS:
        m = re.fullmatch(padrao, mensagem, re.S)
        if m:
            return m.expand(troca)
    return mensagem


def nome_do_comando(instalado, modulo):
    """Como o usuário chamou: pelo pip, o comando instalado; por python -m, o módulo.

    Por python -m, argv[0] é o caminho do .py; pelo pip, o do comando
    (no Windows, com .exe).
    """
    return instalado if Path(sys.argv[0]).stem == instalado else f"python -m {modulo}"


class _Uso:
    """Formatador da ajuda com "uso:" no lugar de "usage:"."""

    def add_usage(self, usage, actions, groups, prefix=None):
        super().add_usage(usage, actions, groups, "uso: " if prefix is None else prefix)


class Argumentos(argparse.ArgumentParser):
    """ArgumentParser com a ajuda e os erros em português."""

    def __init__(self, *args, add_help=True, formatter_class=argparse.HelpFormatter, **kwargs):
        formatador = type("Formatador", (_Uso, formatter_class), {})
        super().__init__(*args, add_help=False, formatter_class=formatador, **kwargs)
        self._positionals.title = "argumentos"
        self._optionals.title = "opções"
        if add_help:
            self.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS,
                              help="mostra esta ajuda e sai")

    def add_argument(self, *args, **kwargs):
        if kwargs.get("action") == "version":
            kwargs.setdefault("help", "mostra a versão e sai")
        return super().add_argument(*args, **kwargs)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: erro: {traduzir_erro(message)}\n")


__all__ = ["Argumentos", "nome_do_comando", "traduzir_erro"]
