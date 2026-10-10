"""Entrada e saída no formato brasileiro, públicas desde a 0.3.1.

Quem integra a biblioteca (a CLI dela e outros sistemas) lê número digitado
e mostra valor e alíquota sem reescrever a regra do ponto de milhar.
"""

import unittest
from decimal import Decimal
from pathlib import Path

import simples_nacional
from simples_nacional import ler_numero, para_decimal, porcentagem, reais


class TestLerNumero(unittest.TestCase):

    def test_formatos_aceitos(self):
        casos = {
            "4500000": Decimal("4500000"),
            "4500000.00": Decimal("4500000.00"),
            "1000,50": Decimal("1000.50"),
            "1.000,50": Decimal("1000.50"),
            "360.000": Decimal("360000"),       # ponto e três dígitos: milhar
            "4.800.000,00": Decimal("4800000.00"),
            "8,8": Decimal("8.8"),
            "-1.000,50": Decimal("-1000.50"),
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(ler_numero(texto), esperado)

    def test_reais_na_frente_e_espaco_nas_pontas(self):
        # como o Excel copia a célula: "R$ 1.000,50", às vezes com espaço sem quebra
        casos = {"R$ 100.000,00": Decimal("100000.00"), "R$100": Decimal("100"),
                 " 1.000,50 ": Decimal("1000.50"), "R$\u00a01.000,50": Decimal("1000.50"),
                 "\tR$  8,8\n": Decimal("8.8")}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(ler_numero(texto), esperado)
        for texto in ("R$", "R$ abc", "R$ 1 000", "100 000", "1.000,50 R$", "US$ 10"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "número inválido"):
                    ler_numero(texto)

    def test_ambiguo_e_recusado_com_valueerror(self):
        # 0.500: grupo de milhar não começa em zero
        for texto in ("1,000.50", "1.0000", "1.000.0", "1.5.0", "abc", "", "1 000", "0.500"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "número inválido"):
                    ler_numero(texto)


class TestPorcentagem(unittest.TestCase):

    def test_quatro_casas_e_virgula(self):
        self.assertEqual(porcentagem(Decimal("0.0565")), "5,6500%")
        self.assertEqual(porcentagem(Decimal("0.143037778")), "14,3038%")
        self.assertEqual(porcentagem(Decimal("0.000000005")), "0,0000%")
        self.assertEqual(porcentagem(Decimal("0.000000500")), "0,0001%")  # meio sobe

    def test_int_e_str_como_no_decimal_e_erro_em_portugues(self):
        self.assertEqual(porcentagem("0.05"), "5,0000%")
        self.assertEqual(porcentagem(1), "100,0000%")
        self.assertEqual(reais("1000.5"), "1.000,50")
        with self.assertRaisesRegex(TypeError, "^fracao: .*float"):
            porcentagem(0.05)
        with self.assertRaisesRegex(ValueError, "^valor: não é número"):
            reais("abc")


class TestParaDecimal(unittest.TestCase):

    def test_aceita_decimal_int_e_str(self):
        self.assertEqual(para_decimal("1000.50", "x"), Decimal("1000.50"))
        self.assertEqual(para_decimal(7, "x"), Decimal(7))

    def test_recusa_float_bool_e_lixo_com_o_nome(self):
        with self.assertRaisesRegex(TypeError, "^rbt12: .*float"):
            para_decimal(1.5, "rbt12")
        with self.assertRaises(TypeError):
            para_decimal(True, "x")
        with self.assertRaisesRegex(ValueError, "^receita: não é número"):
            para_decimal("abc", "receita")
        with self.assertRaisesRegex(ValueError, "finito"):
            para_decimal("NaN", "x")


class TestNomesPublicos(unittest.TestCase):

    def test_exportados_e_versao(self):
        for nome in ("ler_numero", "para_decimal", "porcentagem", "reais"):
            with self.subTest(nome=nome):
                self.assertIn(nome, simples_nacional.__all__)
        pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8")
        # a versão mora só no __version__; o pyproject a lê de lá
        self.assertNotRegex(pyproject, r'(?m)^version = "')
        self.assertIn('version = { attr = "simples_nacional.__version__" }', pyproject)
        self.assertRegex(simples_nacional.__version__, r"^\d+\.\d+\.\d+$")

    def test_reais(self):
        self.assertEqual(reais(Decimal("4800000")), "4.800.000,00")
        self.assertEqual(reais(Decimal("0.005")), "0,01")

    def test_nomes_antigos_seguem_valendo(self):
        from simples_nacional import calculo
        from simples_nacional import __main__ as cli
        self.assertIs(calculo.reais, reais)
        self.assertEqual(cli._numero("360.000"), Decimal("360000"))


if __name__ == "__main__":
    unittest.main()
