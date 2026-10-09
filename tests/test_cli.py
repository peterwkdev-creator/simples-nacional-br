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

if __name__ == "__main__":
    unittest.main()
