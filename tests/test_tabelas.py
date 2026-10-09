"""Each band of each annex (I to V) against the official table, by hand.

Source of every number below: LC 123/2006, Annexes I to V, as worded by
LC 155/2016 (in force since 01/01/2018). Read at the Brazilian Chamber of
Deputies on 09/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html

Effective rate (LC 123, art. 18, par. 1-A): (RBT12 x Aliq - PD) / RBT12.
The `conta` column is the hand calculation; the test re-does it with the
row's own numbers, so a typo in the expected value fails too.

Monthly amount = monthly revenue x effective rate, rounded to cents with
ROUND_HALF_UP. The law does not set a rounding rule; this is the library's
convention, and the only rounding it does.
"""

import unittest
from decimal import Decimal, ROUND_HALF_UP

from simples_nacional import faixa, aliquota_efetiva, valor_devido

RECEITA_MES = Decimal("31234.56")

# (annex, band, RBT12, nominal rate %, deduction, hand calculation,
#  effective rate, amount for RECEITA_MES)
CASOS = [
    ("I", 1, "150000", "4.00", "0", "(150.000 x 4% - 0) / 150.000", "0.04", "1249.38"),
    ("I", 2, "300000", "7.30", "5940", "(21.900 - 5.940) / 300.000", "0.0532", "1661.68"),
    ("I", 3, "600000", "9.50", "13860", "(57.000 - 13.860) / 600.000", "0.0719", "2245.76"),
    ("I", 4, "1500000", "10.70", "22500", "(160.500 - 22.500) / 1.500.000", "0.092", "2873.58"),
    ("I", 5, "3000000", "14.30", "87300", "(429.000 - 87.300) / 3.000.000", "0.1139", "3557.62"),
    ("I", 6, "4500000", "19.00", "378000", "(855.000 - 378.000) / 4.500.000", "0.106", "3310.86"),
    ("II", 1, "150000", "4.50", "0", "(6.750 - 0) / 150.000", "0.045", "1405.56"),
    ("II", 2, "300000", "7.80", "5940", "(23.400 - 5.940) / 300.000", "0.0582", "1817.85"),
    ("II", 3, "600000", "10.00", "13860", "(60.000 - 13.860) / 600.000", "0.0769", "2401.94"),
    ("II", 4, "1500000", "11.20", "22500", "(168.000 - 22.500) / 1.500.000", "0.097", "3029.75"),
    ("II", 5, "3000000", "14.70", "85500", "(441.000 - 85.500) / 3.000.000", "0.1185", "3701.30"),
    ("II", 6, "4500000", "30.00", "720000", "(1.350.000 - 720.000) / 4.500.000", "0.14", "4372.84"),
    ("III", 1, "150000", "6.00", "0", "(9.000 - 0) / 150.000", "0.06", "1874.07"),
    ("III", 2, "300000", "11.20", "9360", "(33.600 - 9.360) / 300.000", "0.0808", "2523.75"),
    ("III", 3, "600000", "13.50", "17640", "(81.000 - 17.640) / 600.000", "0.1056", "3298.37"),
    ("III", 4, "1500000", "16.00", "35640", "(240.000 - 35.640) / 1.500.000", "0.13624", "4255.40"),
    ("III", 5, "3000000", "21.00", "125640", "(630.000 - 125.640) / 3.000.000", "0.16812", "5251.15"),
    ("III", 6, "4500000", "33.00", "648000", "(1.485.000 - 648.000) / 4.500.000", "0.186", "5809.63"),
    ("IV", 1, "150000", "4.50", "0", "(6.750 - 0) / 150.000", "0.045", "1405.56"),
    ("IV", 2, "300000", "9.00", "8100", "(27.000 - 8.100) / 300.000", "0.063", "1967.78"),
    ("IV", 3, "600000", "10.20", "12420", "(61.200 - 12.420) / 600.000", "0.0813", "2539.37"),
    ("IV", 4, "1500000", "14.00", "39780", "(210.000 - 39.780) / 1.500.000", "0.11348", "3544.50"),
    ("IV", 5, "3000000", "22.00", "183780", "(660.000 - 183.780) / 3.000.000", "0.15874", "4958.17"),
    ("IV", 6, "4500000", "33.00", "828000", "(1.485.000 - 828.000) / 4.500.000", "0.146", "4560.25"),
    ("V", 1, "150000", "15.50", "0", "(23.250 - 0) / 150.000", "0.155", "4841.36"),
    ("V", 2, "300000", "18.00", "4500", "(54.000 - 4.500) / 300.000", "0.165", "5153.70"),
    ("V", 3, "600000", "19.50", "9900", "(117.000 - 9.900) / 600.000", "0.1785", "5575.37"),
    ("V", 4, "1500000", "20.50", "17100", "(307.500 - 17.100) / 1.500.000", "0.1936", "6047.01"),
    ("V", 5, "3000000", "23.00", "62100", "(690.000 - 62.100) / 3.000.000", "0.2093", "6537.39"),
    ("V", 6, "4500000", "30.50", "540000", "(1.372.500 - 540.000) / 4.500.000", "0.185", "5778.39"),
]

# Upper limit of each band, the same in all five annexes ("Ate" / "De ... a").
TETOS = ["180000.00", "360000.00", "720000.00", "1800000.00", "3600000.00", "4800000.00"]


class TestFaixasPorAnexo(unittest.TestCase):

    def test_cobre_cinco_anexos_seis_faixas(self):
        self.assertEqual(len(CASOS), 30)
        self.assertEqual({(c[0], c[1]) for c in CASOS},
                         {(a, n) for a in ("I", "II", "III", "IV", "V") for n in range(1, 7)})

    def test_conta_a_mao_confere(self):
        # Guards the expected values themselves, independent of the library.
        for anexo, n, rbt12, aliq, pd, conta, efetiva, valor in CASOS:
            with self.subTest(anexo=anexo, faixa=n, conta=conta):
                rbt12, aliq, pd = Decimal(rbt12), Decimal(aliq) / 100, Decimal(pd)
                self.assertEqual((rbt12 * aliq - pd) / rbt12, Decimal(efetiva))
                self.assertEqual(
                    (RECEITA_MES * Decimal(efetiva)).quantize(Decimal("0.01"), ROUND_HALF_UP),
                    Decimal(valor))

    def test_tabela_igual_a_lei(self):
        for anexo, n, rbt12, aliq, pd, *_ in CASOS:
            with self.subTest(anexo=anexo, faixa=n):
                f = faixa(anexo, rbt12)
                self.assertEqual(f.numero, n)
                self.assertEqual(f.aliquota, Decimal(aliq) / 100)
                self.assertEqual(f.parcela_deduzir, Decimal(pd))
                self.assertEqual(f.teto, Decimal(TETOS[n - 1]))

    def test_aliquota_efetiva(self):
        for anexo, n, rbt12, _, _, conta, efetiva, _ in CASOS:
            with self.subTest(anexo=anexo, faixa=n, conta=conta):
                self.assertEqual(aliquota_efetiva(anexo, rbt12), Decimal(efetiva))

    def test_valor_do_mes_centavo_a_centavo(self):
        for anexo, n, rbt12, *_, valor in CASOS:
            with self.subTest(anexo=anexo, faixa=n):
                self.assertEqual(valor_devido(anexo, rbt12, RECEITA_MES), Decimal(valor))


class TestFronteiras(unittest.TestCase):
    """The ceiling belongs to the lower band: the annex says 'Ate' (up to)."""

    def test_teto_fica_na_faixa_de_baixo(self):
        for anexo in ("I", "II", "III", "IV", "V"):
            for n, teto in enumerate(TETOS, 1):
                with self.subTest(anexo=anexo, teto=teto):
                    self.assertEqual(faixa(anexo, teto).numero, n)

    def test_um_centavo_acima_sobe_de_faixa(self):
        for anexo in ("I", "II", "III", "IV", "V"):
            for n, teto in enumerate(TETOS[:-1], 1):
                acima = Decimal(teto) + Decimal("0.01")
                with self.subTest(anexo=anexo, rbt12=acima):
                    self.assertEqual(faixa(anexo, acima).numero, n + 1)


if __name__ == "__main__":
    unittest.main()
