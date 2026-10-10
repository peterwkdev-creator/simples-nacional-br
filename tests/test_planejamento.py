"""Planejamento do Fator R: folha que leva a 28% e o DAS no Anexo V e no III.

Fonte: LC 123/2006, art. 18, §§ 5º-J, 5º-M e 24; Anexos III e V com a
redação da LC 155/2016 (tabelas.py). Cada caso com a conta feita à mão.
"""

import unittest
from decimal import Decimal as D

from simples_nacional import LimiteExcedido, PlanoFatorR, planejar_fator_r


class TestPlanejarFatorR(unittest.TestCase):

    def test_anexo_v_hoje_3a_faixa(self):
        # RBT12 600.000, 3ª faixa. V: (600.000 x 19,5% - 9.900) / 600.000 = 17,85%;
        # III: (600.000 x 13,5% - 17.640) / 600.000 = 10,56%. Receita 50.000.
        p = planejar_fator_r(120_000, 600_000, 50_000, ano=2026)
        self.assertEqual(p, PlanoFatorR(
            fator=D("0.2"), anexo="V",
            folha_minima=D("168000.00"),        # 28% x 600.000
            folha_que_falta=D("48000.00"),      # 168.000 - 120.000
            das_anexo_v=D("8925.00"),           # 50.000 x 17,85%
            das_anexo_iii=D("5280.00"),         # 50.000 x 10,56%
            diferenca_das=D("3645.00")))

    def test_ja_no_anexo_iii_nada_falta(self):
        # folha exatamente 28%: Anexo III (§ 5º-J, "igual ou superior")
        p = planejar_fator_r(280_000, 1_000_000, 80_000, ano=2026)
        self.assertEqual((p.anexo, p.folha_minima, p.folha_que_falta),
                         ("III", D("280000.00"), D(0)))
        # 4ª faixa. V: (1.000.000 x 20,5% - 17.100) / 1.000.000 = 18,79%;
        # III: (1.000.000 x 16% - 35.640) / 1.000.000 = 12,436%
        self.assertEqual(p.das_anexo_v, D("15032.00"))      # 80.000 x 18,79%
        self.assertEqual(p.das_anexo_iii, D("9948.80"))     # 80.000 x 12,436%
        self.assertEqual(p.diferenca_das, D("5083.20"))

    def test_6a_faixa_o_v_sai_mais_barato(self):
        # RBT12 4.800.000. V: (4.800.000 x 30,5% - 540.000) / 4.800.000 = 19,25%;
        # III: (4.800.000 x 33% - 648.000) / 4.800.000 = 19,5%. Receita 400.000.
        p = planejar_fator_r(0, 4_800_000, 400_000, ano=2026)
        self.assertEqual((p.das_anexo_v, p.das_anexo_iii, p.diferenca_das),
                         (D("77000.00"), D("78000.00"), D("-1000.00")))
        self.assertEqual(p.folha_que_falta, D("1344000.00"))  # 28% x 4.800.000

    def test_2027_usa_a_tabela_do_ano(self):
        # 2027: 6ª faixa 0,1 ponto menor. V: (4.800.000 x 30,4% - 540.000) / 4.800.000
        # = 19,15%; III: (4.800.000 x 32,9% - 648.000) / 4.800.000 = 19,4%.
        p = planejar_fator_r(0, 4_800_000, 400_000, ano=2027)
        self.assertEqual((p.das_anexo_v, p.das_anexo_iii, p.diferenca_das),
                         (D("76600.00"), D("77600.00"), D("-1000.00")))

    def test_folha_minima_arredonda_para_cima(self):
        # 28% x 100.000,01 = 28.000,0028: 28.000,00 (o arredondamento comum)
        # daria 27,99999...%
        p = planejar_fator_r("28000.00", "100000.01", 10_000, ano=2026)
        self.assertEqual((p.anexo, p.folha_minima, p.folha_que_falta),
                         ("V", D("28000.01"), D("0.01")))
        self.assertGreaterEqual(p.folha_minima / D("100000.01"), D("0.28"))
        p = planejar_fator_r("28000.0028", "100000.01", 10_000, ano=2026)
        self.assertEqual((p.anexo, p.folha_que_falta), ("III", D(0)))

    def test_icms_iss_no_das_vai_aos_dois_anexos(self):
        # RBT12 4.000.000, 6ª faixa, a pedido com o ISS pela 5ª faixa, que usa
        # o próprio RBT12 (Res. CGSN 140, art. 21, III, b). Receita 100.000.
        # V: (4.000.000 x 30,5% - 540.000) / 4.000.000 = 17%; 5ª do V:
        # (4.000.000 x 23% - 62.100) / 4.000.000 = 21,4475%, x ISS 23,5%
        # = 5,0401625%. V = 22,0401625% x 100.000 = 22.040,16.
        # III: (4.000.000 x 33% - 648.000) / 4.000.000 = 16,8%; 5ª do III:
        # (4.000.000 x 21% - 125.640) / 4.000.000 = 17,859%, x ISS 33,5%
        # = 5,982765%. III = 22,782765% x 100.000 = 22.782,77.
        p = planejar_fator_r(0, 4_000_000, 100_000, ano=2026, icms_iss_no_das=True)
        self.assertEqual((p.das_anexo_v, p.das_anexo_iii, p.diferenca_das),
                         (D("22040.16"), D("22782.77"), D("-742.61")))

    def test_entradas_como_nos_calculos(self):
        with self.assertRaisesRegex(ValueError, "negativa"):
            planejar_fator_r(-1, 600_000, 50_000, ano=2026)
        with self.assertRaises(LimiteExcedido):
            planejar_fator_r(0, "4800000.01", 50_000, ano=2026)
        with self.assertRaises(TypeError):
            planejar_fator_r(0, 600_000, 50_000, ano="2026")
        with self.assertRaises(TypeError):
            planejar_fator_r(0.5, 600_000, 50_000, ano=2026)


if __name__ == "__main__":
    unittest.main()
