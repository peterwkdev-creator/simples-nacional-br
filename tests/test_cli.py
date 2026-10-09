"""A linha de comando, rodada como o usuário roda (python -m simples_nacional)."""

import io
import os
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from simples_nacional import __version__, ler_numero
from simples_nacional.__main__ import main

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rodar(*args, codificacao="utf-8"):
    env = dict(os.environ, PYTHONIOENCODING=codificacao)
    return subprocess.run(
        [sys.executable, "-m", "simples_nacional", *args],
        cwd=RAIZ, env=env, capture_output=True, text=True, encoding=codificacao,
    )


def saida(*args):
    """main() no mesmo processo: rápido para muitos casos."""
    with redirect_stdout(io.StringIO()) as texto:
        codigo = main(list(args))
    return codigo, texto.getvalue()


class TestCli(unittest.TestCase):

    def test_caso_146(self):
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "4500000", "--receita-mes", "375000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("10,6000%", r.stdout)
        self.assertIn("R$ 39.750,00", r.stdout)
        self.assertIn("art. 18", r.stdout)
        self.assertIn("ano-calendário 2026", r.stdout)
        self.assertIn("LC 155", r.stdout)
        self.assertIn("estimativa", r.stdout.lower())
        # acima do sublimite de R$ 3,6 milhões: o aviso sai impresso
        self.assertIn("3.600.000,00", r.stdout)
        self.assertIn("art. 21, III, b", r.stdout)

    def test_aviso_do_sublimite_segue_o_ano(self):
        r = rodar("--ano", "2027", "--anexo", "I", "--rbt12", "4500000", "--receita-mes", "375000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ICMS, ISS e IBS", r.stdout)
        self.assertNotIn("art. 21, III, b", r.stdout)

    def test_fator_r_escolhe_o_anexo(self):
        r = rodar("--ano", "2026", "--anexo", "fator-r", "--folha12", "280000",
                  "--rbt12", "1000000", "--receita-mes", "100000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Anexo III", r.stdout)
        self.assertIn("28,0000%", r.stdout)

    def test_fator_r_sem_folha(self):
        r = rodar("--ano", "2026", "--anexo", "fator-r", "--rbt12", "1000000", "--receita-mes", "1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--folha12", r.stderr)

    def test_acima_do_limite_sai_com_erro_sem_numero(self):
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "5000000", "--receita-mes", "400000")
        self.assertEqual(r.returncode, 2)
        self.assertIn("4.800.000,00", r.stderr)
        self.assertNotIn("R$", r.stdout)

    def test_valor_invalido(self):
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "abc", "--receita-mes", "1")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_aceita_virgula_decimal(self):
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "150000", "--receita-mes", "1000,50")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("R$ 40,02", r.stdout)  # 1.000,50 x 4% = 40,02


    def test_ano_2027_sexta_faixa(self):
        # (4.500.000 x 18,90% - 378.000) / 4.500.000 = 10,50%; 375.000 x 10,5% = 39.375,00
        r = rodar("--ano", "2027", "--anexo", "I", "--rbt12", "4500000", "--receita-mes", "375000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("18,9000%", r.stdout)
        self.assertIn("10,5000%", r.stdout)
        self.assertIn("R$ 39.375,00", r.stdout)
        self.assertIn("ano-calendário 2027", r.stdout)
        self.assertIn("LC 214", r.stdout)

    def test_sem_ano_usa_o_corrente_e_diz_qual(self):
        r = rodar("--anexo", "I", "--rbt12", "150000", "--receita-mes", "1000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"ano-calendário {date.today().year}", r.stdout)
        self.assertIn("--ano", r.stdout)

    def test_ano_fora_da_cobertura(self):
        r = rodar("--ano", "2017", "--anexo", "I", "--rbt12", "150000", "--receita-mes", "1000")
        self.assertEqual(r.returncode, 2)
        self.assertIn("2018", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_ponto_de_milhar_sem_virgula(self):
        # 360.000 é trezentos e sessenta mil, não 360: 2ª faixa, 5,65%; 10.000 x 5,65% = 565,00
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "360.000", "--receita-mes", "10.000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("5,6500%", r.stdout)
        self.assertIn("R$ 565,00", r.stdout)

    def test_ponto_decimal_com_centavos(self):
        # 1000.50 x 4% = 40,02 (o formato do exemplo 4500000.00 continua valendo)
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "150000.00", "--receita-mes", "1000.50")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("R$ 40,02", r.stdout)

    def test_formato_ambiguo_recusado(self):
        for valor in ("1,000.50", "1.0000", "1.000.0"):
            with self.subTest(valor=valor):
                r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "150000", "--receita-mes", valor)
                self.assertEqual(r.returncode, 2)
                self.assertIn("inválido", r.stderr)
                self.assertNotIn("Traceback", r.stderr)

    def test_inicio_de_atividade_2026(self):
        # 2º mês: 30.000 x 12 = 360.000 -> 5,65%; 50.000 x 5,65% = 2.825,00
        r = rodar("--ano", "2026", "--anexo", "I", "--receitas", "30.000;50.000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2º mês de atividade", r.stdout)
        self.assertIn("R$ 360.000,00", r.stdout)
        self.assertIn("art. 22", r.stdout)
        self.assertIn("R$ 2.825,00", r.stdout)

    def test_inicio_de_atividade_2027_primeira_faixa(self):
        # 1º mês em 2027: 1ª faixa do Anexo I, 4%; 400.000 x 4% = 16.000,00
        r = rodar("--ano", "2027", "--anexo", "I", "--receitas", "400000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1ª faixa", r.stdout)
        self.assertIn("Res. CGSN 190", r.stdout)
        self.assertIn("R$ 16.000,00", r.stdout)

    def test_receitas_exclui_rbt12_e_receita_mes(self):
        for args in (["--rbt12", "150000"], ["--receita-mes", "1000"]):
            with self.subTest(args=args):
                r = rodar("--ano", "2026", "--anexo", "I", "--receitas", "30000", *args)
                self.assertEqual(r.returncode, 2)
                self.assertNotIn("Traceback", r.stderr)

    def test_sem_rbt12_nem_receitas(self):
        r = rodar("--ano", "2026", "--anexo", "I", "--receita-mes", "1000")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--receitas", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

class TestCliEntradas(unittest.TestCase):

    def test_folha12_sem_fator_r_e_erro(self):
        r = rodar("--ano", "2026", "--anexo", "I", "--rbt12", "100000", "--receita-mes", "1",
                  "--folha12", "28000")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--folha12 só vale com --anexo fator-r", r.stderr)

    def test_fator_r_com_receitas_e_erro(self):
        r = rodar("--ano", "2026", "--anexo", "fator-r", "--receitas", "30.000;50.000",
                  "--folha12", "28000")
        self.assertEqual(r.returncode, 2)
        self.assertIn("informe o anexo (III ou V)", r.stderr)

    def test_receitas_acima_do_limite(self):
        # 2º mês de 2026: RBT12 = 500.000 x 12 = 6 milhões
        r = rodar("--ano", "2026", "--anexo", "I", "--receitas", "500.000;500.000")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")
        self.assertIn("erro:", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_ajuda_cita_a_lc_214(self):
        self.assertIn("LC 214/2025", rodar("--help").stdout)


class TestCli034(unittest.TestCase):

    def test_conta_do_valor_fecha_no_centavo(self):
        # R$ 1.000.000,00 x 15,9054% daria 159.054,00; a efetiva vai com as
        # casas que fecham: 15,905405%
        linha = re.compile(r"Valor do mês: R\$ ([\d.,]+) = R\$ ([\d.,]+) × ([\d,]+)%")
        for anexo in ("I", "II", "III", "IV", "V"):
            for rbt12 in ("180000", "1234567,89", "3700000", "4800000"):
                for receita in ("1.000.000,00", "123.456,78", "0,01"):
                    with self.subTest(anexo=anexo, rbt12=rbt12, receita=receita):
                        codigo, texto = saida("--ano", "2026", "--anexo", anexo,
                                              "--rbt12", rbt12, "--receita-mes", receita)
                        self.assertEqual(codigo, 0)
                        valor, base, efetiva = linha.search(texto).groups()
                        conta = ler_numero(base) * ler_numero(efetiva) / 100
                        self.assertEqual(conta.quantize(Decimal("0.01"), ROUND_HALF_UP),
                                         ler_numero(valor))
        _, texto = saida("--ano", "2026", "--anexo", "V", "--rbt12", "3700000",
                         "--receita-mes", "1000000")
        self.assertIn("R$ 159.054,05 = R$ 1.000.000,00 × 15,905405%", texto)
        _, texto = saida("--ano", "2026", "--anexo", "I", "--rbt12", "4500000",
                         "--receita-mes", "375000")
        self.assertIn("R$ 39.750,00 = R$ 375.000,00 × 10,6000%", texto)  # 4 casas bastam

    def test_fator_r_nao_arredonda_para_cima(self):
        # 27.999,99 / 100.000 = 27,99999%: abaixo de 28%, Anexo V
        _, texto = saida("--ano", "2026", "--anexo", "fator-r", "--rbt12", "100000",
                         "--folha12", "27999,99", "--receita-mes", "10000")
        self.assertIn("Fator R: 27,9999% -> Anexo V", texto)
        _, texto = saida("--ano", "2026", "--anexo", "fator-r", "--rbt12", "100000",
                         "--folha12", "28000", "--receita-mes", "10000")
        self.assertIn("Fator R: 28,0000% -> Anexo III", texto)

    def test_version(self):
        r = rodar("--version")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), f"simples-nacional {__version__}")

    def test_reais_na_linha_de_comando(self):
        _, com_rs = saida("--ano", "2026", "--anexo", "I", "--rbt12", "R$ 4.500.000,00",
                          "--receita-mes", "R$ 375.000,00")
        _, sem_rs = saida("--ano", "2026", "--anexo", "I", "--rbt12", "4500000",
                          "--receita-mes", "375000")
        self.assertEqual(com_rs, sem_rs)

    def test_saida_redirecionada_em_cp1252(self):
        # o Windows redirecionado escreve em cp1252: um caractere fora dele
        # viraria UnicodeEncodeError (PYTHONIOENCODING sem errors é estrito)
        casos = (
            ("--ano", "2026", "--anexo", "I", "--rbt12", "4500000", "--receita-mes", "375000"),
            ("--ano", "2027", "--anexo", "III", "--rbt12", "4000000", "--receita-mes", "1"),
            ("--ano", "2026", "--anexo", "fator-r", "--rbt12", "100000", "--folha12",
             "27999,99", "--receita-mes", "10000"),
            ("--ano", "2026", "--anexo", "I", "--receitas", "30.000;50.000"),
            ("--ano", "2027", "--anexo", "I", "--receitas", "30.000;50.000;60.000"),
            ("--ano", "2028", "--anexo", "V", "--rbt12", "4800000", "--receita-mes", "1"),
            ("--ano", "2027", "--anexo", "I", "--receitas", "2.000.000", "--mes-inicio", "8"),
            ("--ano", "2027", "--anexo", "I", "--receitas", "2.000.000"),
        )
        for args in casos:
            with self.subTest(args=args):
                r = rodar(*args, codificacao="cp1252")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn("×", r.stdout)


class TestCliLimiteNoInicio(unittest.TestCase):

    def test_sem_mes_de_inicio_pede_o_mes(self):
        _, texto = saida("--ano", "2027", "--anexo", "I", "--receitas", "2.000.000")
        self.assertIn("Aviso: R$ 2.000.000,00 em 1 mês passa de R$ 300.000,00 por mês", texto)
        self.assertIn("informe --mes-inicio", texto)
        _, texto = saida("--ano", "2026", "--anexo", "I", "--receitas", "300.000;300.000")
        self.assertNotIn("Aviso", texto)  # 600.000 em 2 meses: não passa de 300.000 por mês
        _, texto = saida("--ano", "2026", "--anexo", "I", "--receitas", "350.000;350.000")
        self.assertIn("informe --mes-inicio", texto)  # 700.000: acima do sublimite, abaixo do limite

    def test_com_mes_de_inicio_confere(self):
        _, texto = saida("--ano", "2027", "--anexo", "I", "--receitas", "2.000.000",
                         "--mes-inicio", "12")
        self.assertIn("Aviso: Receita acumulada no ano de início de atividade (2027)", texto)
        self.assertIn("fora do Simples Nacional desde o início de atividade", texto)
        self.assertNotIn("informe --mes-inicio", texto)
        _, texto = saida("--ano", "2026", "--anexo", "I", "--receitas", "30.000;50.000",
                         "--mes-inicio", "3")
        self.assertNotIn("Aviso", texto)

    def test_erros_de_uso(self):
        for args, erro in ((("--rbt12", "1", "--receita-mes", "1", "--mes-inicio", "3"),
                            "--mes-inicio só vale com --receitas"),
                           (("--receitas", "1", "--mes-inicio", "13"), "mês inválido: '13'"),
                           (("--receitas", "1", "--mes-inicio", "x"), "mês inválido: 'x'")):
            with self.subTest(args=args):
                r = rodar("--ano", "2026", "--anexo", "I", *args)
                self.assertEqual(r.returncode, 2)
                self.assertIn(erro, r.stderr)


if __name__ == "__main__":
    unittest.main()
