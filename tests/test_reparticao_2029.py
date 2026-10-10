"""Repartição do DAS por tributo de 2029 em diante, contra a lei.

Fonte: LC 214/2025, Anexos XVIII a XXII, tabelas "Partilha do Simples
Nacional" de 2029, 2030, 2031, 2032 e "A partir do ano-calendário 2033", e a
nota (*) dos Anexos III e IV (redação da LC 227/2026). Texto atualizado lido
no site da Câmara em 10/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html

Os percentuais abaixo estão como no texto da lei (vírgula). Arredondamento:
o de reparticao.py (DAS do valor_devido, parcelas pelo maior resto).
"""

import unittest
from decimal import Decimal

from simples_nacional import aliquota_efetiva, valor_devido
from simples_nacional import parcelas_das
from simples_nacional.tabelas_reparticao import PARTILHA_DESDE_2029, TETO_ISS_DESDE_2029

D = Decimal
ANEXOS = ("I", "II", "III", "IV", "V")

# Ano de início de cada tabela; 2033 vale para 2033 em diante.
# "-" na lei = tributo fora do DAS na faixa (ausente aqui).
PARTILHA_LEI = {
    2029: {
        "I": ("IRPJ CSLL CBS CPP ICMS IBS", [
            "5,50 3,50 15,50 41,50 30,60 3,40",
            "5,50 3,50 15,50 41,50 30,60 3,40",
            "5,50 3,50 15,50 42,00 30,15 3,35",
            "5,50 3,50 15,50 42,00 30,15 3,35",
            "5,50 3,50 15,50 42,00 30,15 3,35",
            "13,50 10,00 34,40 42,10 - -",
        ]),
        "II": ("IRPJ CSLL CBS CPP IPI ICMS IBS", [
            "5,50 3,50 14,00 37,50 7,50 28,80 3,20",
            "5,50 3,50 14,00 37,50 7,50 28,80 3,20",
            "5,50 3,50 14,00 37,50 7,50 28,80 3,20",
            "5,50 3,50 14,00 37,50 7,50 28,80 3,20",
            "5,50 3,50 14,00 37,50 7,50 28,80 3,20",
            "8,50 7,50 25,50 23,50 35,00 - -",
        ]),
        "III": ("IRPJ CSLL CBS CPP ISS IBS", [
            "4,00 3,50 15,60 43,40 30,15 3,35",
            "4,00 3,50 17,10 43,40 28,80 3,20",
            "4,00 3,50 16,60 43,40 29,25 3,25",
            "4,00 3,50 16,60 43,40 29,25 3,25",
            "4,00 3,50 15,60 43,40 30,15 3,35",
            "35,00 15,00 19,50 30,50 - -",
        ]),
        "IV": ("IRPJ CSLL CBS ISS IBS", [
            "18,80 15,20 21,50 40,05 4,45",
            "19,80 15,20 25,00 36,00 4,00",
            "20,80 15,20 24,00 36,00 4,00",
            "17,80 19,20 23,00 36,00 4,00",
            "18,80 19,20 22,00 36,00 4,00",
            "53,50 21,50 25,00 - -",
        ]),
        "V": ("IRPJ CSLL CBS CPP ISS IBS", [
            "25,00 15,00 17,15 28,85 12,60 1,40",
            "23,00 15,00 17,15 27,85 15,30 1,70",
            "24,00 15,00 18,15 23,85 17,10 1,90",
            "21,00 15,00 19,15 23,85 18,90 2,10",
            "23,00 12,50 17,15 23,85 21,15 2,35",
            "35,00 15,50 20,00 29,50 - -",
        ]),
    },
    2030: {
        "I": ("IRPJ CSLL CBS CPP ICMS IBS", [
            "5,50 3,50 15,50 41,50 27,20 6,80",
            "5,50 3,50 15,50 41,50 27,20 6,80",
            "5,50 3,50 15,50 42,00 26,80 6,70",
            "5,50 3,50 15,50 42,00 26,80 6,70",
            "5,50 3,50 15,50 42,00 26,80 6,70",
            "13,50 10,00 34,40 42,10 - -",
        ]),
        "II": ("IRPJ CSLL CBS CPP IPI ICMS IBS", [
            "5,50 3,50 14,00 37,50 7,50 25,60 6,40",
            "5,50 3,50 14,00 37,50 7,50 25,60 6,40",
            "5,50 3,50 14,00 37,50 7,50 25,60 6,40",
            "5,50 3,50 14,00 37,50 7,50 25,60 6,40",
            "5,50 3,50 14,00 37,50 7,50 25,60 6,40",
            "8,50 7,50 25,50 23,50 35,00 - -",
        ]),
        "III": ("IRPJ CSLL CBS CPP ISS IBS", [
            "4,00 3,50 15,60 43,40 26,80 6,70",
            "4,00 3,50 17,10 43,40 25,60 6,40",
            "4,00 3,50 16,60 43,40 26,00 6,50",
            "4,00 3,50 16,60 43,40 26,00 6,50",
            "4,00 3,50 15,60 43,40 26,80 6,70",
            "35,00 15,00 19,50 30,50 - -",
        ]),
        "IV": ("IRPJ CSLL CBS ISS IBS", [
            "18,80 15,20 21,50 35,60 8,90",
            "19,80 15,20 25,00 32,00 8,00",
            "20,80 15,20 24,00 32,00 8,00",
            "17,80 19,20 23,00 32,00 8,00",
            "18,80 19,20 22,00 32,00 8,00",
            "53,50 21,50 25,00 - -",
        ]),
        "V": ("IRPJ CSLL CBS CPP ISS IBS", [
            "25,00 15,00 17,15 28,85 11,20 2,80",
            "23,00 15,00 17,15 27,85 13,60 3,40",
            "24,00 15,00 18,15 23,85 15,20 3,80",
            "21,00 15,00 19,15 23,85 16,80 4,20",
            "23,00 12,50 17,15 23,85 18,80 4,70",
            "35,00 15,50 20,00 29,50 - -",
        ]),
    },
    2031: {
        "I": ("IRPJ CSLL CBS CPP ICMS IBS", [
            "5,50 3,50 15,50 41,50 23,80 10,20",
            "5,50 3,50 15,50 41,50 23,80 10,20",
            "5,50 3,50 15,50 42,00 23,45 10,05",
            "5,50 3,50 15,50 42,00 23,45 10,05",
            "5,50 3,50 15,50 42,00 23,45 10,05",
            "13,50 10,00 34,40 42,10 - -",
        ]),
        "II": ("IRPJ CSLL CBS CPP IPI ICMS IBS", [
            "5,50 3,50 14,00 37,50 7,50 22,40 9,60",
            "5,50 3,50 14,00 37,50 7,50 22,40 9,60",
            "5,50 3,50 14,00 37,50 7,50 22,40 9,60",
            "5,50 3,50 14,00 37,50 7,50 22,40 9,60",
            "5,50 3,50 14,00 37,50 7,50 22,40 9,60",
            "8,50 7,50 25,50 23,50 35,00 - -",
        ]),
        "III": ("IRPJ CSLL CBS CPP ISS IBS", [
            "4,00 3,50 15,60 43,40 23,45 10,05",
            "4,00 3,50 17,10 43,40 22,40 9,60",
            "4,00 3,50 16,60 43,40 22,75 9,75",
            "4,00 3,50 16,60 43,40 22,75 9,75",
            "4,00 3,50 15,60 43,40 23,45 10,05",
            "35,00 15,00 19,50 30,50 - -",
        ]),
        "IV": ("IRPJ CSLL CBS ISS IBS", [
            "18,80 15,20 21,50 31,15 13,35",
            "19,80 15,20 25,00 28,00 12,00",
            "20,80 15,20 24,00 28,00 12,00",
            "17,80 19,20 23,00 28,00 12,00",
            "18,80 19,20 22,00 28,00 12,00",
            "53,50 21,50 25,00 - -",
        ]),
        "V": ("IRPJ CSLL CBS CPP ISS IBS", [
            "25,00 15,00 17,15 28,85 9,80 4,20",
            "23,00 15,00 17,15 27,85 11,90 5,10",
            "24,00 15,00 18,15 23,85 13,30 5,70",
            "21,00 15,00 19,15 23,85 14,70 6,30",
            "23,00 12,50 17,15 23,85 16,45 7,05",
            "35,00 15,50 20,00 29,50 - -",
        ]),
    },
    2032: {
        "I": ("IRPJ CSLL CBS CPP ICMS IBS", [
            "5,50 3,50 15,50 41,50 20,40 13,60",
            "5,50 3,50 15,50 41,50 20,40 13,60",
            "5,50 3,50 15,50 42,00 20,10 13,40",
            "5,50 3,50 15,50 42,00 20,10 13,40",
            "5,50 3,50 15,50 42,00 20,10 13,40",
            "13,50 10,00 34,40 42,10 - -",
        ]),
        "II": ("IRPJ CSLL CBS CPP IPI ICMS IBS", [
            "5,50 3,50 14,00 37,50 7,50 19,20 12,80",
            "5,50 3,50 14,00 37,50 7,50 19,20 12,80",
            "5,50 3,50 14,00 37,50 7,50 19,20 12,80",
            "5,50 3,50 14,00 37,50 7,50 19,20 12,80",
            "5,50 3,50 14,00 37,50 7,50 19,20 12,80",
            "8,50 7,50 25,50 23,50 35,00 - -",
        ]),
        "III": ("IRPJ CSLL CBS CPP ISS IBS", [
            "4,00 3,50 15,60 43,40 20,10 13,40",
            "4,00 3,50 17,10 43,40 19,20 12,80",
            "4,00 3,50 16,60 43,40 19,50 13,00",
            "4,00 3,50 16,60 43,40 19,50 13,00",
            "4,00 3,50 15,60 43,40 20,10 13,40",
            "35,00 15,00 19,50 30,50 - -",
        ]),
        "IV": ("IRPJ CSLL CBS ISS IBS", [
            "18,80 15,20 21,50 26,70 17,80",
            "19,80 15,20 25,00 24,00 16,00",
            "20,80 15,20 24,00 24,00 16,00",
            "17,80 19,20 23,00 24,00 16,00",
            "18,80 19,20 22,00 24,00 16,00",
            "53,50 21,50 25,00 - -",
        ]),
        "V": ("IRPJ CSLL CBS CPP ISS IBS", [
            "25,00 15,00 17,15 28,85 8,40 5,60",
            "23,00 15,00 17,15 27,85 10,20 6,80",
            "24,00 15,00 18,15 23,85 11,40 7,60",
            "21,00 15,00 19,15 23,85 12,60 8,40",
            "23,00 12,50 17,15 23,85 14,10 9,40",
            "35,00 15,50 20,00 29,50 - -",
        ]),
    },
    2033: {
        "I": ("IRPJ CSLL CBS CPP IBS", [
            "5,50 3,50 15,50 41,50 34,00",
            "5,50 3,50 15,50 41,50 34,00",
            "5,50 3,50 15,50 42,00 33,50",
            "5,50 3,50 15,50 42,00 33,50",
            "5,50 3,50 15,50 42,00 33,50",
            "13,50 10,00 34,40 42,10 -",
        ]),
        "II": ("IRPJ CSLL CBS CPP IPI IBS", [
            "5,50 3,50 14,00 37,50 7,50 32,00",
            "5,50 3,50 14,00 37,50 7,50 32,00",
            "5,50 3,50 14,00 37,50 7,50 32,00",
            "5,50 3,50 14,00 37,50 7,50 32,00",
            "5,50 3,50 14,00 37,50 7,50 32,00",
            "8,50 7,50 25,50 23,50 35,00 -",
        ]),
        "III": ("IRPJ CSLL CBS CPP IBS", [
            "4,00 3,50 15,60 43,40 33,50",
            "4,00 3,50 17,10 43,40 32,00",
            "4,00 3,50 16,60 43,40 32,50",
            "4,00 3,50 16,60 43,40 32,50",
            "4,00 3,50 15,60 43,40 33,50",
            "35,00 15,00 19,50 30,50 -",
        ]),
        "IV": ("IRPJ CSLL CBS IBS", [
            "18,80 15,20 21,50 44,50",
            "19,80 15,20 25,00 40,00",
            "20,80 15,20 24,00 40,00",
            "17,80 19,20 23,00 40,00",
            "18,80 19,20 22,00 40,00",
            "53,50 21,50 25,00 -",
        ]),
        "V": ("IRPJ CSLL CBS CPP IBS", [
            "25,00 15,00 17,15 28,85 14,00",
            "23,00 15,00 17,15 27,85 17,00",
            "24,00 15,00 18,15 23,85 19,00",
            "21,00 15,00 19,15 23,85 21,00",
            "23,00 12,50 17,15 23,85 23,50",
            "35,00 15,50 20,00 29,50 -",
        ]),
    },
}

# Nota (*), 5ª faixa acima de 14,92537% (III) ou 12,5% (IV): ISS fixo no
# teto do ano e (efetiva - teto) x estes percentuais. De 2033 em diante não há.
TETO_LEI = {
    2029: ("4,5", {
        "III": ("IRPJ CSLL CBS CPP IBS", "5,73 5,01 22,33 62,13 4,8"),
        "IV": ("IRPJ CSLL CBS IBS", "29,38 30 34,38 6,25"),
    }),
    2030: ("4", {
        "III": ("IRPJ CSLL CBS CPP IBS", "5,46 4,78 21,31 59,29 9,15"),
        "IV": ("IRPJ CSLL CBS IBS", "27,65 28,24 32,35 11,76"),
    }),
    2031: ("3,5", {
        "III": ("IRPJ CSLL CBS CPP IBS", "5,23 4,57 20,38 56,69 13,13"),
        "IV": ("IRPJ CSLL CBS IBS", "26,11 26,67 30,56 16,67"),
    }),
    2032: ("3", {
        "III": ("IRPJ CSLL CBS CPP IBS", "5,01 4,38 19,52 54,32 16,77"),
        "IV": ("IRPJ CSLL CBS IBS", "24,74 25,26 28,95 21,05"),
    }),
}


def _lei(colunas, linha):
    return {c: D(v.replace(",", ".")) / 100
            for c, v in zip(colunas.split(), linha.split()) if v != "-"}


def _reais(**valores):
    return {t: D(v) for t, v in valores.items()}


class TestTabela(unittest.TestCase):
    def test_igual_a_lei(self):
        self.assertEqual(set(PARTILHA_DESDE_2029), set(PARTILHA_LEI))
        for ano, anexos in PARTILHA_LEI.items():
            self.assertEqual(set(PARTILHA_DESDE_2029[ano]), set(ANEXOS))
            for anexo, (colunas, linhas) in anexos.items():
                for n, linha in enumerate(linhas):
                    with self.subTest(ano=ano, anexo=anexo, faixa=n + 1):
                        self.assertEqual(PARTILHA_DESDE_2029[ano][anexo][n],
                                         _lei(colunas, linha))

    def test_cada_linha_soma_100(self):
        for ano, anexos in PARTILHA_DESDE_2029.items():
            for anexo, linhas in anexos.items():
                self.assertEqual(len(linhas), 6)
                for n, linha in enumerate(linhas):
                    with self.subTest(ano=ano, anexo=anexo, faixa=n + 1):
                        self.assertEqual(sum(linha.values()), 1)

    def test_sexta_faixa_so_federal(self):
        for ano, anexos in PARTILHA_DESDE_2029.items():
            for anexo, linhas in anexos.items():
                self.assertFalse({"ICMS", "ISS", "IBS"} & set(linhas[5]), (ano, anexo))

    def test_de_2033_em_diante_sem_icms_nem_iss(self):
        for anexo, linhas in PARTILHA_DESDE_2029[2033].items():
            for linha in linhas:
                self.assertFalse({"ICMS", "ISS"} & set(linha), anexo)

    def test_teto_do_iss_igual_a_lei(self):
        self.assertEqual(set(TETO_ISS_DESDE_2029), {2029, 2030, 2031, 2032})
        for ano, (maximo, notas) in TETO_LEI.items():
            iss_maximo, teto = TETO_ISS_DESDE_2029[ano]
            self.assertEqual(iss_maximo, D(maximo.replace(",", ".")) / 100)
            self.assertEqual(set(teto), {"III", "IV"})
            for anexo, (colunas, linha) in notas.items():
                with self.subTest(ano=ano, anexo=anexo):
                    self.assertEqual(teto[anexo], _lei(colunas, linha))


class TestParcelas(unittest.TestCase):
    def test_anexo_i_primeira_faixa_2029(self):
        # efetiva = 4%; DAS = 10.000 x 4% = 400,00. IRPJ 400 x 5,50% = 22,00;
        # CSLL x 3,50% = 14,00; CBS x 15,50% = 62,00; CPP x 41,50% = 166,00;
        # ICMS x 30,60% = 122,40; IBS x 3,40% = 13,60
        self.assertEqual(parcelas_das("I", 150_000, 10_000, ano=2029), _reais(
            IRPJ="22.00", CSLL="14.00", CBS="62.00", CPP="166.00", ICMS="122.40",
            IBS="13.60"))

    def test_anexo_i_primeira_faixa_2033_e_depois(self):
        # sem ICMS: IBS 400 x 34,00% = 136,00; o resto como em 2029
        esperado = _reais(IRPJ="22.00", CSLL="14.00", CBS="62.00", CPP="166.00",
                          IBS="136.00")
        for ano in (2033, 2040):
            with self.subTest(ano=ano):
                self.assertEqual(parcelas_das("I", 150_000, 10_000, ano=ano), esperado)

    def test_anexo_i_sexta_faixa_so_federal(self):
        # efetiva = (4.000.000 x 19% - 378.000) / 4.000.000 = 9,55%; DAS 9.550,00
        # IRPJ 13,50% = 1.289,25; CSLL 10% = 955,00; CBS 34,40% = 3.285,20;
        # CPP 42,10% = 4.020,55. ICMS e IBS fora do DAS.
        self.assertEqual(parcelas_das("I", 4_000_000, 100_000, ano=2029), _reais(
            IRPJ="1289.25", CSLL="955.00", CBS="3285.20", CPP="4020.55"))

    def test_anexo_iii_quinta_faixa_com_teto_de_4_5(self):
        # efetiva = 16,812% (como em 2026); ISS 30,15% x 16,812% > 4,5%.
        # DAS 16.812,00; ISS 4,5% = 4.500,00; resto 12.312,00 x 5,73% = 705,4776,
        # x 5,01% = 616,8312, x 22,33% = 2.749,2696, x 62,13% = 7.649,4456,
        # x 4,8% = 590,976. Faltam 3 centavos: CBS, IRPJ e IBS (maiores restos).
        self.assertEqual(parcelas_das("III", 3_000_000, 100_000, ano=2029), _reais(
            IRPJ="705.48", CSLL="616.83", CBS="2749.27", CPP="7649.44", IBS="590.98",
            ISS="4500.00"))

    def test_anexo_iv_nota_que_soma_100_01(self):
        # efetiva = 15,874%; ISS 36% x 15,874% > 4,5%. DAS 15.874,00; ISS 4.500,00;
        # resto 11.374,00. A nota de 2029 soma 100,01% (29,38 + 30 + 34,38 + 6,25):
        # aplicada na proporção, IRPJ 11.374 x 29,38 / 100,01 = 3.341,347;
        # CSLL x 30 / 100,01 = 3.411,859; CBS x 34,38 / 100,01 = 3.909,990;
        # IBS x 6,25 / 100,01 = 710,804. Faltam 2 centavos: CSLL e IRPJ.
        self.assertEqual(parcelas_das("IV", 3_000_000, 100_000, ano=2029), _reais(
            IRPJ="3341.35", CSLL="3411.86", CBS="3909.99", IBS="710.80", ISS="4500.00"))

    def test_anexo_iii_quinta_faixa_2033_sem_teto(self):
        # sem ISS, sem nota: DAS 16.812,00 x 4% = 672,48 (IRPJ), x 3,5% = 588,42,
        # x 15,60% = 2.622,672 (CBS), x 43,40% = 7.296,408 (CPP), x 33,50% =
        # 5.632,02 (IBS). Falta 1 centavo: CPP (resto 0,008).
        self.assertEqual(parcelas_das("III", 3_000_000, 100_000, ano=2033), _reais(
            IRPJ="672.48", CSLL="588.42", CBS="2622.67", CPP="7296.41", IBS="5632.02"))

    def test_toda_faixa_de_todo_anexo_bate_com_a_lei(self):
        # Uma receita por faixa e um ano por tabela; cada parcela a menos de 1
        # centavo da conta exata e a soma é o DAS da biblioteca.
        rbt12_por_faixa = (150_000, 300_000, 600_000, 1_500_000, 3_000_000, 4_200_000)
        receita = D(100_000)
        for inicio, anexos in PARTILHA_LEI.items():
            nota = TETO_LEI.get(inicio)
            for anexo, (colunas, linhas) in anexos.items():
                for n, rbt12 in enumerate(rbt12_por_faixa):
                    ano = 2035 if inicio == 2033 else inicio
                    with self.subTest(ano=ano, anexo=anexo, faixa=n + 1):
                        das = valor_devido(anexo, rbt12, receita, ano=ano)
                        p = parcelas_das(anexo, rbt12, receita, ano=ano)
                        self.assertEqual(sum(p.values()), das)
                        efetiva = aliquota_efetiva(anexo, rbt12, ano=ano)
                        lei = _lei(colunas, linhas[n])
                        com_nota = nota and n == 4 and anexo in nota[1]
                        maximo = D(nota[0].replace(",", ".")) / 100 if com_nota else None
                        if com_nota and efetiva * lei["ISS"] > maximo:
                            pesos = _lei(*nota[1][anexo])
                            soma = sum(pesos.values())
                            exatos = {t: receita * (efetiva - maximo) * x / soma
                                      for t, x in pesos.items()}
                            exatos["ISS"] = receita * maximo
                        else:
                            exatos = {t: receita * efetiva * x for t, x in lei.items()}
                        self.assertEqual(set(p), set(exatos))
                        for t in p:
                            self.assertLess(abs(p[t] - exatos[t]), D("0.01"), t)

    def test_o_teto_cai_meio_ponto_por_ano(self):
        for ano, iss in ((2029, "4500.00"), (2030, "4000.00"), (2031, "3500.00"),
                         (2032, "3000.00")):
            for anexo in ("III", "IV"):
                with self.subTest(ano=ano, anexo=anexo):
                    self.assertEqual(parcelas_das(anexo, 3_000_000, 100_000, ano=ano)["ISS"],
                                     D(iss))


if __name__ == "__main__":
    unittest.main()
