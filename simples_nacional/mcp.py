"""Servidor MCP (Model Context Protocol) da biblioteca, só com a biblioteca padrão.

    python -m simples_nacional.mcp

Transporte stdio: uma mensagem JSON-RPC por linha, em UTF-8; nada além do
protocolo no stdout. Atende as duas formas do protocolo no mesmo processo:
com `initialize` (revisões 2025-06-18 e 2025-11-25) e sem estado, com a
versão no `_meta` de cada requisição e `server/discover` (2026-07-28).
Especificação: https://modelcontextprotocol.io/specification, consultada em
10/10/2026.

Quatro ferramentas, todas cálculo puro: calcular_das, repartir_das,
planejar_fator_r e enquadrar_cnae. Estimativa: não substitui o PGDAS-D nem
o contador.
"""

import json
import sys
from decimal import Decimal

from . import __version__
from .calculo import LimiteExcedido, aliquota_efetiva, avisos, faixa, valor_devido
from .cnae import AVISO_INTERPRETACAO, enquadrar
from .formato import ler_numero, porcentagem, reais
from .planejamento import planejar_fator_r
from .reparticao import aliquotas_por_tributo, parcelas_das
from .tabelas import vigencia

VERSAO_SEM_ESTADO = "2026-07-28"
VERSOES_COM_INITIALIZE = ("2025-11-25", "2025-06-18")  # a mais nova primeiro
VERSOES = (VERSAO_SEM_ESTADO,) + VERSOES_COM_INITIALIZE

META_VERSAO = "io.modelcontextprotocol/protocolVersion"
META_CAPACIDADES = "io.modelcontextprotocol/clientCapabilities"
META_SERVIDOR = "io.modelcontextprotocol/serverInfo"

SERVIDOR = {"name": "simples-nacional", "title": "Simples Nacional (LC 123)",
            "version": __version__}

AVISO = "Estimativa conferida contra a tabela da lei: não substitui o PGDAS-D nem o contador."

INSTRUCOES = (
    "Cálculo do Simples Nacional conferido contra a LC 123/2006 e, de 2027 em diante, a "
    "LC 214/2025: alíquota efetiva, valor do mês (DAS), repartição por tributo, "
    "planejamento do Fator R e enquadramento CNAE -> anexo, para uma empresa por vez. "
    "Valores em reais, como número JSON ou texto no formato brasileiro ('4.500.000,00'). "
    "`ano` é o ano-calendário do mês de apuração, não o de hoje. " + AVISO)

# códigos JSON-RPC 2.0 e do MCP (versão não suportada: revisão 2026-07-28)
JSON_INVALIDO, REQUISICAO_INVALIDA, METODO_DESCONHECIDO = -32700, -32600, -32601
PARAMETRO_INVALIDO, ERRO_INTERNO, VERSAO_NAO_SUPORTADA = -32602, -32603, -32022


class ErroDoProtocolo(Exception):
    def __init__(self, codigo, mensagem, dados=None):
        super().__init__(mensagem)
        self.codigo, self.dados = codigo, dados


# --- ferramentas -------------------------------------------------------------

def _valor(descricao):
    return {"type": ["number", "string"], "description": descricao}


ANEXO = {"type": "string", "enum": ["I", "II", "III", "IV", "V"],
         "description": "Anexo da LC 123: I comércio, II indústria, III a V serviços."}
ANO = {"type": "integer", "minimum": 2018,
       "description": "Ano-calendário do mês de apuração (o DAS de dezembro de 2026 usa 2026)."}
RBT12 = _valor("Receita bruta dos 12 meses anteriores ao de apuração, em reais (de 2027 em "
               "diante, dos 12 antecedentes ao mês anterior).")
RECEITA_MES = _valor("Receita bruta do mês de apuração, em reais.")
FOLHA12 = _valor("Folha de salários dos 12 meses do RBT12, com pró-labore e encargos "
                 "(LC 123, art. 18, § 24), em reais.")
ICMS_ISS = {"type": "boolean", "default": False,
            "description": "RBT12 acima de R$ 3,6 milhões com a receita do ano dentro do "
                           "sublimite: soma ICMS ou ISS (e IBS desde 2027) pela 5ª faixa."}

PURO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True,
        "openWorldHint": False}


def _esquema(propriedades, obrigatorias):
    return {"type": "object", "properties": propriedades, "required": obrigatorias,
            "additionalProperties": False}


FERRAMENTAS = [
    {"name": "calcular_das",
     "title": "Alíquota efetiva e valor do mês",
     "description": "Faixa, alíquota efetiva (LC 123, art. 18, § 1º-A) e valor do mês no "
                    "Simples Nacional, com os avisos de sublimite e teto.",
     "inputSchema": _esquema({"anexo": ANEXO, "rbt12": RBT12, "receita_mes": RECEITA_MES,
                              "ano": ANO, "icms_iss_no_das": ICMS_ISS},
                             ["anexo", "rbt12", "receita_mes", "ano"])},
    {"name": "repartir_das",
     "title": "Repartição do DAS por tributo",
     "description": "Quanto do valor do mês vai a cada tributo (IRPJ, CSLL, Cofins, PIS, "
                    "CPP, ICMS, ISS e, de 2027 em diante, CBS e IBS), em centavos.",
     "inputSchema": _esquema({"anexo": ANEXO, "rbt12": RBT12, "receita_mes": RECEITA_MES,
                              "ano": ANO},
                             ["anexo", "rbt12", "receita_mes", "ano"])},
    {"name": "planejar_fator_r",
     "title": "Planejamento do Fator R",
     "description": "Fator R (folha ÷ RBT12), a folha de 12 meses que leva a 28% e o valor "
                    "do mês nos Anexos V e III. A diferença é só no DAS: a contribuição "
                    "previdenciária e o IRPF do pró-labore a mais não estão descontados.",
     "inputSchema": _esquema({"folha12": FOLHA12, "rbt12": RBT12,
                              "receita_mes": RECEITA_MES, "ano": ANO,
                              "icms_iss_no_das": ICMS_ISS},
                             ["folha12", "rbt12", "receita_mes", "ano"])},
    {"name": "enquadrar_cnae",
     "title": "CNAE -> anexo",
     "description": "Situação de uma subclasse da CNAE no Simples: impeditiva (Res. CGSN "
                    "140, Anexo VI), ambígua (Anexo VII), anexo pela LC 123, art. 18, Fator "
                    "R ou sem classificação. Interpretação declarada, não tabela oficial.",
     "inputSchema": _esquema({"cnae": {"type": "string",
                                       "description": "Subclasse com 7 dígitos: 6920-6/01 "
                                                      "ou 6920601."},
                              "ano": ANO,
                              "folha12": FOLHA12, "rbt12": RBT12},
                             ["cnae", "ano"])},
]
for _ferramenta in FERRAMENTAS:
    _ferramenta["annotations"] = PURO


class ErroDeEntrada(ValueError):
    """Argumento que não serve: volta ao modelo como erro da ferramenta."""


def _numero(argumentos, nome):
    valor = argumentos.get(nome)
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, Decimal, str)):
        raise ErroDeEntrada(f"{nome}: número ou texto, não {type(valor).__name__}")
    if isinstance(valor, str):
        try:
            return ler_numero(valor)
        except ValueError as erro:
            raise ErroDeEntrada(f"{nome}: {erro}") from None
    return valor


def _ano(argumentos):
    ano = argumentos["ano"]
    if isinstance(ano, bool) or not isinstance(ano, int):
        raise ErroDeEntrada(f"ano: número inteiro (ex.: 2026), não {ano!r}")
    vigencia(ano)  # ano antes de 2018: ValueError explicado
    return ano


def _anexo(argumentos):
    anexo = argumentos["anexo"]
    if anexo not in ANEXO["enum"]:
        raise ErroDeEntrada(f"anexo: um de I, II, III, IV ou V, não {anexo!r}")
    return anexo


def _texto(valor):
    """Decimal sem notação científica: '0.106', '39750.00'."""
    return format(valor, "f")


def calcular_das(a):
    anexo, ano = _anexo(a), _ano(a)
    rbt12, receita = _numero(a, "rbt12"), _numero(a, "receita_mes")
    icms_iss = a.get("icms_iss_no_das", False)
    f = faixa(anexo, rbt12, ano=ano)
    efetiva = aliquota_efetiva(anexo, rbt12, ano=ano, icms_iss_no_das=icms_iss)
    valor = valor_devido(anexo, rbt12, receita, ano=ano, icms_iss_no_das=icms_iss)
    lista = avisos(rbt12, ano=ano, icms_iss_no_das=icms_iss)
    dados = {"ano": ano, "tabela": vigencia(ano).fonte, "anexo": anexo,
             "faixa": {"numero": f.numero, "teto": _texto(f.teto),
                       "aliquota_nominal": _texto(f.aliquota),
                       "parcela_deduzir": _texto(f.parcela_deduzir)},
             "aliquota_efetiva": _texto(efetiva), "valor_do_mes": _texto(valor),
             "avisos": lista}
    linhas = [f"Anexo {anexo}, {f.numero}ª faixa, ano {ano}: alíquota efetiva "
              f"{porcentagem(efetiva)}; valor do mês R$ {reais(valor)}."]
    return dados, linhas + [f"Aviso: {texto}" for texto in lista]


def repartir_das(a):
    anexo, ano = _anexo(a), _ano(a)
    rbt12, receita = _numero(a, "rbt12"), _numero(a, "receita_mes")
    parcelas = parcelas_das(anexo, rbt12, receita, ano=ano)
    fracoes = aliquotas_por_tributo(anexo, rbt12, ano=ano)
    total = sum(parcelas.values())
    dados = {"ano": ano, "anexo": anexo, "valor_do_mes": _texto(total),
             "parcelas": {tributo: _texto(v) for tributo, v in parcelas.items()},
             "aliquotas": {tributo: _texto(v) for tributo, v in fracoes.items()}}
    return dados, [f"Valor do mês R$ {reais(total)}: "
                   + "; ".join(f"{t} R$ {reais(v)}" for t, v in parcelas.items()) + "."]


def planejar(a):
    ano = _ano(a)
    folha12, rbt12 = _numero(a, "folha12"), _numero(a, "rbt12")
    receita = _numero(a, "receita_mes")
    p = planejar_fator_r(folha12, rbt12, receita, ano=ano,
                         icms_iss_no_das=a.get("icms_iss_no_das", False))
    dados = {"ano": ano, **{campo: (v if isinstance(v, str) else _texto(v))
                            for campo, v in p._asdict().items()},
             "aviso_fator_r": "A diferença é só no DAS: a contribuição previdenciária e o "
                              "IRPF do pró-labore a mais não estão descontados."}
    return dados, [
        f"Fator R {porcentagem(p.fator)}: Anexo {p.anexo}. Folha de 12 meses para 28%: "
        f"R$ {reais(p.folha_minima)} (faltam R$ {reais(p.folha_que_falta)}).",
        f"Valor do mês no Anexo V R$ {reais(p.das_anexo_v)}; no III R$ "
        f"{reais(p.das_anexo_iii)}; diferença R$ {reais(p.diferenca_das)}.",
        dados["aviso_fator_r"]]


def enquadrar_cnae(a):
    ano = _ano(a)
    cnae = a["cnae"]
    if not isinstance(cnae, str):
        raise ErroDeEntrada(f"cnae: texto com 7 dígitos, não {cnae!r}")
    e = enquadrar(cnae, ano=ano, folha12=_numero(a, "folha12"), rbt12=_numero(a, "rbt12"))
    dados = {"ano": ano, **e._asdict(),
             "fator_r": None if e.fator_r is None else _texto(e.fator_r),
             "aviso_interpretacao": AVISO_INTERPRETACAO}
    anexo = f"Anexo {e.anexo}" if e.anexo else e.situacao
    return dados, [f"{e.subclasse} {e.denominacao}: {anexo} ({e.fundamento or 'sem fundamento'}).",
                   e.observacao, AVISO_INTERPRETACAO]


EXECUTAR = {"calcular_das": calcular_das, "repartir_das": repartir_das,
            "planejar_fator_r": planejar, "enquadrar_cnae": enquadrar_cnae}


def chamar(nome, argumentos):
    """Resultado de tools/call: erro de entrada ou de regra volta como isError."""
    if nome not in EXECUTAR:
        raise ErroDoProtocolo(PARAMETRO_INVALIDO, f"Unknown tool: {nome}")
    ferramenta = next(f for f in FERRAMENTAS if f["name"] == nome)
    esquema = ferramenta["inputSchema"]
    try:
        if not isinstance(argumentos, dict):
            raise ErroDeEntrada("arguments: objeto JSON com os argumentos")
        faltam = [c for c in esquema["required"] if c not in argumentos]
        sobram = sorted(set(argumentos) - set(esquema["properties"]))
        if faltam:
            raise ErroDeEntrada(f"faltam argumentos: {', '.join(faltam)}")
        if sobram:
            raise ErroDeEntrada(f"argumentos desconhecidos: {', '.join(sobram)}")
        if not isinstance(argumentos.get("icms_iss_no_das", False), bool):
            raise ErroDeEntrada("icms_iss_no_das: true ou false")
        dados, linhas = EXECUTAR[nome](argumentos)
    except (ValueError, TypeError) as erro:  # LimiteExcedido é ValueError
        rotulo = "limite" if isinstance(erro, LimiteExcedido) else "erro"
        return {"content": [{"type": "text", "text": f"{rotulo}: {erro}"}], "isError": True}
    dados["aviso"] = AVISO
    texto = "\n".join(linhas + [AVISO])
    return {"content": [{"type": "text", "text": texto},
                        {"type": "text", "text": json.dumps(dados, ensure_ascii=False)}],
            "structuredContent": dados, "isError": False}


# --- protocolo ---------------------------------------------------------------

class Servidor:
    """Responde mensagem a mensagem; `iniciado` vale para a forma com initialize."""

    def __init__(self):
        self.iniciado = False

    def responder(self, mensagem):
        """Resposta JSON-RPC (dict) ou None, para notificação e resposta do cliente."""
        if not isinstance(mensagem, dict) or mensagem.get("jsonrpc") != "2.0":
            return _erro(None, REQUISICAO_INVALIDA, "Invalid Request")
        if "method" not in mensagem:
            return None  # resposta do cliente: o servidor não faz requisição
        if "id" not in mensagem:
            return None  # notificação (initialized, cancelled): não se responde
        ident = mensagem["id"]
        try:
            return {"jsonrpc": "2.0", "id": ident, "result": self._metodo(mensagem)}
        except ErroDoProtocolo as erro:
            return _erro(ident, erro.codigo, str(erro), erro.dados)
        except Exception as erro:  # defeito do servidor: nunca derruba o processo
            print(f"simples-nacional mcp: {erro!r}", file=sys.stderr)
            return _erro(ident, ERRO_INTERNO, "Internal error")

    def _metodo(self, mensagem):
        metodo, params = mensagem["method"], mensagem.get("params") or {}
        if not isinstance(params, dict):
            raise ErroDoProtocolo(PARAMETRO_INVALIDO, "params: objeto JSON")
        if metodo == "initialize":
            pedida = params.get("protocolVersion")
            self.iniciado = True
            return {"protocolVersion": (pedida if pedida in VERSOES_COM_INITIALIZE
                                        else VERSOES_COM_INITIALIZE[0]),
                    "capabilities": {"tools": {}}, "serverInfo": SERVIDOR,
                    "instructions": INSTRUCOES}
        meta = params.get("_meta") or {}
        sem_estado = META_VERSAO in meta
        if sem_estado:
            if meta[META_VERSAO] != VERSAO_SEM_ESTADO:
                raise ErroDoProtocolo(VERSAO_NAO_SUPORTADA, "Unsupported protocol version",
                                      {"supported": list(VERSOES),
                                       "requested": meta[META_VERSAO]})
            if META_CAPACIDADES not in meta:
                raise ErroDoProtocolo(PARAMETRO_INVALIDO,
                                      f"_meta sem {META_CAPACIDADES}")
        elif metodo != "ping" and metodo != "server/discover" and not self.iniciado:
            raise ErroDoProtocolo(PARAMETRO_INVALIDO,
                                  f"_meta sem {META_VERSAO} (ou initialize antes)")
        resultado = self._resultado(metodo, params)
        if sem_estado or metodo == "server/discover":
            resultado = {"resultType": "complete", **resultado,
                         "_meta": {META_SERVIDOR: SERVIDOR}}
        return resultado

    def _resultado(self, metodo, params):
        if metodo == "ping":
            return {}
        if metodo == "server/discover":
            return {"supportedVersions": list(VERSOES), "capabilities": {"tools": {}},
                    "instructions": INSTRUCOES, "ttlMs": 3_600_000, "cacheScope": "public"}
        if metodo == "tools/list":
            return {"tools": FERRAMENTAS, "ttlMs": 3_600_000, "cacheScope": "public"}
        if metodo == "tools/call":
            if not isinstance(params.get("name"), str):
                raise ErroDoProtocolo(PARAMETRO_INVALIDO, "tools/call: falta name")
            return chamar(params["name"], params.get("arguments", {}))
        raise ErroDoProtocolo(METODO_DESCONHECIDO, f"Method not found: {metodo}")


def _erro(ident, codigo, mensagem, dados=None):
    erro = {"code": codigo, "message": mensagem}
    if dados is not None:
        erro["data"] = dados
    return {"jsonrpc": "2.0", "id": ident, "error": erro}


def _para_json(valor):
    if isinstance(valor, Decimal):
        return _texto(valor)
    raise TypeError(f"{type(valor).__name__} não vai em JSON")


def tratar_linha(servidor, linha):
    """Uma linha do stdin (bytes) -> a linha da resposta (bytes) ou None."""
    if not linha.strip():
        return None
    try:
        # número decimal vira Decimal: float erra centavo
        mensagem = json.loads(linha.decode("utf-8"), parse_float=Decimal)
    except (UnicodeDecodeError, ValueError):
        resposta = _erro(None, JSON_INVALIDO, "Parse error")
    else:
        resposta = servidor.responder(mensagem)
    if resposta is None:
        return None
    return json.dumps(resposta, ensure_ascii=False, default=_para_json).encode("utf-8") + b"\n"


def main():
    servidor = Servidor()
    for linha in sys.stdin.buffer:  # sai no fim do stdin, como pede o transporte
        resposta = tratar_linha(servidor, linha)
        if resposta is not None:
            sys.stdout.buffer.write(resposta)
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
