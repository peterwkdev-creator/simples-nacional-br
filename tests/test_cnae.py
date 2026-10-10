"""CNAE -> anexo: listas oficiais da Res. CGSN 140 e a tabela própria pela LC 123.

Fontes (lidas em 09/10/2026, conferidas de novo em 10/10/2026; URLs em
simples_nacional/cnae_dados.py):
- Res. CGSN 140/2018, art. 8º: Anexo VI (101 subclasses impeditivas) e
  Anexo VII (22 que abrangem atividade impeditiva e permitida).
- LC 123, art. 18, §§ 4º, 5º-B a 5º-M, texto atualizado na Câmara; § 4º, II
  e § 5º na redação da LC 214/2025, art. 517, de 2027 em diante.
- Nomes das subclasses: API de CNAE do IBGE (1.332 subclasses).

Não há tabela oficial CNAE -> Anexo I a V: cada caso abaixo foi conferido à
mão pelo nome da subclasse contra o inciso citado.
"""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

from simples_nacional import cnae_dados
from simples_nacional.cnae import (AMBIGUA, ANEXO, AVISO_INTERPRETACAO, FATOR_R, IMPEDITIVA,
                                   SEM_CLASSIFICACAO, enquadrar, normalizar, subclasses)

BIBLIOTECA = Path(__file__).resolve().parents[1]
ANO = 2026


class TestFontes(unittest.TestCase):

    def test_lista_do_ibge_tem_1332_subclasses(self):
        nomes = subclasses()
        self.assertEqual(len(nomes), 1332)
        self.assertEqual(nomes["6920-6/01"], "ATIVIDADES DE CONTABILIDADE")

    def test_anexo_vi_tem_101_e_o_vii_22(self):
        self.assertEqual(len(cnae_dados.IMPEDITIVOS), 101)
        self.assertEqual(len(cnae_dados.AMBIGUOS), 22)

    def test_linhas_do_pdf_do_anexo_vi(self):
        # primeira, uma do meio e a última do PDF vigente (anexo 50966)
        for codigo in ("1220-4/01", "8299-7/04", "9900-8/00"):
            with self.subTest(codigo=codigo):
                self.assertIn(codigo, cnae_dados.IMPEDITIVOS)

    def test_anexo_vii_inteiro(self):
        # transcrito do PDF vigente (anexo 58338), um por um
        esperado = {"1113-5/02", "4635-4/02", "4635-4/03", "4635-4/99", "4684-2/99",
                    "4924-8/00", "4929-9/02", "4929-9/04", "4929-9/99", "4950-7/00",
                    "5011-4/02", "5091-2/02", "5099-8/01", "5099-8/99", "5111-1/00",
                    "5112-9/01", "5112-9/99", "5229-0/01", "5229-0/99", "6619-3/02",
                    "6619-3/99", "8299-7/99"}
        self.assertEqual(set(cnae_dados.AMBIGUOS), esperado)

    def test_todo_codigo_das_listas_existe_na_cnae(self):
        nomes = subclasses()
        for grupo, codigos in _grupos():
            for codigo in codigos:
                with self.subTest(grupo=grupo, codigo=codigo):
                    self.assertIn(codigo, nomes)

    def test_nenhum_codigo_em_dois_grupos(self):
        visto = {}
        for grupo, codigos in _grupos():
            for codigo in codigos:
                with self.subTest(codigo=codigo):
                    self.assertNotIn(codigo, visto, f"{codigo} em {visto.get(codigo)} e {grupo}")
                visto[codigo] = grupo


def _grupos():
    yield "Anexo VI", cnae_dados.IMPEDITIVOS
    yield "Anexo VII", cnae_dados.AMBIGUOS
    yield "revenda", cnae_dados.REVENDA
    yield "indústria", cnae_dados.INDUSTRIA
    for anexo, fundamento, _obs, codigos in cnae_dados.SERVICOS:
        yield f"{anexo} {fundamento}", codigos


class TestRegraDoNome(unittest.TestCase):
    """Revenda e indústria saem do nome oficial: o conferidor refaz a regra."""

    def test_revenda_e_comercio_da_secao_g(self):
        nomes = subclasses()
        lojas = {"4713-0/02", "4713-0/04", "4713-0/05", "4721-1/02", "4722-9/02", "4729-6/01"}
        for codigo in cnae_dados.REVENDA:
            with self.subTest(codigo=codigo):
                self.assertIn(codigo[:2], ("45", "46", "47"))
                nome = nomes[codigo]
                self.assertTrue(codigo in lojas or nome.startswith("COMÉRCIO"), nome)
                self.assertNotIn("CONSIGNAÇÃO", nome)

    def test_toda_subclasse_de_comercio_da_secao_g_esta_classificada(self):
        # fora: manipulação (§ 4º, VII, depende da encomenda) e consignação
        nomes = subclasses()
        fora = {"4771-7/02", "4512-9/02", "4542-1/02"}
        for codigo, nome in nomes.items():
            if codigo[:2] in ("45", "46", "47") and nome.startswith("COMÉRCIO") \
                    and codigo not in fora:
                with self.subTest(codigo=codigo):
                    self.assertNotEqual(enquadrar(codigo, ano=ANO).situacao, SEM_CLASSIFICACAO)

    def test_industria_e_fabricacao_da_secao_c(self):
        nomes = subclasses()
        for codigo in cnae_dados.INDUSTRIA:
            with self.subTest(codigo=codigo):
                self.assertTrue(10 <= int(codigo[:2]) <= 33)
                self.assertTrue(nomes[codigo].startswith(cnae_dados.PREFIXOS_INDUSTRIA),
                                nomes[codigo])


class TestEnquadrar(unittest.TestCase):

    def assertEnquadra(self, codigo, situacao, anexo, trecho, ano=ANO):
        e = enquadrar(codigo, ano=ano)
        self.assertEqual((e.situacao, e.anexo), (situacao, anexo), codigo)
        self.assertIn(trecho, e.fundamento, codigo)
        return e

    def test_um_caso_por_grupo(self):
        casos = [
            # (código, nome do IBGE conferido à mão, situação, anexo, trecho da lei)
            ("4781-4/00", "varejo de vestuário", ANEXO, "I", "§ 4º, I"),
            ("4729-6/01", "tabacaria (loja, sem COMÉRCIO no nome)", ANEXO, "I", "§ 4º, I"),
            ("1091-1/02", "fabricação de produtos de padaria", ANEXO, "II", "§ 4º, II"),
            ("1412-6/01", "confecção de vestuário, não sob medida", ANEXO, "II", "§ 4º, II"),
            ("8513-9/00", "ensino fundamental", ANEXO, "III", "§ 5º-B, I"),
            ("5310-5/02", "franqueada do correio", ANEXO, "III", "§ 5º-B, II"),
            ("7911-2/00", "agência de viagens", ANEXO, "III", "§ 5º-B, III"),
            ("8599-6/01", "formação de condutores", ANEXO, "III", "§ 5º-B, IV"),
            ("8299-7/06", "casa lotérica", ANEXO, "III", "§ 5º-B, V"),
            ("4520-0/01", "manutenção mecânica de veículos", ANEXO, "III", "§ 5º-B, IX"),
            ("2539-0/01", "usinagem, tornearia e solda", ANEXO, "III", "§ 5º-B, IX"),
            ("4921-3/01", "ônibus municipal", ANEXO, "III", "§ 5º-B, XIII"),
            ("6920-6/01", "contabilidade", ANEXO, "III", "§ 5º-B, XIV"),
            ("9001-9/01", "produção teatral", ANEXO, "III", "§ 5º-B, XV"),
            ("6622-3/00", "corretores de seguros", ANEXO, "III", "§ 5º-B, XVII"),
            ("6821-8/02", "corretagem no aluguel de imóveis", ANEXO, "III", "§ 4º, III"),
            ("7711-0/00", "locação de automóveis sem condutor", ANEXO, "III", "§ 4º, V"),
            ("4930-2/02", "carga intermunicipal", ANEXO, "III", "§ 5º-E"),
            ("4120-4/00", "construção de edifícios", ANEXO, "IV", "§ 5º-C, I"),
            ("8121-4/00", "limpeza em prédios", ANEXO, "IV", "§ 5º-C, VI"),
            ("6911-7/01", "serviços advocatícios", ANEXO, "IV", "§ 5º-C, VII"),
            ("8650-0/04", "fisioterapia", FATOR_R, None, "§ 5º-B, XVI"),
            ("7111-1/00", "arquitetura", FATOR_R, None, "§ 5º-B, XVIII"),
            ("8630-5/03", "médica restrita a consultas", FATOR_R, None, "§ 5º-B, XIX"),
            ("8630-5/04", "odontológica", FATOR_R, None, "§ 5º-B, XX"),
            ("8650-0/03", "psicologia e psicanálise", FATOR_R, None, "§ 5º-B, XXI"),
            ("6822-6/00", "administração de imóveis", FATOR_R, None, "§ 5º-D, I"),
            ("9313-1/00", "condicionamento físico", FATOR_R, None, "§ 5º-D, III"),
            ("6201-5/01", "programas sob encomenda", FATOR_R, None, "§ 5º-D, IV"),
            ("6203-1/00", "programas não customizáveis", FATOR_R, None, "§ 5º-D, V"),
            ("6201-5/02", "web design", FATOR_R, None, "§ 5º-D, VI"),
            ("8640-2/02", "laboratórios clínicos", FATOR_R, None, "§ 5º-D, XII"),
            ("8640-2/06", "ressonância magnética", FATOR_R, None, "§ 5º-D, XIII"),
            ("7500-1/00", "veterinária", FATOR_R, None, "§ 5º-I, II"),
            ("7490-1/01", "tradução", FATOR_R, None, "§ 5º-I, V"),
            ("7112-0/00", "engenharia", FATOR_R, None, "§ 5º-I, VI"),
            ("4618-4/01", "representante de medicamentos", FATOR_R, None, "§ 5º-I, VII"),
            ("6621-5/01", "peritos de seguros", FATOR_R, None, "§ 5º-I, VIII"),
            ("7020-4/00", "consultoria em gestão", FATOR_R, None, "§ 5º-I, IX"),
            ("7311-4/00", "agência de publicidade", FATOR_R, None, "§ 5º-I, X"),
            ("7312-2/00", "agenciamento de espaço publicitário", FATOR_R, None, "§ 5º-I, XI"),
        ]
        nomes = subclasses()
        for codigo, _conferido, situacao, anexo, trecho in casos:
            with self.subTest(codigo=codigo, nome=nomes[codigo]):
                self.assertEnquadra(codigo, situacao, anexo, trecho)
        # todo grupo de serviço tem caso aqui: trocar o anexo de um grupo derruba
        fundamentos = {f for _a, f, _o, _c in cnae_dados.SERVICOS}
        cobertos = {f for f in fundamentos
                    if any(enquadrar(c, ano=ANO).fundamento.endswith(f) for c, *_ in casos)}
        self.assertEqual(fundamentos - cobertos, set())

    def test_impeditiva(self):
        e = self.assertEnquadra("8299-7/04", IMPEDITIVA, None, "Anexo VI")
        self.assertEqual(e.denominacao, "LEILOEIROS INDEPENDENTES")

    def test_ambigua(self):
        e = self.assertEnquadra("1113-5/02", AMBIGUA, None, "Anexo VII")
        self.assertIn("impeditiva", e.observacao)

    def test_sem_classificacao(self):
        # restaurante: a LC 123 não o descreve; fica com o contador
        e = self.assertEnquadra("5611-2/01", SEM_CLASSIFICACAO, None, "")
        self.assertIn("contador", e.observacao)

    def test_anexo_iv_avisa_a_cpp(self):
        self.assertIn("CPP", enquadrar("6911-7/01", ano=ANO).observacao)

    def test_comunicacao_e_carga_trocam_iss_por_icms(self):
        self.assertIn("ICMS", enquadrar("6120-5/01", ano=ANO).observacao)

    def test_locacao_de_bem_movel_sem_iss(self):
        self.assertIn("ISS", enquadrar("7732-2/02", ano=ANO).observacao)


class TestIndustriaDe2027(unittest.TestCase):
    """LC 123, art. 18, § 5º, redação da LC 214, art. 517 (vigência 01/01/2027):
    "as atividades industriais serão tributadas na forma do Anexo I", ressalvado
    o produto com IPI mantido (ZFM), que segue no Anexo II (§ 4º, II)."""

    def test_2026_e_o_ultimo_ano_no_anexo_ii(self):
        e = enquadrar("1091-1/02", ano=2026)
        self.assertEqual((e.anexo, e.fundamento), ("II", "LC 123, art. 18, § 4º, II"))
        self.assertNotIn("Zona Franca", e.observacao)

    def test_de_2027_em_diante_anexo_i_com_aviso_da_zfm(self):
        for ano in (2027, 2028, 2029, 2033, 2040):
            with self.subTest(ano=ano):
                e = enquadrar("1091-1/02", ano=ano)
                self.assertEqual((e.situacao, e.anexo), (ANEXO, "I"))
                self.assertEqual(e.fundamento, "LC 123, art. 18, § 5º")
                self.assertIn("Industrialização.", e.observacao)
                self.assertIn("IPI mantido", e.observacao)
                self.assertIn("Zona Franca de Manaus", e.observacao)

    def test_toda_a_industria_muda_e_so_ela(self):
        mudou = {c for c in subclasses()
                 if enquadrar(c, ano=2026).anexo != enquadrar(c, ano=2027).anexo}
        self.assertEqual(mudou, set(cnae_dados.INDUSTRIA))
        self.assertEqual(len(mudou), 320)

    def test_ano_como_no_resto_da_biblioteca(self):
        with self.assertRaises(TypeError):
            enquadrar("1091-1/02", ano="2027")
        with self.assertRaisesRegex(ValueError, "2018"):
            enquadrar("1091-1/02", ano=2017)
        with self.assertRaises(TypeError):
            enquadrar("1091-1/02")  # ano é obrigatório


class TestFatorR(unittest.TestCase):

    def test_sem_folha_diz_os_dois_anexos(self):
        e = enquadrar("7112-0/00", ano=ANO)
        self.assertIsNone(e.anexo)
        self.assertIn("28%", e.observacao)

    def test_28_por_cento_e_anexo_iii(self):
        # 280.000 / 1.000.000 = 0,28: o § 5º-J diz "igual ou superior"
        self.assertEqual(enquadrar("7112-0/00", ano=ANO, folha12=280000, rbt12=1000000).anexo,
                         "III")

    def test_abaixo_de_28_e_anexo_v(self):
        # 279.999,99 / 1.000.000 = 0,27999999
        self.assertEqual(enquadrar("7112-0/00", ano=ANO, folha12="279999.99",
                                   rbt12=1000000).anexo, "V")

    def test_paragrafo_5m_tambem(self):
        self.assertEqual(enquadrar("8630-5/03", ano=ANO, folha12=100, rbt12=1000).anexo, "V")
        self.assertEqual(enquadrar("8630-5/03", ano=ANO, folha12=300, rbt12=1000).anexo, "III")

    def test_paragrafo_que_leva_ao_outro_anexo(self):
        # § 5º-I (Anexo V) sobe ao III pelo § 5º-J; §§ 5º-B e 5º-D descem ao V pelo § 5º-M
        self.assertIn("§ 5º-J", enquadrar("7112-0/00", ano=ANO).observacao)
        self.assertIn("§ 5º-M", enquadrar("8630-5/03", ano=ANO).observacao)
        self.assertIn("§ 5º-M", enquadrar("6201-5/01", ano=ANO).observacao)

    def test_folha_sem_rbt12_e_erro(self):
        with self.assertRaisesRegex(ValueError, "folha12 e rbt12"):
            enquadrar("7112-0/00", ano=ANO, folha12=1000)

    def test_folha_em_anexo_fixo_nao_muda_nada(self):
        self.assertEqual(enquadrar("6920-6/01", ano=ANO, folha12=1, rbt12=1000).anexo, "III")


class TestCodigo(unittest.TestCase):

    def test_formatos_aceitos(self):
        for texto in ("6920601", "6920-6/01", " 6920-6/01 ", "6920.6-01"):
            with self.subTest(texto=texto):
                self.assertEqual(normalizar(texto), "6920-6/01")

    def test_formato_errado(self):
        for texto in ("692060", "69206011", "abc", ""):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "7 dígitos"):
                    normalizar(texto)

    def test_codigo_que_nao_existe(self):
        with self.assertRaisesRegex(ValueError, "não existe na CNAE"):
            enquadrar("9999-9/99", ano=ANO)


class TestEmpacotamento(unittest.TestCase):

    def test_todo_arquivo_que_nao_e_py_esta_no_package_data(self):
        # sem isso, o pip install deixa o .tsv de fora e subclasses() quebra
        pacote = BIBLIOTECA / "simples_nacional"
        dados = {p.name for p in pacote.iterdir()
                 if p.is_file() and p.suffix not in (".py", ".pyc")}
        pyproject = (BIBLIOTECA / "pyproject.toml").read_text(encoding="utf-8")
        bloco = re.search(r"\[tool\.setuptools\.package-data\]\n(.*?)(?:\n\[|\Z)", pyproject, re.S)
        declarados = set(re.findall(r'"([^"]+)"', bloco.group(1))) if bloco else set()
        self.assertEqual(dados, {"cnae_subclasses.tsv"})
        self.assertEqual(dados - declarados, set())


def rodar(*args, env=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8") if env is None else env
    return subprocess.run([sys.executable, "-m", "simples_nacional.cnae", *args],
                          cwd=BIBLIOTECA, capture_output=True, env=env)


def saida(r):
    return r.stdout.decode("utf-8"), r.stderr.decode("utf-8")


class TestCLI(unittest.TestCase):

    def test_anexo_fixo(self):
        r = rodar("6920-6/01", "--ano", "2026")
        out, err = saida(r)
        self.assertEqual(r.returncode, 0, err)
        self.assertIn("ATIVIDADES DE CONTABILIDADE", out)
        self.assertIn("Anexo III", out)
        self.assertIn("§ 5º-B, XIV", out)
        self.assertIn(AVISO_INTERPRETACAO, out)

    def test_industria_pelo_ano(self):
        out26, _ = saida(rodar("1091-1/02", "--ano", "2026"))
        out27, _ = saida(rodar("1091-1/02", "--ano", "2027"))
        self.assertIn("Anexo II (LC 123, art. 18, § 4º, II)", out26)
        self.assertIn("Anexo I (LC 123, art. 18, § 5º)", out27)
        self.assertIn("Zona Franca", out27)

    def test_fator_r_com_folha(self):
        # 300.000 / 1.000.000 = 30%
        r = rodar("7112000", "--ano", "2026", "--folha12", "300000", "--rbt12", "1000000")
        out, err = saida(r)
        self.assertEqual(r.returncode, 0, err)
        self.assertIn("Fator R: 30,0000%", out)
        self.assertIn("Anexo III", out)

    def test_varios_codigos(self):
        r = rodar("8299-7/04", "1113-5/02", "5611-2/01", "--ano", "2026")
        out, err = saida(r)
        self.assertEqual(r.returncode, 0, err)
        self.assertIn("impede o Simples", out)
        self.assertIn("Anexo VII", out)
        self.assertIn("sem classificação", out)

    def test_codigo_invalido_e_erro_de_uso(self):
        r = rodar("123")
        _, err = saida(r)
        self.assertEqual(r.returncode, 2)
        self.assertIn("7 dígitos", err)
        self.assertNotIn("Traceback", err)

    def test_ano_antes_de_2018_e_erro_de_uso(self):
        r = rodar("6920-6/01", "--ano", "2017")
        _, err = saida(r)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", err)

    def test_saida_redirecionada_sem_utf8(self):
        # norma da saída fora do ASCII: sem PYTHONIOENCODING, redirecionada
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        r = rodar("6911-7/01", "1091-1/02", "--ano", "2027", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(b"Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
