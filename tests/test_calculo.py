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
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

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

    def test_rbt12_zero_ou_negativo_e_erro(self):
        for rbt12 in (0, -5, "0.00"):
            with self.subTest(rbt12=rbt12):
                with self.assertRaisesRegex(ValueError, "rbt12 tem de ser positivo"):
                    avisos(rbt12)

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


class TestContextoDecimalDeQuemChama(unittest.TestCase):
    """O getcontext() de quem usa a biblioteca não muda as contas dela."""

    def test_precisao_e_arredondamento_alheios(self):
        import simples_nacional as sn
        contas = {
            "aliquota_efetiva": lambda: sn.aliquota_efetiva("III", "1234567.89", ano=2026),
            "valor_devido": lambda: sn.valor_devido("III", "1234567.89", "131131.58", ano=2026),
            "valor_devido_icms_iss": lambda: sn.valor_devido(
                "III", "4123456.78", "131131.58", ano=2026, icms_iss_no_das=True),
            "fator_r": lambda: sn.fator_r("345678.9", "1234567.89"),
            "rbt12_inicio_atividade": lambda: sn.rbt12_inicio_atividade("1000000", 7),
            "aliquota_inicio_atividade": lambda: sn.aliquota_inicio_atividade(
                "I", ["30000", "50000", "70000.01"], ano=2026),
            "valor_devido_inicio_atividade": lambda: sn.valor_devido_inicio_atividade(
                "I", ["30000", "50000", "70000.01"], ano=2026),
            # média com dízima: a CLI chama esta direto, fora das públicas
            "_rbt12_primeiros_meses": lambda: sn.calculo._rbt12_primeiros_meses(
                ["10000", "10000.01", "10000.01", "70000"], 2026),
            "avisos_inicio_atividade": lambda: sn.avisos_inicio_atividade(
                ["123456.789", "234567.891", "345678.912"], 11, ano=2026),
            "reais": lambda: sn.reais(Decimal("1234567.895")),
            "porcentagem": lambda: sn.porcentagem(Decimal("0.123456789")),
        }
        esperado = {nome: conta() for nome, conta in contas.items()}
        with localcontext() as alheio:
            alheio.prec = 6
            alheio.rounding = ROUND_DOWN
            alheio.traps[Inexact] = True
            for nome, conta in contas.items():
                with self.subTest(conta=nome):
                    self.assertEqual(conta(), esperado[nome])
            self.assertEqual(alheio.prec, 6)  # o contexto de quem chama volta igual


class TestLimiteProporcionalNoInicio(unittest.TestCase):
    """LC 123, art. 3º, §§ 2º, 10 a 13; Res. CGSN 140, arts. 3º e 9º, § 2º.

    Conta à mão: começo em novembro são 2 meses até dezembro; limite
    400.000 × 2 = 800.000, sublimite 300.000 × 2 = 600.000; 20% do limite =
    160.000 (retroage acima de 960.000), do sublimite = 120.000 (acima de
    720.000).
    """

    def aviso(self, *receitas, mes=11, ano=2026):
        from simples_nacional import avisos_inicio_atividade
        return " ".join(avisos_inicio_atividade(list(receitas), mes, ano=ano))

    def test_dentro_dos_dois(self):
        self.assertEqual(self.aviso("300000", "300000"), "")  # 600.000: no sublimite, não acima

    def test_sublimite_ate_20_por_cento_vale_no_ano_seguinte(self):
        for acumulada in ("600000.01", "720000.00"):
            with self.subTest(acumulada=acumulada):
                texto = self.aviso("0", acumulada)
                self.assertIn("acima do sublimite proporcional de R$ 600.000,00", texto)
                self.assertIn("R$ 300.000,00 × 2 meses", texto)
                self.assertIn("a partir de 1º de janeiro do ano seguinte", texto)
                self.assertIn("ICMS e ISS saem do DAS", texto)
                self.assertNotIn("do limite proporcional", texto)

    def test_sublimite_acima_de_20_por_cento_retroage(self):
        texto = self.aviso("0", "720000.01")
        self.assertIn("desde o início de atividade, porque o excesso passa de 20% do sublimite", texto)

    def test_limite_ate_20_por_cento_vale_no_ano_seguinte(self):
        for acumulada in ("800000.01", "960000.00"):
            with self.subTest(acumulada=acumulada):
                texto = self.aviso(acumulada, "0")
                self.assertIn("acima do limite proporcional de R$ 800.000,00", texto)
                self.assertIn("fora do Simples Nacional a partir de 1º de janeiro do ano seguinte", texto)
                self.assertNotIn("sublimite", texto)
        self.assertNotIn("do limite proporcional", self.aviso("800000.00", "0"))

    def test_limite_acima_de_20_por_cento_retroage(self):
        texto = self.aviso("960000.01", "0")
        self.assertIn("fora do Simples Nacional desde o início de atividade", texto)
        self.assertIn("passa de 20% do limite", texto)

    def test_um_mes_e_o_exemplo_da_revisao(self):
        # 2.000.000 no 1º mês, aberta em dezembro: 1 mês, limite 400.000
        texto = self.aviso("2000000", mes=12, ano=2027)
        self.assertIn("(2027) de R$ 2.000.000,00, acima do limite proporcional de R$ 400.000,00", texto)
        self.assertIn("R$ 400.000,00 × 1 mês,", texto)
        self.assertIn("desde o início de atividade", texto)
        # aberta em agosto: 5 meses, limite 2.000.000 (não passa), sublimite 1.500.000
        texto = self.aviso("2000000", mes=8, ano=2027)
        self.assertIn("acima do sublimite proporcional de R$ 1.500.000,00", texto)
        self.assertIn("ICMS, ISS e IBS saem do DAS", texto)
        self.assertEqual(self.aviso("2000000", mes=1, ano=2027), "")

    def test_so_as_receitas_do_ano_de_inicio(self):
        # aberta em dezembro de 2026, apuração em fevereiro de 2027: conta só dezembro
        self.assertEqual(self.aviso("100000", "900000", "900000", mes=12, ano=2027), "")
        texto = self.aviso("500000", "1", "1", mes=12, ano=2027)
        self.assertIn("(2026) de R$ 500.000,00, acima do limite proporcional de R$ 400.000,00", texto)

    def test_texto_do_ibs_sozinho(self):
        texto = self.aviso("0", "700000", ano=2033)
        self.assertIn("o IBS sai do DAS", texto)
        self.assertIn("e é recolhido pelas regras", texto)

    def test_entradas_invalidas(self):
        from simples_nacional import avisos_inicio_atividade
        for mes in (0, 13, True, "3", 3.0):
            with self.subTest(mes=mes):
                with self.assertRaisesRegex(ValueError, "mes_inicio"):
                    avisos_inicio_atividade(["1"], mes, ano=2026)
        with self.assertRaisesRegex(ValueError, "negativo"):
            avisos_inicio_atividade(["1", "-1"], 3, ano=2026)
        with self.assertRaises(TypeError):
            avisos_inicio_atividade("1000", 3, ano=2026)


class TestIcmsIssAcimaDoSublimite(unittest.TestCase):
    """Res. CGSN 140, art. 21, III, b (até 31/12/2026): RBT12 acima da 5ª faixa e
    sublimite não excedido no ano, ICMS ou ISS =
    {[(RBT12 × nominal da 5ª faixa) − PD da 5ª faixa] / RBT12} × repartição do
    ICMS/ISS da 5ª faixa, somado à 6ª faixa, que é só federal.

    Repartição da 5ª faixa (LC 123, Anexos I a V, "Percentual de Repartição"):
    I 33,50%, II 32,00%, III 33,50%, IV 40,00%, V 23,50%.
    """

    def efetiva(self, anexo, rbt12, ano=2026):
        from simples_nacional import aliquota_efetiva
        return aliquota_efetiva(anexo, rbt12, ano=ano, icms_iss_no_das=True)

    def test_conta_a_mao_nos_cinco_anexos(self):
        casos = {
            # 6ª: (4.500.000 × 19% − 378.000) / 4.500.000 = 0,106
            # 5ª: (4.500.000 × 14,3% − 87.300) / 4.500.000 = 0,1236; × 33,5% = 0,041406
            ("I", 4_500_000): Decimal("0.106") + Decimal("0.1236") * Decimal("0.335"),
            # 6ª: (4.000.000 × 30% − 720.000) / 4.000.000 = 0,12
            # 5ª: (4.000.000 × 14,7% − 85.500) / 4.000.000 = 0,125625; × 32% = 0,0402
            ("II", 4_000_000): Decimal("0.12") + Decimal("0.125625") * Decimal("0.32"),
            # 6ª: (4.000.000 × 33% − 648.000) / 4.000.000 = 0,168
            # 5ª: (4.000.000 × 21% − 125.640) / 4.000.000 = 0,17859; × 33,5% = 0,05982765
            # (ISS acima de 5%: o teto da alínea a passa a diferença aos federais,
            # o total fica o mesmo)
            ("III", 4_000_000): Decimal("0.168") + Decimal("0.17859") * Decimal("0.335"),
            # 6ª: (4.800.000 × 33% − 828.000) / 4.800.000 = 0,1575
            # 5ª: (4.800.000 × 22% − 183.780) / 4.800.000 = 0,1817125; × 40% = 0,072685
            ("IV", 4_800_000): Decimal("0.1575") + Decimal("0.1817125") * Decimal("0.40"),
            # 6ª: (4.000.000 × 30,5% − 540.000) / 4.000.000 = 0,17
            # 5ª: (4.000.000 × 23% − 62.100) / 4.000.000 = 0,214475; × 23,5% = 0,050401625
            ("V", 4_000_000): Decimal("0.17") + Decimal("0.214475") * Decimal("0.235"),
        }
        for (anexo, rbt12), esperado in casos.items():
            with self.subTest(anexo=anexo):
                self.assertEqual(self.efetiva(anexo, rbt12), esperado)
        self.assertEqual(casos[("I", 4_500_000)], Decimal("0.147406"))

    def test_valor_do_mes(self):
        # 375.000 × 14,7406% = 55.277,25; só federal, 375.000 × 10,6% = 39.750,00
        self.assertEqual(valor_devido("I", 4_500_000, "375000", ano=2026, icms_iss_no_das=True),
                         Decimal("55277.25"))
        self.assertEqual(valor_devido("I", 4_500_000, "375000", ano=2026), Decimal("39750.00"))
        self.assertEqual(valor_devido("I", 4_500_000, "375000", ano=2026, icms_iss_no_das=False),
                         Decimal("39750.00"))

    def test_ate_o_sublimite_nao_muda_nada(self):
        from simples_nacional import aliquota_efetiva
        for anexo in ("I", "II", "III", "IV", "V"):
            for rbt12 in ("1000000", "3600000.00"):
                with self.subTest(anexo=anexo, rbt12=rbt12):
                    self.assertEqual(self.efetiva(anexo, rbt12),
                                     aliquota_efetiva(anexo, rbt12, ano=2026))
        # um centavo acima do sublimite já soma o ICMS: 5ª faixa em 3.600.000
        # dá (3.600.000 × 14,3% − 87.300) / 3.600.000 = 427.500 / 3.600.000 =
        # 0,11875; × 33,5% = 0,03978125
        acima = Decimal("3600000.01")
        quinta = (acima * Decimal("0.143") - 87_300) / acima * Decimal("0.335")
        self.assertEqual(self.efetiva("I", acima),
                         aliquota_efetiva("I", acima, ano=2026) + quinta)
        self.assertEqual(round(quinta, 8), Decimal("0.03978125"))

    def test_anos_de_2018_a_2026(self):
        for ano in (2018, 2026):
            with self.subTest(ano=ano):
                self.assertEqual(self.efetiva("I", 4_500_000, ano=ano), Decimal("0.147406"))

    def test_a_partir_de_2027_nao_calcula(self):
        for ano in (2027, 2029, 2033):
            with self.subTest(ano=ano):
                with self.assertRaisesRegex(ValueError, "Res. CGSN 190/2026"):
                    self.efetiva("I", 4_500_000, ano=ano)
                with self.assertRaisesRegex(ValueError, "a partir de 2027"):
                    valor_devido("I", 4_500_000, "1000", ano=ano, icms_iss_no_das=True)
        # até o sublimite a opção não muda nada, também em 2027
        from simples_nacional import aliquota_efetiva
        self.assertEqual(self.efetiva("I", 3_000_000, ano=2027),
                         aliquota_efetiva("I", 3_000_000, ano=2027))

    def test_opcao_so_aceita_bool(self):
        from simples_nacional import aliquota_efetiva
        for valor in ("sim", 1, None):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(TypeError, "icms_iss_no_das"):
                    aliquota_efetiva("I", 4_500_000, ano=2026, icms_iss_no_das=valor)

    def test_reparticao_da_tabela(self):
        from simples_nacional import ICMS_ISS_QUINTA_FAIXA
        self.assertEqual(ICMS_ISS_QUINTA_FAIXA, {
            "I": Decimal("0.335"), "II": Decimal("0.32"), "III": Decimal("0.335"),
            "IV": Decimal("0.40"), "V": Decimal("0.235")})

    def test_aviso_com_a_opcao(self):
        texto = " ".join(avisos(4_500_000, ano=2026, icms_iss_no_das=True))
        self.assertIn("soma à parte federal ICMS ou ISS pela 5ª faixa", texto)
        self.assertIn("art. 12", texto)
        self.assertIn("art. 24", texto)
        self.assertNotIn("--icms-iss-no-das", texto)
        texto = " ".join(avisos(4_500_000, ano=2026))
        self.assertIn("icms_iss_no_das=True (na linha de comando, --icms-iss-no-das)", texto)
        self.assertIn("art. 12", texto)
        # a partir de 2027 a opção não troca o texto
        self.assertEqual(avisos(4_500_000, ano=2027, icms_iss_no_das=True),
                         avisos(4_500_000, ano=2027))


if __name__ == "__main__":
    unittest.main()
