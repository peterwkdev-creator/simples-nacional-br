"""Linha de comando em português: a ajuda e cada erro do argparse, do
Python 3.9 ao 3.14 (o CI roda todos)."""

import argparse
import contextlib
import io
import unittest

from simples_nacional.argumentos import Argumentos, traduzir_erro
from simples_nacional.__main__ import main
from simples_nacional.cnae import main as main_cnae

INGLES = ("usage", "options", "positional arguments", "show this help", "show program",
          "error:", "required", "invalid", "expected", "unrecognized", "argument ",
          "choose from", "not allowed", "ambiguous")


def rodar(funcao, argv):
    """(código de saída, saída, erro) de uma linha de comando que termina em SystemExit."""
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        try:
            funcao(argv)
            codigo = 0
        except SystemExit as fim:
            codigo = fim.code
    return codigo, saida.getvalue(), erro.getvalue()


class TestAjuda(unittest.TestCase):

    def test_ajuda_dos_comandos_em_portugues(self):
        for funcao, esperado in [(main, ("uso: ", "opções:", "mostra esta ajuda e sai",
                                         "mostra a versão e sai")),
                                 (main_cnae, ("uso: ", "argumentos:", "opções:",
                                              "mostra esta ajuda e sai"))]:
            with self.subTest(funcao=funcao.__module__):
                codigo, saida, _ = rodar(funcao, ["--help"])
                self.assertEqual(codigo, 0)
                for trecho in esperado:
                    self.assertIn(trecho, saida)
                for palavra in INGLES:
                    self.assertNotIn(palavra, saida.lower())

    def test_cnae_mostra_o_nome_de_quem_reexporta(self):
        # o pacote completo reexporta este comando com o nome dele
        _, saida, _ = rodar(lambda argv: main_cnae(argv, prog="python -m outro.cnae"), ["--help"])
        self.assertTrue(saida.startswith("uso: python -m outro.cnae "), saida[:40])

    def test_argparse_de_fora_nao_muda(self):
        Argumentos(prog="x")
        self.assertTrue(argparse.ArgumentParser(prog="y").format_help().startswith("usage: y"))


class TestErros(unittest.TestCase):

    def parser(self):
        p = Argumentos(prog="teste")
        p.add_argument("--obrigatorio", required=True)
        p.add_argument("--numero", type=int)
        p.add_argument("--escolha", choices=["a", "b"])
        p.add_argument("--dois", nargs=2)
        grupo = p.add_mutually_exclusive_group()
        grupo.add_argument("--sim", action="store_true")
        grupo.add_argument("--nao", action="store_true")
        return p

    def test_cada_erro_do_argparse_em_portugues(self):
        casos = [
            ([], "faltam argumentos obrigatórios: --obrigatorio"),
            (["--obrigatorio", "1", "--numero", "x"], "argumento --numero: valor inválido: 'x'"),
            (["--obrigatorio", "1", "--escolha", "z"], "argumento --escolha: opção inválida: 'z'"),
            (["--obrigatorio"], "argumento --obrigatorio: falta o valor"),
            (["--obrigatorio", "1", "--dois", "x"], "argumento --dois: espera 2 valor(es)"),
            (["--obrigatorio", "1", "--sim", "--nao"],
             "argumento --nao: não pode vir junto com --sim"),
            (["--obrigatorio", "1", "--xyz"], "argumentos desconhecidos: --xyz"),
            (["--obrigatorio", "1", "--n", "1"], "opção ambígua: --n"),
        ]
        for argv, esperado in casos:
            with self.subTest(argv=argv):
                codigo, _, erro = rodar(self.parser().parse_args, argv)
                self.assertEqual(codigo, 2)
                self.assertTrue(erro.startswith("uso: teste "), erro)
                self.assertIn(f"teste: erro: {esperado}", erro)
                for palavra in INGLES:
                    self.assertNotIn(palavra, erro.lower())

    def test_erro_desconhecido_sai_como_veio(self):
        self.assertEqual(traduzir_erro("--receitas substitui --rbt12"), "--receitas substitui --rbt12")

    def test_rbt12_zero_indica_a_opcao_do_comando(self):
        # a mensagem da API cita aliquota_inicio_atividade, que quem usa o comando não tem
        codigo, _, erro = rodar(main, ["--ano", "2026", "--anexo", "I", "--rbt12", "0",
                                       "--receita-mes", "1000"])
        self.assertEqual(codigo, 2)
        self.assertIn("use --receitas", erro)
        self.assertNotIn("aliquota_inicio_atividade", erro)


if __name__ == "__main__":
    unittest.main()
