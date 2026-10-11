"""Adaptador da vitrine (vitrine/vitrine.py): a conta que a página mostra.

O `test_vitrine.py` é o do modelo comum e confere só o formato; aqui ficam os
valores, com a conta feita à mão, e as entradas que a página pode receber.
"""
import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("montar", RAIZ / "vitrine" / "montar.py")
montar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(montar)
vitrine = montar.carregar_adaptador(RAIZ)


def entradas(anexo="III", ano="2026", rbt12="1.500.000,00", receita_mes="100.000,00", folha12="",
             receitas="", mes_inicio=""):
    return {"anexo": anexo, "ano": ano, "rbt12": rbt12, "receita_mes": receita_mes, "folha12": folha12,
            "receitas": receitas, "mes_inicio": mes_inicio}


class TestAdaptador(unittest.TestCase):
    def rodar(self, **campos):
        e = entradas(**campos)
        res = vitrine.executar(e)
        self.assertEqual(montar.conferir_resultado(res, e), [])
        self.assertIn("não substitui o PGDAS-D nem o contador", res["aviso"])
        return res

    def passo(self, res, nome):
        return [valor for passo, valor in res["tabela"]["linhas"] if passo == nome]

    def test_exemplo_da_pagina(self):
        # Anexo III, 4ª faixa (até 1,8 mi): 16%, parcela 35.640.
        # (1.500.000 × 0,16 − 35.640) ÷ 1.500.000 = 204.360 ÷ 1.500.000 = 13,624%;
        # × 100.000 = 13.624,00.
        res = self.rodar()
        self.assertEqual(res["resumo"], "Alíquota efetiva de 13,6240% na 4ª faixa do Anexo III: "
                                        "R$ 13.624,00 no mês, pela tabela de 2026.")
        self.assertEqual(self.passo(res, "Parcela a deduzir"), ["R$ 35.640,00"])
        self.assertEqual(self.passo(res, "Aviso"), [])

    def test_fator_r(self):
        # Folha 420.000 ÷ 1.500.000 = 28%: Anexo III, mesmo valor do exemplo.
        res = self.rodar(anexo="Fator R", folha12="420.000,00")
        self.assertIn("R$ 13.624,00", res["resumo"])
        self.assertEqual(self.passo(res, "Fator R (folha ÷ RBT12)"), ["28,0000%: 28% ou mais, Anexo III"])
        # Folha 300.000: 20%, Anexo V, 4ª faixa: 20,5%, parcela 17.100.
        # (307.500 − 17.100) ÷ 1.500.000 = 19,36%; × 100.000 = 19.360,00.
        res = self.rodar(anexo="fator-r", folha12="300000")
        self.assertIn("19,3600% na 4ª faixa do Anexo V: R$ 19.360,00", res["resumo"])

    def test_fator_r_cortado_nao_vira_28(self):
        # 419.999,99 ÷ 1.500.000 = 27,99999...%: Anexo V, e o texto não diz 28,0000%.
        res = self.rodar(anexo="Fator R", folha12="419.999,99")
        self.assertEqual(self.passo(res, "Fator R (folha ÷ RBT12)"), ["27,9999%: abaixo de 28%, Anexo V"])

    def test_acima_do_sublimite_avisa(self):
        # Anexo I, 6ª faixa: (4.500.000 × 19% − 378.000) ÷ 4.500.000 = 10,6%; × 375.000 = 39.750,00.
        res = self.rodar(anexo="i", rbt12="4500000", receita_mes="375.000")
        self.assertTrue(res["resumo"].startswith("Alíquota efetiva de 10,6000% na 6ª faixa do Anexo I: R$ 39.750,00"))
        self.assertTrue(res["resumo"].endswith("Há aviso na tabela."))
        self.assertEqual(len(self.passo(res, "Aviso")), 1)

    def tributos(self, res):
        return {passo[len("No DAS: "):]: valor for passo, valor in res["tabela"]["linhas"]
                if passo.startswith("No DAS: ")}

    def test_reparticao_por_tributo(self):
        # Exemplo da página, 4ª faixa do Anexo III em 2026 (LC 123, Anexo III,
        # repartição): IRPJ 4%, CSLL 3,5%, COFINS 13,64%, PIS 2,96%, CPP 43,4%,
        # ISS 32,5% da efetiva de 13,624%. COFINS: 13,624% × 13,64% = 1,8583136%,
        # × 100.000 = 1.858,31; a soma das parcelas é o valor do mês, 13.624,00.
        res = self.rodar()
        self.assertEqual(self.tributos(res), {
            "IRPJ": "R$ 544,96 (0,5450% da receita)",
            "CSLL": "R$ 476,84 (0,4768% da receita)",
            "COFINS": "R$ 1.858,31 (1,8583% da receita)",
            "PIS": "R$ 403,27 (0,4033% da receita)",
            "CPP": "R$ 5.912,82 (5,9128% da receita)",
            "ISS": "R$ 4.427,80 (4,4278% da receita)",
        })
        # Acima do sublimite o ICMS fica fora; em 2027 entram CBS e IBS.
        res = self.rodar(anexo="I", rbt12="4500000", receita_mes="375.000")
        self.assertEqual(list(self.tributos(res)), ["IRPJ", "CSLL", "COFINS", "PIS", "CPP"])
        res = self.rodar(ano="2027")
        self.assertEqual(list(self.tributos(res)), ["IRPJ", "CSLL", "CBS", "CPP", "ISS", "IBS"])

    def test_fator_r_planejado(self):
        # RBT12 600.000, folha 120.000 (20%), receita 50.000, 3ª faixa.
        # V: (600.000 × 19,5% − 9.900) ÷ 600.000 = 17,85% → 8.925,00;
        # III: (600.000 × 13,5% − 17.640) ÷ 600.000 = 10,56% → 5.280,00.
        # Folha para 28%: 168.000, faltam 48.000.
        res = self.rodar(anexo="Fator R", rbt12="600.000", receita_mes="50.000", folha12="120.000")
        self.assertEqual(self.passo(res, "Folha para 28%"), ["R$ 168.000,00: faltam R$ 48.000,00"])
        self.assertEqual(self.passo(res, "Valor no Anexo V"), ["R$ 8.925,00"])
        self.assertEqual(self.passo(res, "Valor no Anexo III"), ["R$ 5.280,00"])
        self.assertEqual(self.passo(res, "Diferença"), ["o III sai R$ 3.645,00 mais barato"])
        self.assertIn("pró-labore", self.passo(res, "Atenção")[0])
        self.assertTrue(res["resumo"].endswith(
            "Com mais R$ 48.000,00 de folha em 12 meses, o Anexo III sairia "
            "R$ 3.645,00 mais barato no DAS."))
        # Já em 28%: nada falta; V na 4ª faixa 19,36% → 19.360,00 contra 13.624,00.
        res = self.rodar(anexo="Fator R", folha12="420.000,00")
        self.assertEqual(self.passo(res, "Folha para 28%"), ["R$ 420.000,00: a de hoje já chega"])
        self.assertEqual(self.passo(res, "Diferença"), ["o III sai R$ 5.736,00 mais barato"])
        self.assertNotIn("Com mais", res["resumo"])
        # 6ª faixa: V 19,25% → 77.000,00; III 19,5% → 78.000,00. O resumo não sugere o III.
        res = self.rodar(anexo="Fator R", rbt12="4.800.000", receita_mes="400.000", folha12="0")
        self.assertEqual(self.passo(res, "Diferença"), ["o V sai R$ 1.000,00 mais barato"])
        self.assertNotIn("Com mais", res["resumo"])
        res = self.rodar(anexo="Fator R", receita_mes="0", folha12="0")
        self.assertEqual(self.passo(res, "Diferença"), ["o mesmo valor"])
        self.assertNotIn("Com mais", res["resumo"])
        # Com o anexo informado não há planejamento.
        self.assertEqual(self.passo(self.rodar(), "Folha para 28%"), [])

    def test_tabela_de_2027(self):
        res = self.rodar(ano="2027")
        self.assertEqual(self.passo(res, "Tabela"),
                         ["LC 214/2025, Anexos XVIII a XXII, anos-calendário 2027 e 2028"])

    def test_campos_vazios_dizem_o_que_falta(self):
        res = self.rodar(anexo=" ", ano="", rbt12="", receita_mes="")
        self.assertEqual(res["resumo"], "Faltam o anexo, o ano de apuração, a receita dos 12 meses "
                                        "(RBT12) e a receita do mês.")
        self.assertNotIn("tabela", res)
        res = self.rodar(receita_mes="")
        self.assertEqual(res["resumo"], "Falta a receita do mês.")
        res = self.rodar(anexo="Fator R")
        self.assertTrue(res["resumo"].startswith("Falta a folha dos 12 meses"))

    def test_entrada_invalida_vira_resumo(self):
        casos = {
            "número": (dict(rbt12="1,000.50"), "RBT12: '1,000.50' não é número"),
            "ano curto": (dict(ano="26"), "ano: '26' não é um ano"),
            "ano antigo": (dict(ano="2017"), "ano 2017"),
            "anexo": (dict(anexo="VI"), "anexo: esperado I, II, III, IV ou V"),
            "acima do limite": (dict(rbt12="4.800.000,01"), "acima do limite de R$ 4.800.000,00"),
            "receita negativa": (dict(receita_mes="-1"), "receita"),
            "folha": (dict(anexo="Fator R", folha12="abc"), "folha dos 12 meses: 'abc' não é número"),
        }
        for nome, (campos, trecho) in casos.items():
            with self.subTest(nome):
                res = self.rodar(**campos)
                self.assertTrue(res["resumo"].startswith("Não deu para calcular. "), res["resumo"])
                self.assertIn(trecho, res["resumo"])
                self.assertNotIn("tabela", res)



class TestInicioDeAtividade(unittest.TestCase):
    """Res. CGSN 140, art. 22, com a conta à mão; a mesma do MCP e da linha de comando."""

    rodar, passo = TestAdaptador.rodar, TestAdaptador.passo

    def inicio(self, receitas, **campos):
        return self.rodar(rbt12="", receita_mes="", receitas=receitas, **campos)

    def test_terceiro_mes_de_2026(self):
        # (30.000 + 40.000) ÷ 2 × 12 = 420.000, 3ª faixa do Anexo III (13,5%, 17.640):
        # (420.000 × 0,135 − 17.640) ÷ 420.000 = 39.060 ÷ 420.000 = 9,3%; × 50.000 = 4.650,00
        res = self.inicio("30.000,00;40.000,00;50.000,00", mes_inicio="10")
        self.assertEqual(res["resumo"], "Alíquota efetiva de 9,3000% na 3ª faixa do Anexo III: "
                                        "R$ 4.650,00 no 3º mês de atividade, pela tabela de 2026.")
        self.assertEqual(self.passo(res, "Mês de atividade"), ["3º"])
        (regra,) = self.passo(res, "Regra do início")
        self.assertIn("art. 22, § 3º", regra)
        self.assertTrue(regra.endswith("= R$ 420.000,00"), regra)
        self.assertEqual(self.passo(res, "Faixa"), ["3ª do Anexo III, RBT12 até R$ 720.000,00"])
        self.assertTrue(self.passo(res, "Valor do mês")[0].startswith("R$ 4.650,00 "))
        # a repartição soma o DAS: 186,00 + 162,75 + 634,26 + 137,64 + 2.018,10 + 1.511,25
        parcelas = [valor for passo, valor in res["tabela"]["linhas"] if passo.startswith("No DAS: ")]
        self.assertEqual(sum(Decimal(p.split()[1].replace(".", "").replace(",", "."))
                             for p in parcelas), Decimal("4650.00"))
        self.assertEqual(self.passo(res, "Aviso"), [])  # 120.000 cabe em 900.000

    def test_primeiro_mes_de_2026(self):
        # 20.000 × 12 = 240.000, 2ª faixa (11,2%, 9.360): 17.520 ÷ 240.000 = 7,3%; × 20.000 = 1.460,00
        res = self.inicio("20.000")
        self.assertIn("R$ 1.460,00 no 1º mês", res["resumo"])
        self.assertIn("art. 22, § 2º", self.passo(res, "Regra do início")[0])

    def test_dois_primeiros_meses_de_2027_na_primeira_faixa(self):
        # Res. CGSN 190/2026: 1ª faixa do Anexo III de 2027, 6%; 20.000 × 0,06 = 1.200,00
        res = self.inicio("10.000;20.000", ano="2027")
        self.assertIn("6,0000% na 1ª faixa", res["resumo"])
        self.assertIn("R$ 1.200,00 no 2º mês", res["resumo"])
        self.assertEqual(self.passo(res, "Faixa"), ["1ª do Anexo III"])
        self.assertEqual(self.passo(res, "Alíquota efetiva"), ["6,0000% = nominal da 1ª faixa"])
        self.assertIn("Res. CGSN 190/2026", self.passo(res, "Regra do início")[0])
        parcelas = [valor for passo, valor in res["tabela"]["linhas"] if passo.startswith("No DAS: ")]
        self.assertEqual(sum(Decimal(p.split()[1].replace(".", "").replace(",", "."))
                             for p in parcelas), Decimal("1200.00"))

    def test_sublimite_proporcional(self):
        # 400.000 × 3 = 1,2 mi; de outubro a dezembro, sublimite 300.000 × 3 = 900.000
        com = self.inicio("400.000;400.000;400.000", anexo="I", mes_inicio="10")
        (aviso,) = self.passo(com, "Aviso")
        self.assertIn("sublimite proporcional de R$ 900.000,00", aviso)
        self.assertTrue(com["resumo"].endswith(" Há aviso na tabela."))
        sem = self.inicio("400.000;400.000;400.000", anexo="I")
        (aviso,) = self.passo(sem, "Aviso")
        self.assertIn("informe o mês de início", aviso)

    def test_combinacoes_que_nao_valem(self):
        casos = {
            "RBT12 junto": (self.rodar(receitas="1"), "deixe em branco o RBT12"),
            "receita do mês junto": (self.rodar(rbt12="", receitas="1"), "deixe em branco o RBT12"),
            "Fator R": (self.inicio("1", anexo="Fator R"), "o Fator R não é calculado"),
            "mês sem receitas": (self.rodar(mes_inicio="3"), "só vale com as receitas"),
            "sem o anexo": (self.inicio("1", anexo=""), "Falta o anexo."),
        }
        for nome, (res, trecho) in casos.items():
            with self.subTest(nome):
                self.assertIn(trecho, res["resumo"])
                self.assertNotIn("tabela", res)

    def test_entrada_invalida_vira_resumo(self):
        casos = {
            "número": (dict(receitas="1;x"), "receitas: 'x' não é número"),
            "13 meses em 2026": (dict(receitas=";".join(["1"] * 13)), "de 1 a 12 meses"),
            "negativo": (dict(receitas="1;-1"), "negativo"),
            "mês 13": (dict(receitas="1", mes_inicio="13"), "mês de início: '13' não é mês"),
            "mês por extenso": (dict(receitas="1", mes_inicio="março"), "não é mês"),
        }
        for nome, (campos, trecho) in casos.items():
            with self.subTest(nome):
                res = self.inicio(**campos)
                self.assertTrue(res["resumo"].startswith("Não deu para calcular. "), res["resumo"])
                self.assertIn(trecho, res["resumo"])
                self.assertNotIn("tabela", res)


if __name__ == "__main__":
    unittest.main()
