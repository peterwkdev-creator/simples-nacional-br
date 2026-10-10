"""Repartição de 2027 e 2028 contra a lei, faixa a faixa.

Fonte: LC 214/2025, art. 519 e Anexos XVIII a XXII (nova redação dos Anexos
I a V da LC 123, vigência 1º/1/2027 a 31/12/2028), com a redação da LC
227/2026 no Anexo III. Texto atualizado lido no site da Câmara em 09/10/2026:
https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html

A repartição troca PIS e Cofins por CBS e IBS. Na 6ª faixa o IBS, o ICMS e
o ISS não têm parcela no DAS (LC 123, art. 13-A). A alíquota nominal e a
parcela a deduzir se testam em test_tabelas.py.
"""

import unittest
from decimal import Decimal

from simples_nacional.tabelas_reparticao import PARTILHA_2027_2028, TETO_ISS_2027_2028

# Repartição da lei, faixa a faixa, na ordem das colunas de cada anexo.
# Célula "-" ou vazia na lei = tributo fora do DAS na faixa (ausente aqui).
PARTILHA_LEI = {
    "I": ("IRPJ CSLL CBS CPP ICMS IBS", [
        "5,50 3,50 15,33 41,50 34,00 0,17",
        "5,50 3,50 15,33 41,50 34,00 0,17",
        "5,50 3,50 15,33 42,00 33,50 0,17",
        "5,50 3,50 15,33 42,00 33,50 0,17",
        "5,50 3,50 15,33 42,00 33,50 0,17",
        "13,58 10,06 34,02 42,34 - -",
    ]),
    "II": ("IRPJ CSLL CBS CPP IPI ICMS IBS", [
        "5,50 3,50 13,85 37,50 7,50 32,00 0,15",
        "5,50 3,50 13,85 37,50 7,50 32,00 0,15",
        "5,50 3,50 13,85 37,50 7,50 32,00 0,15",
        "5,50 3,50 13,85 37,50 7,50 32,00 0,15",
        "5,50 3,50 13,85 37,50 7,50 32,00 0,15",
        "8,53 7,53 25,22 23,59 35,13 - -",
    ]),
    "III": ("IRPJ CSLL CBS CPP ISS IBS", [
        "4,00 3,50 15,43 43,40 33,50 0,17",
        "4,00 3,50 16,91 43,40 32,00 0,19",
        "4,00 3,50 16,41 43,40 32,50 0,19",
        "4,00 3,50 16,41 43,40 32,50 0,19",
        "4,00 3,50 15,43 43,40 33,50 0,17",
        "35,09 15,04 19,29 30,58 - -",
    ]),
    "IV": ("IRPJ CSLL CBS ISS IBS", [
        "18,80 15,20 21,26 44,50 0,24",
        "19,80 15,20 24,73 40,00 0,27",
        "20,80 15,20 23,74 40,00 0,26",
        "17,80 19,20 22,75 40,00 0,25",
        "18,80 19,20 21,76 40,00 0,24",
        "53,71 21,59 24,70 - -",
    ]),
    "V": ("IRPJ CSLL CBS CPP ISS IBS", [
        "25,00 15,00 16,96 28,85 14,00 0,19",
        "23,00 15,00 16,96 27,85 17,00 0,19",
        "24,00 15,00 17,95 23,85 19,00 0,20",
        "21,00 15,00 18,94 23,85 21,00 0,21",
        "23,00 12,50 16,96 23,85 23,50 0,19",
        "35,10 15,54 19,78 29,58 - -",
    ]),
}

# Nota (*) dos Anexos III e IV: ISS limitado a 5% da receita; na 5ª faixa,
# acima do limite, cada tributo leva (efetiva - 5%) x o percentual abaixo.
TETO_ISS_LEI = {
    "III": ("IRPJ CSLL CBS CPP IBS", "6,02 5,26 23,20 65,26 0,26"),
    "IV": ("IRPJ CSLL CBS IBS", "31,33 32,00 36,27 0,40"),
}


def _pct(texto):
    return Decimal(texto.replace(",", ".")) / 100


def _linha(colunas, valores):
    return {c: _pct(v) for c, v in zip(colunas.split(), valores.split()) if v != "-"}


class TestPartilha(unittest.TestCase):

    def test_igual_a_lei(self):
        for anexo, (colunas, linhas) in PARTILHA_LEI.items():
            for n, valores in enumerate(linhas, 1):
                with self.subTest(anexo=anexo, faixa=n):
                    self.assertEqual(PARTILHA_2027_2028[anexo][n - 1], _linha(colunas, valores))

    def test_cada_linha_soma_100(self):
        for anexo, linhas in PARTILHA_2027_2028.items():
            for n, linha in enumerate(linhas, 1):
                with self.subTest(anexo=anexo, faixa=n):
                    self.assertEqual(sum(linha.values()), Decimal(1))

    def test_sexta_faixa_sem_ibs_icms_iss(self):
        for anexo, linhas in PARTILHA_2027_2028.items():
            with self.subTest(anexo=anexo):
                self.assertFalse({"IBS", "ICMS", "ISS"} & set(linhas[5]))

    def test_teto_do_iss_igual_a_lei(self):
        self.assertEqual(set(TETO_ISS_2027_2028), set(TETO_ISS_LEI))
        for anexo, (colunas, valores) in TETO_ISS_LEI.items():
            with self.subTest(anexo=anexo):
                linha = _linha(colunas, valores)
                self.assertEqual(TETO_ISS_2027_2028[anexo], linha)
                # mais os 5% do ISS, fecha a receita inteira
                self.assertEqual(sum(linha.values()), Decimal(1))


if __name__ == "__main__":
    unittest.main()
