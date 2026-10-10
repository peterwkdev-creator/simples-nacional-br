"""Servidor MCP: as duas formas do protocolo, as quatro ferramentas e o stdio.

Formatos conferidos na especificação (https://modelcontextprotocol.io/specification,
revisões 2025-06-18, 2025-11-25 e 2026-07-28, consultada em 10/10/2026).
"""

import json
import os
import re
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

from simples_nacional import aliquota_efetiva, parcelas_das, valor_devido
from simples_nacional.mcp import (AVISO, FERRAMENTAS, VERSAO_SEM_ESTADO, Servidor,
                                  tratar_linha)

BIBLIOTECA = Path(__file__).resolve().parents[1]

META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {}}


def pedido(metodo, params=None, ident=1, meta=META):
    params = dict(params or {})
    if meta is not None:
        params["_meta"] = meta
    return {"jsonrpc": "2.0", "id": ident, "method": metodo, "params": params}


def chamar(nome, **argumentos):
    """tools/call na forma sem estado; devolve o result."""
    r = Servidor().responder(pedido("tools/call", {"name": nome, "arguments": argumentos}))
    return r["result"]


def erro(resposta):
    return resposta["error"]["code"]


class TestSemEstado(unittest.TestCase):
    """Revisão 2026-07-28: a versão vem no _meta de cada requisição."""

    def test_discover(self):
        r = Servidor().responder(pedido("server/discover"))["result"]
        self.assertEqual(r["resultType"], "complete")
        self.assertEqual(r["supportedVersions"][0], VERSAO_SEM_ESTADO)
        self.assertEqual(r["capabilities"], {"tools": {}})
        self.assertEqual(r["cacheScope"], "public")
        self.assertIsInstance(r["ttlMs"], int)
        servidor = r["_meta"]["io.modelcontextprotocol/serverInfo"]
        self.assertEqual(servidor["name"], "simples-nacional")
        self.assertIn("PGDAS-D", r["instructions"])

    def test_tools_list_sem_initialize(self):
        r = Servidor().responder(pedido("tools/list"))["result"]
        self.assertEqual(r["resultType"], "complete")
        self.assertEqual([f["name"] for f in r["tools"]],
                         ["calcular_das", "repartir_das", "planejar_fator_r", "enquadrar_cnae"])
        self.assertIn("ttlMs", r)
        self.assertIn("cacheScope", r)

    def test_versao_nao_suportada(self):
        meta = dict(META, **{"io.modelcontextprotocol/protocolVersion": "1900-01-01"})
        r = Servidor().responder(pedido("tools/list", meta=meta))
        self.assertEqual(erro(r), -32022)
        self.assertEqual(r["error"]["data"]["requested"], "1900-01-01")
        self.assertIn(VERSAO_SEM_ESTADO, r["error"]["data"]["supported"])

    def test_sem_capacidades_do_cliente(self):
        meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}
        self.assertEqual(erro(Servidor().responder(pedido("tools/list", meta=meta))), -32602)

    def test_sem_meta_e_sem_initialize(self):
        self.assertEqual(erro(Servidor().responder(pedido("tools/list", meta=None))), -32602)


class TestComInitialize(unittest.TestCase):
    """Até a revisão 2025-11-25: initialize, depois as requisições sem _meta."""

    def iniciar(self, versao):
        s = Servidor()
        r = s.responder(pedido("initialize", {"protocolVersion": versao, "capabilities": {},
                                              "clientInfo": {"name": "teste", "version": "0"}},
                               meta=None))["result"]
        return s, r

    def test_responde_a_versao_pedida_se_suporta(self):
        for versao in ("2025-06-18", "2025-11-25"):
            with self.subTest(versao=versao):
                _, r = self.iniciar(versao)
                self.assertEqual(r["protocolVersion"], versao)
                self.assertEqual(r["capabilities"], {"tools": {}})
                self.assertEqual(r["serverInfo"]["name"], "simples-nacional")

    def test_versao_que_nao_suporta_recebe_a_mais_nova(self):
        for versao in ("2024-11-05", "2026-07-28", None):
            with self.subTest(versao=versao):
                self.assertEqual(self.iniciar(versao)[1]["protocolVersion"], "2025-11-25")

    def test_depois_do_initialize_sem_meta(self):
        s, _ = self.iniciar("2025-06-18")
        self.assertIsNone(s.responder({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        r = s.responder(pedido("tools/list", meta=None))["result"]
        self.assertNotIn("resultType", r)  # a forma antiga não conhece o campo
        self.assertEqual(len(r["tools"]), 4)
        self.assertEqual(s.responder(pedido("ping", meta=None))["result"], {})


class TestErrosDoProtocolo(unittest.TestCase):

    def test_metodo_desconhecido(self):
        self.assertEqual(erro(Servidor().responder(pedido("resources/list"))), -32601)

    def test_ferramenta_desconhecida(self):
        r = Servidor().responder(pedido("tools/call", {"name": "calcular_irpf", "arguments": {}}))
        self.assertEqual(erro(r), -32602)

    def test_mensagem_que_nao_e_jsonrpc(self):
        s = Servidor()
        for mensagem in ([pedido("tools/list")], {"id": 1, "method": "tools/list"}, 7):
            with self.subTest(mensagem=mensagem):
                self.assertEqual(erro(s.responder(mensagem)), -32600)

    def test_params_que_nao_e_objeto(self):
        r = Servidor().responder({"jsonrpc": "2.0", "id": 1, "method": "tools/list",
                                  "params": [1]})
        self.assertEqual(erro(r), -32602)

    def test_notificacao_e_resposta_do_cliente_nao_tem_resposta(self):
        s = Servidor()
        self.assertIsNone(s.responder({"jsonrpc": "2.0", "method": "notifications/cancelled"}))
        self.assertIsNone(s.responder({"jsonrpc": "2.0", "id": 9, "result": {}}))

    def test_json_quebrado(self):
        r = json.loads(tratar_linha(Servidor(), b'{"jsonrpc": "2.0",'))
        self.assertEqual((r["id"], erro(r)), (None, -32700))
        r = json.loads(tratar_linha(Servidor(), b"\xff\xfe"))
        self.assertEqual(erro(r), -32700)

    def test_linha_vazia_e_ignorada(self):
        self.assertIsNone(tratar_linha(Servidor(), b"\r\n"))


class TestDescricaoDasFerramentas(unittest.TestCase):

    def test_nome_esquema_e_dicas(self):
        for f in FERRAMENTAS:
            with self.subTest(ferramenta=f["name"]):
                self.assertRegex(f["name"], r"^[A-Za-z0-9_.-]{1,128}$")
                self.assertEqual(f["inputSchema"]["type"], "object")
                self.assertIs(f["inputSchema"]["additionalProperties"], False)
                self.assertIn("ano", f["inputSchema"]["required"])  # decisão de 10/10
                self.assertEqual(f["annotations"]["readOnlyHint"], True)
                self.assertEqual(f["annotations"]["openWorldHint"], False)
                for nome in f["inputSchema"]["required"]:
                    self.assertIn(nome, f["inputSchema"]["properties"])


class TestFerramentas(unittest.TestCase):
    """Os números são os da API (e do README), em texto exato."""

    def assertOk(self, resultado):
        self.assertIs(resultado["isError"], False, resultado["content"][0]["text"])
        dados = resultado["structuredContent"]
        self.assertEqual(dados["aviso"], AVISO)
        self.assertIn(AVISO, resultado["content"][0]["text"])
        # o mesmo JSON em texto, para cliente que não lê structuredContent
        self.assertEqual(json.loads(resultado["content"][1]["text"]), dados)
        json.dumps(dados)  # nada de Decimal solto
        return dados

    def test_calcular_das(self):
        d = self.assertOk(chamar("calcular_das", anexo="I", rbt12=4_500_000,
                                 receita_mes=375_000, ano=2026))
        self.assertEqual(d["aliquota_efetiva"], "0.106")
        self.assertEqual(d["valor_do_mes"], "39750.00")
        self.assertEqual(d["faixa"], {"numero": 6, "teto": "4800000.00",
                                      "aliquota_nominal": "0.19",
                                      "parcela_deduzir": "378000.00"})
        self.assertTrue(d["avisos"])  # acima do sublimite

    def test_calcular_das_com_icms_iss_e_2027(self):
        d = self.assertOk(chamar("calcular_das", anexo="I", rbt12=4_500_000,
                                 receita_mes=375_000, ano=2027, icms_iss_no_das=True))
        self.assertEqual(Decimal(d["aliquota_efetiva"]),
                         aliquota_efetiva("I", 4_500_000, ano=2027, icms_iss_no_das=True))
        self.assertEqual(d["aliquota_efetiva"], "0.14661612")
        self.assertIn("2027", d["tabela"])

    def test_repartir_das(self):
        d = self.assertOk(chamar("repartir_das", anexo="III", rbt12=3_000_000,
                                 receita_mes=100_000, ano=2026))
        self.assertEqual(d["valor_do_mes"], "16812.00")
        self.assertEqual(d["parcelas"]["ISS"], "5000.00")
        self.assertEqual({k: Decimal(v) for k, v in d["parcelas"].items()},
                         parcelas_das("III", 3_000_000, 100_000, ano=2026))
        self.assertEqual(sum(Decimal(v) for v in d["parcelas"].values()),
                         valor_devido("III", 3_000_000, 100_000, ano=2026))

    def test_planejar_fator_r(self):
        d = self.assertOk(chamar("planejar_fator_r", folha12=120_000, rbt12=600_000,
                                 receita_mes=50_000, ano=2026))
        self.assertEqual((d["fator"], d["anexo"], d["folha_minima"], d["folha_que_falta"]),
                         ("0.2", "V", "168000.00", "48000.00"))
        self.assertEqual((d["das_anexo_v"], d["das_anexo_iii"], d["diferenca_das"]),
                         ("8925.00", "5280.00", "3645.00"))
        self.assertIn("pró-labore", d["aviso_fator_r"])

    def test_enquadrar_cnae(self):
        d = self.assertOk(chamar("enquadrar_cnae", cnae="1091-1/02", ano=2026))
        self.assertEqual((d["situacao"], d["anexo"]), ("anexo", "II"))
        d = self.assertOk(chamar("enquadrar_cnae", cnae="1091102", ano=2027))
        self.assertEqual((d["anexo"], d["fundamento"]), ("I", "LC 123, art. 18, § 5º"))
        self.assertIn("interpretação", d["aviso_interpretacao"])

    def test_enquadrar_cnae_com_fator_r(self):
        d = self.assertOk(chamar("enquadrar_cnae", cnae="7112-0/00", ano=2026,
                                 folha12=300_000, rbt12=1_000_000))
        self.assertEqual((d["situacao"], d["fator_r"], d["anexo"]), ("fator_r", "0.3", "III"))

    def test_impeditiva_nao_e_erro(self):
        d = self.assertOk(chamar("enquadrar_cnae", cnae="8299-7/04", ano=2026))
        self.assertEqual((d["situacao"], d["anexo"]), ("impeditiva", None))


class TestEntrada(unittest.TestCase):
    """Entrada ruim volta como erro da ferramenta (isError), para o modelo corrigir."""

    BASE = {"anexo": "I", "rbt12": 4_500_000, "receita_mes": 375_000, "ano": 2026}

    def calcular(self, **troca):
        argumentos = {k: v for k, v in dict(self.BASE, **troca).items() if v is not None}
        return chamar("calcular_das", **argumentos)

    def assertErro(self, resultado, trecho):
        self.assertIs(resultado["isError"], True)
        self.assertNotIn("structuredContent", resultado)
        self.assertIn(trecho, resultado["content"][0]["text"])

    def test_numero_no_formato_brasileiro(self):
        r = self.calcular(rbt12="R$ 4.500.000,00", receita_mes="375.000")
        self.assertEqual(r["structuredContent"]["valor_do_mes"], "39750.00")

    def test_numero_com_casas_vira_decimal_exato(self):
        linha = json.dumps(pedido("tools/call", {"name": "calcular_das", "arguments": dict(
            self.BASE, receita_mes=0)})).replace('"receita_mes": 0', '"receita_mes": 0.1')
        r = json.loads(tratar_linha(Servidor(), linha.encode()))["result"]
        # 0.1 chega como Decimal('0.1'); como float, a biblioteca recusaria
        self.assertIs(r["isError"], False, r["content"][0]["text"])
        self.assertEqual(r["structuredContent"]["valor_do_mes"], "0.01")  # 0,1 × 10,6%

    def test_numero_ambiguo(self):
        self.assertErro(self.calcular(rbt12="1,000.50"), "rbt12")

    def test_booleano_nao_e_numero(self):
        self.assertErro(self.calcular(rbt12=True), "rbt12")

    def test_ano(self):
        self.assertErro(self.calcular(ano="2026"), "ano")
        self.assertErro(self.calcular(ano=Decimal("2026.0")), "ano")
        self.assertErro(self.calcular(ano=2017), "2018")

    def test_ano_obrigatorio(self):
        self.assertErro(self.calcular(ano=None), "faltam argumentos: ano")

    def test_argumento_desconhecido(self):
        self.assertErro(self.calcular(regime="simples"), "argumentos desconhecidos: regime")

    def test_anexo(self):
        self.assertErro(self.calcular(anexo="VI"), "anexo")
        self.assertErro(self.calcular(anexo="iii"), "anexo")

    def test_icms_iss_no_das_so_booleano(self):
        self.assertErro(self.calcular(icms_iss_no_das="sim"), "icms_iss_no_das")

    def test_acima_do_limite(self):
        r = self.calcular(rbt12="4.800.000,01")
        self.assertErro(r, "4.800.000,00")
        self.assertTrue(r["content"][0]["text"].startswith("limite: "))

    def test_cnae(self):
        self.assertErro(chamar("enquadrar_cnae", cnae="123", ano=2026), "7 dígitos")
        self.assertErro(chamar("enquadrar_cnae", cnae=6920601, ano=2026), "cnae")
        self.assertErro(chamar("enquadrar_cnae", cnae="6920-6/01", ano=2026, folha12=1),
                        "juntos")

    def test_numero_fora_do_alcance(self):
        # 1E+999999999 é número JSON válido e chega como Decimal
        linha = json.dumps(pedido("tools/call", {"name": "calcular_das", "arguments": dict(
            self.BASE, receita_mes=0)})).replace('"receita_mes": 0', '"receita_mes": 1E+999999999')
        r = json.loads(tratar_linha(Servidor(), linha.encode()))["result"]
        self.assertErro(r, "receita_mes: acima de R$ 1 trilhão")
        self.assertErro(self.calcular(rbt12="2.000.000.000.000"), "rbt12: acima")
        self.assertErro(self.calcular(receita_mes=Decimal("NaN")), "finito")
        self.assertIs(self.calcular(receita_mes=10**12)["isError"], False)

    def test_rbt12_zero_nao_cita_funcao_python(self):
        for rbt12 in (0, -1, "0,00"):
            with self.subTest(rbt12=rbt12):
                r = self.calcular(rbt12=rbt12)
                self.assertErro(r, "rbt12: tem de ser positivo")
                self.assertNotIn("aliquota_inicio_atividade", r["content"][0]["text"])

    def test_arguments_que_nao_e_objeto(self):
        r = Servidor().responder(pedido("tools/call", {"name": "calcular_das",
                                                       "arguments": [1]}))["result"]
        self.assertErro(r, "arguments")


class TestStdio(unittest.TestCase):
    """O processo de verdade: uma linha por mensagem, UTF-8, sai no fim do stdin."""

    def test_conversa(self):
        linhas = [
            pedido("server/discover", ident=1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            pedido("tools/call", {"name": "enquadrar_cnae",
                                  "arguments": {"cnae": "6920-6/01", "ano": 2026}}, ident=2),
            pedido("tools/call", {"name": "calcular_das", "arguments": {
                "anexo": "III", "rbt12": "3.000.000", "receita_mes": 100000, "ano": 2026}},
                ident="três"),
        ]
        # CRLF no fim de uma linha, como manda um cliente no Windows
        entrada = "\n".join(json.dumps(m, ensure_ascii=False) for m in linhas) + "\r\n"
        # sem PYTHONIOENCODING: o servidor não depende da codificação do console
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        r = subprocess.run([sys.executable, "-m", "simples_nacional.mcp"], cwd=BIBLIOTECA,
                           input=entrada.encode("utf-8"), capture_output=True, env=env,
                           timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, b"")
        self.assertNotIn(b"\r", r.stdout)
        saida = [json.loads(linha) for linha in r.stdout.decode("utf-8").splitlines()]
        self.assertEqual([m["id"] for m in saida], [1, 2, "três"])  # sem resposta à notificação
        self.assertIn("ATIVIDADES DE CONTABILIDADE",
                      saida[1]["result"]["content"][0]["text"])
        self.assertEqual(saida[2]["result"]["structuredContent"]["valor_do_mes"], "16812.00")

    def test_modulo_nao_escreve_ao_ser_importado(self):
        r = subprocess.run([sys.executable, "-c", "import simples_nacional.mcp"],
                           cwd=BIBLIOTECA, capture_output=True, timeout=60)
        self.assertEqual((r.returncode, r.stdout), (0, b""))


class TestReadme(unittest.TestCase):

    def test_readme_mostra_o_comando_e_as_ferramentas(self):
        readme = (BIBLIOTECA / "README.md").read_text(encoding="utf-8")
        self.assertIn("python -m simples_nacional.mcp", readme)
        for f in FERRAMENTAS:
            self.assertIn(f"`{f['name']}`", readme)
        self.assertTrue(re.search(r"claude mcp add .*simples_nacional\.mcp", readme))


if __name__ == "__main__":
    unittest.main()
