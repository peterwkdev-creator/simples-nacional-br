"""Critérios de aceite 2 a 5 da especificação, mais a validação da entrada.

Fontes legais (LC 123/2006 na redação da LC 155/2016, lida no site da Câmara
dos Deputados em 09/10/2026, URL em test_tabelas.py):
- art. 18, § 1º-A: fórmula da alíquota efetiva.
- art. 18, § 2º: início de atividade, faixas proporcionais aos meses.
- art. 18, §§ 5º-J e 5º-K: Fator R, folha / receita >= 28% -> Anexo III.
- art. 3º, II: teto de R$ 4,8 milhões; art. 13-A: sublimite de R$ 3,6 milhões.
"""

import unittest
from decimal import Decimal

from simples_nacional import (
    LimiteExcedido,
    aliquota_efetiva,
    anexo_por_fator_r,
    avisos,
    fator_r,
    rbt12_inicio_atividade,
    valor_devido,
)


class TestCaso146(unittest.TestCase):
    """mcp-fiscal-brasil, issue #146: comércio, RBT12 de R$ 4.500.000,00.

    Aquela ferramenta aplica a nominal de 19% (R$ 855.000,00 no ano). Pela lei:
    (4.500.000 x 19% - 378.000) / 4.500.000 = 477.000 / 4.500.000 = 10,60%.
    """

    def test_efetiva(self):
        self.assertEqual(aliquota_efetiva("I", 4_500_000), Decimal("0.106"))

    def test_ano_inteiro(self):
        self.assertEqual(valor_devido("I", 4_500_000, 4_500_000), Decimal("477000.00"))

    def test_mes(self):
        # 375.000 x 10,6% = 39.750,00; x 12 = 477.000,00
        self.assertEqual(valor_devido("I", 4_500_000, 375_000), Decimal("39750.00"))


class TestArredondamento(unittest.TestCase):

    def test_meio_centavo_sobe(self):
        # 12,625 x 4% = 0,505 -> 0,51 (ROUND_HALF_UP; half-even daria 0,50)
        self.assertEqual(valor_devido("I", 100_000, "12.625"), Decimal("0.51"))

    def test_efetiva_sem_arredondar(self):
        # Anexo III, 4ª faixa: (240.000 - 35.640) / 1.500.000 = 0,13624, todos os dígitos
        self.assertEqual(aliquota_efetiva("III", 1_500_000), Decimal("0.13624"))


class TestFatorR(unittest.TestCase):
    """§ 5º-J: Anexo III quando folha / receita for 'igual ou superior a 28%'."""

    def test_razao(self):
        self.assertEqual(fator_r(280_000, 1_000_000), Decimal("0.28"))

    def test_27_99_vai_para_o_v(self):
        self.assertEqual(anexo_por_fator_r(279_900, 1_000_000), "V")

    def test_28_exato_vai_para_o_iii(self):
        self.assertEqual(anexo_por_fator_r(280_000, 1_000_000), "III")

    def test_28_01_vai_para_o_iii(self):
        self.assertEqual(anexo_por_fator_r(280_100, 1_000_000), "III")

    def test_um_centavo_abaixo_nao_arredonda_para_28(self):
        # 279.999,99 / 1.000.000 = 27,999999%: ainda abaixo de 28%
        self.assertEqual(anexo_por_fator_r("279999.99", 1_000_000), "V")

    def test_folha_negativa(self):
        with self.assertRaises(ValueError):
            fator_r(-1, 1_000_000)


class TestLimite(unittest.TestCase):

    def test_teto_exato_ainda_calcula(self):
        # (4.800.000 x 19% - 378.000) / 4.800.000 = 534.000 / 4.800.000 = 11,125%
        self.assertEqual(aliquota_efetiva("I", 4_800_000), Decimal("0.11125"))

    def test_acima_do_teto_e_erro_explicado(self):
        for anexo in ("I", "II", "III", "IV", "V"):
            with self.subTest(anexo=anexo):
                with self.assertRaises(LimiteExcedido) as erro:
                    aliquota_efetiva(anexo, "4800000.01")
                mensagem = str(erro.exception)
                self.assertIn("4.800.000,00", mensagem)
                self.assertIn("art. 3", mensagem)

    def test_valor_devido_tambem_recusa(self):
        with self.assertRaises(LimiteExcedido):
            valor_devido("I", 5_000_000, 400_000)

    def test_limite_excedido_e_value_error(self):
        self.assertTrue(issubclass(LimiteExcedido, ValueError))


class TestAvisos(unittest.TestCase):

    def test_sem_aviso_ate_o_sublimite(self):
        self.assertEqual(avisos(3_600_000), [])

    def test_sublimite(self):
        texto = " ".join(avisos("3600000.01"))
        self.assertIn("3.600.000,00", texto)
        self.assertIn("ICMS", texto)
        self.assertIn("ISS", texto)

    def test_acima_do_limite(self):
        self.assertIn("4.800.000,00", " ".join(avisos(4_800_001)))


class TestInicioDeAtividade(unittest.TestCase):
    """§ 2º: faixas proporcionais aos meses de atividade.

    Proporcionalizar as faixas por n/12 é o mesmo que anualizar a receita por
    12/n: 3 meses, R$ 90.000 -> RBT12 360.000 (teto da 2ª faixa, Anexo I).
    Faixas reduzidas: (90.000 x 7,3% - 5.940 x 3/12) / 90.000 = 5.085 / 90.000 = 5,65%
    Anualizado:       (360.000 x 7,3% - 5.940) / 360.000 = 20.340 / 360.000 = 5,65%
    """

    def test_anualiza(self):
        self.assertEqual(rbt12_inicio_atividade(90_000, 3), Decimal("360000"))

    def test_equivale_a_proporcionalizar_as_faixas(self):
        rbt12 = rbt12_inicio_atividade(90_000, 3)
        self.assertEqual(aliquota_efetiva("I", rbt12), Decimal("0.0565"))

    def test_meses_fora_do_intervalo(self):
        for meses in (0, -1, 12):
            with self.subTest(meses=meses):
                with self.assertRaises(ValueError):
                    rbt12_inicio_atividade(90_000, meses)


class TestEntradas(unittest.TestCase):

    def test_float_recusado(self):
        # float erra centavo: 0.1 + 0.2 != 0.3
        with self.assertRaises(TypeError):
            aliquota_efetiva("I", 4500000.0)

    def test_anexo_invalido(self):
        for anexo in ("VI", "", "1", None):
            with self.subTest(anexo=anexo):
                with self.assertRaises(ValueError):
                    aliquota_efetiva(anexo, 100_000)

    def test_anexo_minusculo(self):
        self.assertEqual(aliquota_efetiva("iii", 150_000), Decimal("0.06"))

    def test_rbt12_zero_ou_negativo(self):
        for rbt12 in (0, -1):
            with self.subTest(rbt12=rbt12):
                with self.assertRaises(ValueError):
                    aliquota_efetiva("I", rbt12)

    def test_receita_negativa(self):
        with self.assertRaises(ValueError):
            valor_devido("I", 100_000, -1)

    def test_texto_invalido(self):
        with self.assertRaises(ValueError):
            aliquota_efetiva("I", "abc")


if __name__ == "__main__":
    unittest.main()
