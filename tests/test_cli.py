"""A linha de comando, rodada como o usuário roda (python -m simples_nacional)."""

import os
import subprocess
import sys
import unittest
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rodar(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "simples_nacional", *args],
        cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8",
    )


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


if __name__ == "__main__":
    unittest.main()
