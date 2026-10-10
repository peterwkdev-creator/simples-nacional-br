"""Repartição do DAS por tributo contra a lei, faixa a faixa.

Fonte de 2018 a 2026: LC 123/2006, Anexos I a V, redação da LC 155/2016
(vigência 1º/1/2018), tabelas "Percentual de Repartição dos Tributos" e a
nota (*) dos Anexos III e IV. Texto atualizado da LC 155 lido no site da
Câmara em 10/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html

2027 e 2028: test_reparticao_2027.py; aqui só se confere que parcelas_das
usa aquela tabela. De 2029 em diante: test_reparticao_2029.py.
Arredondamento: o de reparticao.py (DAS do valor_devido, parcelas pelo
maior resto; empate na ordem da linha da lei).
"""

import unittest
from decimal import Decimal

from simples_nacional import (ICMS_ISS_POR_FAIXA, aliquota_efetiva, aliquotas_por_tributo,
                              parcelas_das, quinta_faixa_icms_iss_ibs, valor_devido)
from simples_nacional.tabelas_reparticao import (PARTILHA_2027_2028, PARTILHA_ATE_2026,
                                                 TETO_ISS_ATE_2026)

D = Decimal

# Repartição da lei, faixa a faixa, na ordem das colunas de cada anexo.
# "-" na lei = tributo fora do DAS na faixa (ausente aqui).
PARTILHA_LEI = {
    "I": ("IRPJ CSLL COFINS PIS CPP ICMS", [
        "5,50 3,50 12,74 2,76 41,50 34,00",
        "5,50 3,50 12,74 2,76 41,50 34,00",
        "5,50 3,50 12,74 2,76 42,00 33,50",
        "5,50 3,50 12,74 2,76 42,00 33,50",
        "5,50 3,50 12,74 2,76 42,00 33,50",
        "13,50 10,00 28,27 6,13 42,10 -",
    ]),
    "II": ("IRPJ CSLL COFINS PIS CPP IPI ICMS", [
        "5,50 3,50 11,51 2,49 37,50 7,50 32,00",
        "5,50 3,50 11,51 2,49 37,50 7,50 32,00",
        "5,50 3,50 11,51 2,49 37,50 7,50 32,00",
        "5,50 3,50 11,51 2,49 37,50 7,50 32,00",
        "5,50 3,50 11,51 2,49 37,50 7,50 32,00",
        "8,50 7,50 20,96 4,54 23,50 35,00 -",
    ]),
    "III": ("IRPJ CSLL COFINS PIS CPP ISS", [
        "4,00 3,50 12,82 2,78 43,40 33,50",
        "4,00 3,50 14,05 3,05 43,40 32,00",
        "4,00 3,50 13,64 2,96 43,40 32,50",
        "4,00 3,50 13,64 2,96 43,40 32,50",
        "4,00 3,50 12,82 2,78 43,40 33,50",
        "35,00 15,00 16,03 3,47 30,50 -",
    ]),
    "IV": ("IRPJ CSLL COFINS PIS ISS", [
        "18,80 15,20 17,67 3,83 44,50",
        "19,80 15,20 20,55 4,45 40,00",
        "20,80 15,20 19,73 4,27 40,00",
        "17,80 19,20 18,90 4,10 40,00",
        "18,80 19,20 18,08 3,92 40,00",
        "53,50 21,50 20,55 4,45 -",
    ]),
    "V": ("IRPJ CSLL COFINS PIS CPP ISS", [
        "25,00 15,00 14,10 3,05 28,85 14,00",
        "23,00 15,00 14,10 3,05 27,85 17,00",
        "24,00 15,00 14,92 3,23 23,85 19,00",
        "21,00 15,00 15,74 3,41 23,85 21,00",
        "23,00 12,50 14,10 3,05 23,85 23,50",
        "35,00 15,50 16,44 3,56 29,50 -",
    ]),
}

# Nota (*): 5ª faixa acima de 14,92537% (III) ou 12,5% (IV): ISS fixo em 5%
# e (efetiva - 5%) x estes percentuais.
TETO_LEI = {
    "III": ("IRPJ CSLL COFINS PIS CPP", "6,02 5,26 19,28 4,18 65,26"),
    "IV": ("IRPJ CSLL COFINS PIS", "31,33 32,00 30,13 6,54"),
}


def _lei(colunas, linha):
    return {c: D(v.replace(",", ".")) / 100
            for c, v in zip(colunas.split(), linha.split()) if v != "-"}


def _reais(**valores):
    return {t: D(v) for t, v in valores.items()}


class TestTabela(unittest.TestCase):
    def test_igual_a_lei(self):
        for anexo, (colunas, linhas) in PARTILHA_LEI.items():
            for n, linha in enumerate(linhas):
                with self.subTest(anexo=anexo, faixa=n + 1):
                    self.assertEqual(PARTILHA_ATE_2026[anexo][n], _lei(colunas, linha))
        self.assertEqual(set(PARTILHA_ATE_2026), set(PARTILHA_LEI))

    def test_cada_linha_soma_100(self):
        for anexo, linhas in PARTILHA_ATE_2026.items():
            self.assertEqual(len(linhas), 6)
            for n, linha in enumerate(linhas):
                with self.subTest(anexo=anexo, faixa=n + 1):
                    self.assertEqual(sum(linha.values()), 1)

    def test_sexta_faixa_sem_icms_iss(self):
        for anexo, linhas in PARTILHA_ATE_2026.items():
            self.assertFalse({"ICMS", "ISS"} & set(linhas[5]), anexo)

    def test_teto_do_iss_igual_a_lei(self):
        for anexo, (colunas, linha) in TETO_LEI.items():
            self.assertEqual(TETO_ISS_ATE_2026[anexo], _lei(colunas, linha))
            self.assertEqual(sum(TETO_ISS_ATE_2026[anexo].values()), 1)
        self.assertEqual(set(TETO_ISS_ATE_2026), {"III", "IV"})


class TestParcelas(unittest.TestCase):
    def test_anexo_i_primeira_faixa(self):
        # efetiva = 4% (1ª faixa, sem parcela a deduzir); DAS = 10.000 x 4% = 400,00
        # IRPJ 400 x 5,50% = 22,00; CSLL 400 x 3,50% = 14,00; Cofins 400 x 12,74% = 50,96;
        # PIS 400 x 2,76% = 11,04; CPP 400 x 41,50% = 166,00; ICMS 400 x 34,00% = 136,00
        self.assertEqual(parcelas_das("I", 150_000, 10_000, ano=2026), _reais(
            IRPJ="22.00", CSLL="14.00", COFINS="50.96", PIS="11.04", CPP="166.00",
            ICMS="136.00"))

    def test_anexo_i_sexta_faixa_so_federal(self):
        # efetiva = (4.000.000 x 19% - 378.000) / 4.000.000 = 9,55%; DAS = 9.550,00
        # IRPJ 1.289,25; CSLL 955,00; Cofins 2.699,785; PIS 585,415; CPP 4.020,55.
        # Truncados somam 9.549,99; o centavo vai para a Cofins (empate de
        # 0,005 com o PIS; a Cofins vem antes na linha da lei).
        self.assertEqual(parcelas_das("I", 4_000_000, 100_000, ano=2026), _reais(
            IRPJ="1289.25", CSLL="955.00", COFINS="2699.79", PIS="585.41", CPP="4020.55"))

    def test_anexo_iii_quinta_faixa_com_teto_do_iss(self):
        # efetiva = (3.000.000 x 21% - 125.640) / 3.000.000 = 16,812% > 14,92537%
        # DAS 16.812,00; ISS 5% = 5.000,00; resto 11.812,00 x 6,02% = 711,0824 (IRPJ),
        # x 5,26% = 621,3112, x 19,28% = 2.277,3536, x 4,18% = 493,7416,
        # x 65,26% = 7.708,5112. O centavo que falta vai para a Cofins (maior resto).
        self.assertEqual(parcelas_das("III", 3_000_000, 100_000, ano=2026), _reais(
            IRPJ="711.08", CSLL="621.31", COFINS="2277.36", PIS="493.74", CPP="7708.51",
            ISS="5000.00"))

    def test_anexo_iii_quinta_faixa_abaixo_do_teto(self):
        # efetiva = (1.900.000 x 21% - 125.640) / 1.900.000 = 14,387...% < 14,92537%:
        # linha da 5ª faixa da lei, ISS = 33,50% da efetiva (abaixo de 5%)
        efetiva = (D(1_900_000) * D("0.21") - 125_640) / 1_900_000
        p = parcelas_das("III", 1_900_000, 100_000, ano=2026)
        self.assertEqual(set(p), {"IRPJ", "CSLL", "COFINS", "PIS", "CPP", "ISS"})
        self.assertLess(abs(p["ISS"] - 100_000 * efetiva * D("0.335")), D("0.01"))
        self.assertLess(p["ISS"], D("5000.00"))

    def test_anexo_iv_quinta_faixa_com_teto_do_iss(self):
        # efetiva = (3.000.000 x 22% - 183.780) / 3.000.000 = 15,874% > 12,5%
        # DAS 15.874,00; ISS 5.000,00; resto 10.874,00 x 31,33% = 3.406,8242 (IRPJ),
        # x 32% = 3.479,68, x 30,13% = 3.276,3362, x 6,54% = 711,1596.
        # Faltam 2 centavos: PIS (0,0096) e Cofins (0,0062), os maiores restos.
        self.assertEqual(parcelas_das("IV", 3_000_000, 100_000, ano=2026), _reais(
            IRPJ="3406.82", CSLL="3479.68", COFINS="3276.34", PIS="711.16", ISS="5000.00"))

    def test_toda_faixa_de_todo_anexo_bate_com_a_lei(self):
        # Uma receita por faixa; cada parcela fica a menos de 1 centavo da conta
        # exata com o percentual da lei e a soma é o DAS da biblioteca.
        rbt12_por_faixa = (150_000, 300_000, 600_000, 1_500_000, 3_000_000, 4_200_000)
        receita = D(100_000)
        for anexo, (colunas, linhas) in PARTILHA_LEI.items():
            for n, rbt12 in enumerate(rbt12_por_faixa):
                for ano in (2018, 2026):
                    with self.subTest(anexo=anexo, faixa=n + 1, ano=ano):
                        das = valor_devido(anexo, rbt12, receita, ano=ano)
                        p = parcelas_das(anexo, rbt12, receita, ano=ano)
                        self.assertEqual(sum(p.values()), das)
                        efetiva = aliquota_efetiva(anexo, rbt12, ano=ano)
                        lei = _lei(colunas, linhas[n])
                        if n == 4 and anexo in TETO_LEI and efetiva * lei["ISS"] > D("0.05"):
                            exatos = {t: receita * (efetiva - D("0.05")) * x
                                      for t, x in _lei(*TETO_LEI[anexo]).items()}
                            exatos["ISS"] = receita * D("0.05")
                        else:
                            exatos = {t: receita * efetiva * x for t, x in lei.items()}
                        self.assertEqual(set(p), set(exatos))
                        for t in p:
                            self.assertLess(abs(p[t] - exatos[t]), D("0.01"), t)

    def test_2027_e_2028_usam_a_tabela_da_lc_214(self):
        for anexo in PARTILHA_LEI:
            for ano in (2027, 2028):
                with self.subTest(anexo=anexo, ano=ano):
                    p = parcelas_das(anexo, 1_000_000, 250_000, ano=ano)  # 4ª faixa
                    self.assertEqual(list(p), list(PARTILHA_2027_2028[anexo][3]))
        self.assertIn("CBS", parcelas_das("I", 150_000, 10_000, ano=2027))
        self.assertNotIn("COFINS", parcelas_das("I", 150_000, 10_000, ano=2027))

    def test_receita_zero(self):
        p = parcelas_das("V", 500_000, 0, ano=2026)
        self.assertEqual(sum(p.values()), 0)

    def test_anexo_por_nome(self):
        self.assertEqual(parcelas_das("iii", 500_000, 1_000, ano=2026),
                         parcelas_das("III", 500_000, 1_000, ano=2026))


class TestEntradas(unittest.TestCase):
    def test_ano(self):
        with self.assertRaisesRegex(ValueError, "2018"):
            parcelas_das("I", 150_000, 10_000, ano=2017)
        for ano in ("2026", True, 2026.0, 2030.0):
            with self.subTest(ano=ano), self.assertRaisesRegex(TypeError, "ano"):
                parcelas_das("I", 150_000, 10_000, ano=ano)

    def test_ano_obrigatorio_e_nomeado(self):
        with self.assertRaises(TypeError):
            parcelas_das("I", 150_000, 10_000)
        with self.assertRaises(TypeError):
            parcelas_das("I", 150_000, 10_000, 2026)

    def test_receita_negativa_e_anexo_invalido(self):
        with self.assertRaises(ValueError):
            parcelas_das("I", 150_000, -1, ano=2026)
        with self.assertRaises(ValueError):
            parcelas_das("VI", 150_000, 10_000, ano=2026)


class TestAliquotasPorTributo(unittest.TestCase):
    # um RBT12 por faixa, e a 5ª faixa de III e IV acima do teto do ISS
    RBT12 = (150_000, 300_000, 600_000, 1_500_000, 3_000_000, 4_000_000)

    def test_somam_a_efetiva_e_seguem_a_ordem_das_parcelas(self):
        for ano in (2026, 2027, 2029, 2030, 2031, 2032, 2033):
            for anexo in ("I", "II", "III", "IV", "V"):
                for rbt12 in self.RBT12:
                    with self.subTest(ano=ano, anexo=anexo, rbt12=rbt12):
                        taxas = aliquotas_por_tributo(anexo, rbt12, ano=ano)
                        efetiva = aliquota_efetiva(anexo, rbt12, ano=ano)
                        self.assertLess(abs(sum(taxas.values()) - efetiva), D("1e-20"))
                        p = parcelas_das(anexo, rbt12, 10_000, ano=ano)
                        self.assertEqual(list(taxas), list(p))

    def test_anexo_iii_quinta_faixa_iss_no_teto(self):
        # 2026, RBT12 3.000.000: efetiva (3.000.000 x 21% - 125.640) / 3.000.000
        # = 16,812%; ISS da tabela 16,812% x 33,5% = 5,632% > 5%: ISS fica em 5%
        taxas = aliquotas_por_tributo("III", 3_000_000, ano=2026)
        self.assertEqual(taxas["ISS"], D("0.05"))
        efetiva = (D(3_000_000) * D("0.21") - 125_640) / 3_000_000
        self.assertLess(abs(taxas["CPP"] - (efetiva - D("0.05")) * D("0.6526")), D("1e-20"))

    def test_entradas_como_nos_calculos(self):
        with self.assertRaises(TypeError):
            aliquotas_por_tributo("I", 150_000, ano="2026")
        with self.assertRaisesRegex(ValueError, "2018"):
            aliquotas_por_tributo("I", 150_000, ano=2017)
        with self.assertRaises(ValueError):
            aliquotas_por_tributo("VI", 150_000, ano=2026)
        self.assertEqual(aliquotas_por_tributo("iii", 150_000, ano=2026),
                         aliquotas_por_tributo("III", 150_000, ano=2026))


class TestCoerenciaComOResto(unittest.TestCase):
    """A repartição e as contas do sublimite leem a mesma lei: têm de bater."""

    def test_icms_iss_por_faixa_ate_2026(self):
        for anexo, linhas in PARTILHA_ATE_2026.items():
            for n in range(5):
                with self.subTest(anexo=anexo, faixa=n + 1):
                    linha = linhas[n]
                    self.assertEqual(linha.get("ICMS", linha.get("ISS")),
                                     ICMS_ISS_POR_FAIXA[anexo][n])

    def test_quinta_faixa_de_cada_periodo(self):
        from simples_nacional.tabelas_reparticao import PARTILHA_DESDE_2029
        tabelas = {2026: PARTILHA_ATE_2026, 2027: PARTILHA_2027_2028, 2028: PARTILHA_2027_2028}
        tabelas.update(PARTILHA_DESDE_2029)
        for ano, partilha in tabelas.items():
            for anexo, linhas in partilha.items():
                with self.subTest(ano=ano, anexo=anexo):
                    linha = linhas[4]
                    icms_iss = linha.get("ICMS", linha.get("ISS", D(0)))
                    self.assertEqual((icms_iss, linha.get("IBS", D(0))),
                                     quinta_faixa_icms_iss_ibs(anexo, ano=ano))


if __name__ == "__main__":
    unittest.main()
