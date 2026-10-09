"""Critérios de aceite 2 a 5 da especificação, mais a validação da entrada.

Fontes legais (LC 123/2006 na redação da LC 155/2016, lida no site da Câmara
dos Deputados em 09/10/2026, URL em test_tabelas.py):
- art. 18, § 1º-A: fórmula da alíquota efetiva.
- art. 18, § 2º: início de atividade, faixas proporcionais aos meses.
- art. 18, §§ 5º-J e 5º-K: Fator R, folha / receita >= 28% -> Anexo III.
- art. 3º, II: teto de R$ 4,8 milhões; art. 13-A: sublimite de R$ 3,6 milhões.
Primeiros meses de atividade: Res. CGSN 140/2018, art. 22 (URL em TestPrimeirosMeses).
"""

import unittest
from decimal import Decimal

from simples_nacional import (
    LimiteExcedido,
    aliquota_efetiva,
    aliquota_inicio_atividade,
    anexo_por_fator_r,
    avisos,
    fator_r,
    rbt12_inicio_atividade,
    valor_devido,
    valor_devido_inicio_atividade,
)


class TestCaso146(unittest.TestCase):
    """mcp-fiscal-brasil, issue #146: comércio, RBT12 de R$ 4.500.000,00.

    Aquela ferramenta aplica a nominal de 19% (R$ 855.000,00 no ano). Pela lei:
    (4.500.000 x 19% - 378.000) / 4.500.000 = 477.000 / 4.500.000 = 10,60%.
    """

    def test_efetiva(self):
        self.assertEqual(aliquota_efetiva("I", 4_500_000, ano=2026), Decimal("0.106"))

    def test_ano_inteiro(self):
        self.assertEqual(valor_devido("I", 4_500_000, 4_500_000, ano=2026), Decimal("477000.00"))

    def test_mes(self):
        # 375.000 x 10,6% = 39.750,00; x 12 = 477.000,00
        self.assertEqual(valor_devido("I", 4_500_000, 375_000, ano=2026), Decimal("39750.00"))


class TestArredondamento(unittest.TestCase):

    def test_meio_centavo_sobe(self):
        # 12,625 x 4% = 0,505 -> 0,51 (ROUND_HALF_UP; half-even daria 0,50)
        self.assertEqual(valor_devido("I", 100_000, "12.625", ano=2026), Decimal("0.51"))

    def test_efetiva_sem_arredondar(self):
        # Anexo III, 4ª faixa: (240.000 - 35.640) / 1.500.000 = 0,13624, todos os dígitos
        self.assertEqual(aliquota_efetiva("III", 1_500_000, ano=2026), Decimal("0.13624"))


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
        self.assertEqual(aliquota_efetiva("I", 4_800_000, ano=2026), Decimal("0.11125"))

    def test_acima_do_teto_e_erro_explicado(self):
        for anexo in ("I", "II", "III", "IV", "V"):
            with self.subTest(anexo=anexo):
                with self.assertRaises(LimiteExcedido) as erro:
                    aliquota_efetiva(anexo, "4800000.01", ano=2026)
                mensagem = str(erro.exception)
                self.assertIn("4.800.000,00", mensagem)
                self.assertIn("art. 3", mensagem)

    def test_valor_devido_tambem_recusa(self):
        with self.assertRaises(LimiteExcedido):
            valor_devido("I", 5_000_000, 400_000, ano=2026)

    def test_limite_excedido_e_value_error(self):
        self.assertTrue(issubclass(LimiteExcedido, ValueError))


class TestAvisos(unittest.TestCase):

    def test_sem_aviso_ate_o_sublimite(self):
        self.assertEqual(avisos(3_600_000), [])
        for ano in (2026, 2027, 2033):
            self.assertEqual(avisos(3_600_000, ano=ano), [])

    def test_sublimite(self):
        texto = " ".join(avisos("3600000.01"))
        self.assertIn("3.600.000,00", texto)
        self.assertIn("ICMS", texto)
        self.assertIn("ISS", texto)

    def test_sublimite_ate_2026_depende_da_receita_do_ano(self):
        # Res. CGSN 140, art. 21, III, b: sublimite não excedido no ano, ICMS e
        # ISS seguem no DAS pela 5ª faixa; o excesso se mede no ano (art. 24)
        for texto in (" ".join(avisos(4_500_000)), " ".join(avisos(4_500_000, ano=2026))):
            self.assertIn("receita acumulada no ano-calendário", texto)
            self.assertIn("art. 21, III, b", texto)
            self.assertIn("5ª faixa", texto)
            self.assertIn("art. 24", texto)
            self.assertNotIn("IBS", texto)

    def test_sublimite_a_partir_de_2027_inclui_o_ibs(self):
        # LC 214, art. 517 (efeito em 01/01/2027): o art. 13-A passa a valer
        # para o IBS; a Res. CGSN 190 revoga o art. 21, III, b
        texto = " ".join(avisos(4_500_000, ano=2027))
        self.assertIn("ICMS, ISS e IBS", texto)
        self.assertIn("LC 214/2025, art. 517", texto)
        self.assertIn("CBS", texto)
        self.assertIn("receita acumulada no ano-calendário", texto)
        self.assertNotIn("art. 21, III, b", texto)

    def test_sublimite_a_partir_de_2033_so_o_ibs(self):
        # LC 214, art. 518 (efeito em 01/01/2033): o art. 13-A fala só do IBS
        texto = " ".join(avisos(4_500_000, ano=2033))
        self.assertIn("art. 518", texto)
        self.assertIn("o IBS sai do DAS", texto)
        self.assertNotIn("ICMS", texto)
        self.assertNotIn("ISS ", texto)

    def test_ano_invalido(self):
        with self.assertRaises(TypeError):
            avisos(4_500_000, ano="2027")
        with self.assertRaises(ValueError):
            avisos(4_500_000, ano=2017)

    def test_acima_do_limite(self):
        self.assertIn("4.800.000,00", " ".join(avisos(4_800_001)))
        self.assertIn("4.800.000,00", " ".join(avisos(4_800_001, ano=2027)))


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
        self.assertEqual(aliquota_efetiva("I", rbt12, ano=2026), Decimal("0.0565"))

    def test_meses_fora_do_intervalo(self):
        for meses in (0, -1, 12):
            with self.subTest(meses=meses):
                with self.assertRaises(ValueError):
                    rbt12_inicio_atividade(90_000, meses)


class TestPrimeirosMeses(unittest.TestCase):
    """Res. CGSN 140/2018, art. 22, lida no portal de normas da Receita em 09/10/2026
    (https://normasinternet2.receita.fazenda.gov.br/#/consulta/externa/92278).

    Até 2026: 1º mês, receita do próprio mês x 12 (§ 2º); do 2º ao 12º, média
    dos meses anteriores x 12 (§ 3º).
    A partir de 2027 (Res. CGSN 190/2026, efeitos em 01/01/2027,
    https://normasinternet2.receita.fazenda.gov.br/#/consulta/externa/152832):
    1º e 2º mês, alíquota da 1ª faixa (§ 2º, I); do 3º ao 13º, média dos meses
    antecedentes ao mês anterior x 12 (§ 2º, II).

    Conta de referência, Anexo I: RBT12 360.000 está na 2ª faixa (7,3%, PD 5.940):
    (360.000 x 7,3% - 5.940) / 360.000 = 20.340 / 360.000 = 5,65%.
    """

    def test_2026_primeiro_mes_anualiza_o_proprio_mes(self):
        # 30.000 x 12 = 360.000 -> 5,65%; 30.000 x 5,65% = 1.695,00
        self.assertEqual(aliquota_inicio_atividade("I", [30_000], ano=2026), Decimal("0.0565"))
        self.assertEqual(valor_devido_inicio_atividade("I", [30_000], ano=2026), Decimal("1695.00"))

    def test_2026_segundo_mes_usa_so_o_primeiro(self):
        # 30.000 x 12 / 1 = 360.000 -> 5,65%; 50.000 x 5,65% = 2.825,00
        self.assertEqual(valor_devido_inicio_atividade("I", [30_000, 50_000], ano=2026),
                         Decimal("2825.00"))

    def test_2026_quarto_mes_media_dos_tres_anteriores(self):
        # (20.000 + 40.000 + 30.000) / 3 x 12 = 360.000 -> 5,65%
        # 99.999 x 5,65% = 5.649,9435 -> 5.649,94
        receitas = [20_000, 40_000, 30_000, 99_999]
        self.assertEqual(valor_devido_inicio_atividade("I", receitas, ano=2026), Decimal("5649.94"))

    def test_2026_decimo_segundo_mes_e_o_ultimo(self):
        # 11 meses de 15.000: 15.000 x 12 = 180.000, teto da 1ª faixa -> 4%; 10.000 x 4% = 400,00
        receitas = [15_000] * 11 + [10_000]
        self.assertEqual(valor_devido_inicio_atividade("I", receitas, ano=2026), Decimal("400.00"))
        with self.assertRaises(ValueError):
            aliquota_inicio_atividade("I", receitas + [10_000], ano=2026)

    def test_2026_primeiro_mes_alto_cai_na_sexta_faixa(self):
        # 400.000 x 12 = 4.800.000 -> 6ª faixa (19%, PD 378.000)
        # (4.800.000 x 19% - 378.000) / 4.800.000 = 534.000 / 4.800.000 = 11,125%
        # 400.000 x 11,125% = 44.500,00
        self.assertEqual(valor_devido_inicio_atividade("I", [400_000], ano=2026), Decimal("44500.00"))

    def test_2027_primeiro_e_segundo_mes_primeira_faixa(self):
        # mesma receita do caso acima: em 2027 vale a 1ª faixa do Anexo I, 4%
        # 400.000 x 4% = 16.000,00; 2º mês, 10.000 x 4% = 400,00
        self.assertEqual(aliquota_inicio_atividade("I", [400_000], ano=2027), Decimal("0.04"))
        self.assertEqual(valor_devido_inicio_atividade("I", [400_000], ano=2027), Decimal("16000.00"))
        self.assertEqual(valor_devido_inicio_atividade("I", [400_000, 10_000], ano=2027),
                         Decimal("400.00"))
        # Anexo III, 1ª faixa: 6%; 10.000 x 6% = 600,00
        self.assertEqual(valor_devido_inicio_atividade("III", [10_000], ano=2027), Decimal("600.00"))

    def test_2027_terceiro_mes_usa_so_o_primeiro(self):
        # meses antecedentes ao anterior: só o 1º. 30.000 x 12 = 360.000 -> 5,65%
        # 70.000 x 5,65% = 3.955,00
        self.assertEqual(valor_devido_inicio_atividade("I", [30_000, 50_000, 70_000], ano=2027),
                         Decimal("3955.00"))

    def test_2027_ignora_o_mes_anterior_ao_de_apuracao(self):
        # 5º mês: média do 1º ao 3º, (20.000 + 40.000 + 30.000) / 3 x 12 = 360.000 -> 5,65%;
        # o 4º (77.777) fica de fora. 10.000 x 5,65% = 565,00
        receitas = [20_000, 40_000, 30_000, 77_777, 10_000]
        self.assertEqual(valor_devido_inicio_atividade("I", receitas, ano=2027), Decimal("565.00"))

    def test_2027_decimo_terceiro_mes_e_o_ultimo(self):
        # 13º mês: média do 1º ao 11º, 30.000 x 12 = 360.000 -> 5,65%; o 12º fica de fora
        # 1.000 x 5,65% = 56,50
        receitas = [30_000] * 11 + [999_999, 1_000]
        self.assertEqual(valor_devido_inicio_atividade("I", receitas, ano=2027), Decimal("56.50"))
        with self.assertRaises(ValueError):
            aliquota_inicio_atividade("I", receitas + [1_000], ano=2027)

    def test_receita_zero_usa_a_primeira_faixa(self):
        # RBT12 zero não tem alíquota pela fórmula; convenção: nominal da 1ª faixa
        # (o limite da fórmula, que na 1ª faixa não tem parcela a deduzir).
        self.assertEqual(aliquota_inicio_atividade("I", [0], ano=2026), Decimal("0.04"))
        # 2º mês com o 1º zerado: 5.000 x 4% = 200,00
        self.assertEqual(valor_devido_inicio_atividade("I", [0, 5_000], ano=2026), Decimal("200.00"))

    def test_entradas_invalidas(self):
        with self.assertRaises(ValueError):
            aliquota_inicio_atividade("I", [], ano=2026)
        with self.assertRaises(ValueError):
            aliquota_inicio_atividade("I", [10_000, -1], ano=2026)
        with self.assertRaises(TypeError):
            aliquota_inicio_atividade("I", "30000", ano=2026)
        with self.assertRaises(TypeError):
            aliquota_inicio_atividade("I", [30_000.0], ano=2026)
        with self.assertRaises(TypeError):
            aliquota_inicio_atividade("I", [30_000])  # ano obrigatório
        with self.assertRaises(ValueError):
            aliquota_inicio_atividade("VI", [30_000], ano=2027)
        with self.assertRaises(ValueError):
            aliquota_inicio_atividade("I", [30_000], ano=2017)


class TestEntradas(unittest.TestCase):

    def test_float_recusado(self):
        # float erra centavo: 0.1 + 0.2 != 0.3
        with self.assertRaises(TypeError):
            aliquota_efetiva("I", 4500000.0, ano=2026)

    def test_anexo_invalido(self):
        for anexo in ("VI", "", "1", None):
            with self.subTest(anexo=anexo):
                with self.assertRaises(ValueError):
                    aliquota_efetiva(anexo, 100_000, ano=2026)

    def test_anexo_minusculo(self):
        self.assertEqual(aliquota_efetiva("iii", 150_000, ano=2026), Decimal("0.06"))

    def test_rbt12_zero_ou_negativo(self):
        for rbt12 in (0, -1):
            with self.subTest(rbt12=rbt12):
                with self.assertRaises(ValueError):
                    aliquota_efetiva("I", rbt12, ano=2026)

    def test_receita_negativa(self):
        with self.assertRaises(ValueError):
            valor_devido("I", 100_000, -1, ano=2026)

    def test_texto_invalido(self):
        with self.assertRaises(ValueError):
            aliquota_efetiva("I", "abc", ano=2026)


class TestAno(unittest.TestCase):
    """O ano-calendário de apuração escolhe a tabela: sem ele, erro."""

    def test_ano_obrigatorio(self):
        with self.assertRaises(TypeError):
            aliquota_efetiva("I", 100_000)
        with self.assertRaises(TypeError):
            valor_devido("I", 100_000, 1_000)

    def test_ano_tem_de_ser_int(self):
        for ano in ("2027", 2027.0, True, None):
            with self.subTest(ano=ano):
                with self.assertRaises(TypeError):
                    aliquota_efetiva("I", 100_000, ano=ano)

    def test_antes_de_2018_nao_coberto(self):
        # A tabela da LC 155/2016 vale desde 01/01/2018.
        with self.assertRaises(ValueError) as erro:
            aliquota_efetiva("I", 100_000, ano=2017)
        self.assertIn("2018", str(erro.exception))


class TestEntradasErradas(unittest.TestCase):

    def test_anexo_que_nao_e_texto(self):
        with self.assertRaisesRegex(ValueError, "^anexo: esperado I"):
            aliquota_efetiva(["I"], 100_000, ano=2026)

    def test_receitas_que_nao_sao_lista(self):
        for receitas in ({1: 30_000}, {30_000}, "30000"):
            with self.subTest(receitas=type(receitas).__name__):
                with self.assertRaisesRegex(TypeError, "^receitas: lista"):
                    valor_devido_inicio_atividade("I", receitas, ano=2026)


if __name__ == "__main__":
    unittest.main()
