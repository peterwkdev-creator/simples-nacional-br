"""Repartição do DAS por tributo: percentual de cada tributo em cada faixa.

Uma tabela "Percentual de Repartição dos Tributos" (ou "Partilha do Simples
Nacional") por anexo e período, mais a nota (*) dos Anexos III e IV, que
limita o ISS da 5ª faixa:

- 2018 a 2026: LC 123/2006, Anexos I a V, com a redação da LC 155/2016
  (vigência: 1º/1/2018). Texto atualizado da LC 155 lido no site da Câmara
  dos Deputados em 10/10/2026:
  https://www2.camara.leg.br/legin/fed/leicom/2016/leicomplementar-155-27-outubro-2016-783850-normaatualizada-pl.html
- 2027 e 2028: LC 214/2025, art. 519 e Anexos XVIII a XXII (nova redação dos
  Anexos I a V da LC 123, vigência de 1º/1/2027 a 31/12/2028, art. 544,
  III); Anexo III com a redação da LC 227/2026. PIS e Cofins dão lugar a CBS
  e IBS. Texto atualizado lido no site da Câmara em 09/10/2026:
  https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html
- 2029, 2030, 2031, 2032 e "a partir do ano-calendário 2033": LC 214/2025,
  os mesmos anexos, uma tabela por período; III e IV com a redação da LC
  227/2026. O IBS toma o lugar do ICMS e do ISS aos poucos; de 2033 em diante
  só há IBS. Mesmo texto atualizado, lido em 10/10/2026.

Percentuais em fração (34,00% = Decimal("0.34")). O "-" da lei (tributo sem
parcela na faixa) fica de fora da linha: na 6ª faixa, acima do sublimite, o
ICMS, o ISS e o IBS são pagos fora do DAS (LC 123, art. 13-A). Alíquota
nominal e parcela a deduzir estão em `tabelas.py`.
"""

from decimal import Decimal


def _partilha(colunas, *linhas):
    return tuple(
        {c: Decimal(v) / 100 for c, v in zip(colunas.split(), linha.split()) if v != "-"}
        for linha in linhas
    )


PARTILHA_ATE_2026 = {
    # Anexo I - Comércio
    "I": _partilha(
        "IRPJ CSLL COFINS PIS CPP ICMS",
        "5.50 3.50 12.74 2.76 41.50 34.00",
        "5.50 3.50 12.74 2.76 41.50 34.00",
        "5.50 3.50 12.74 2.76 42.00 33.50",
        "5.50 3.50 12.74 2.76 42.00 33.50",
        "5.50 3.50 12.74 2.76 42.00 33.50",
        "13.50 10.00 28.27 6.13 42.10 -",
    ),
    # Anexo II - Indústria
    "II": _partilha(
        "IRPJ CSLL COFINS PIS CPP IPI ICMS",
        "5.50 3.50 11.51 2.49 37.50 7.50 32.00",
        "5.50 3.50 11.51 2.49 37.50 7.50 32.00",
        "5.50 3.50 11.51 2.49 37.50 7.50 32.00",
        "5.50 3.50 11.51 2.49 37.50 7.50 32.00",
        "5.50 3.50 11.51 2.49 37.50 7.50 32.00",
        "8.50 7.50 20.96 4.54 23.50 35.00 -",
    ),
    # Anexo III - locação de bens móveis e serviços fora do § 5º-C do art. 18
    "III": _partilha(
        "IRPJ CSLL COFINS PIS CPP ISS",
        "4.00 3.50 12.82 2.78 43.40 33.50",
        "4.00 3.50 14.05 3.05 43.40 32.00",
        "4.00 3.50 13.64 2.96 43.40 32.50",
        "4.00 3.50 13.64 2.96 43.40 32.50",
        "4.00 3.50 12.82 2.78 43.40 33.50",
        "35.00 15.00 16.03 3.47 30.50 -",
    ),
    # Anexo IV - serviços do art. 18, § 5º-C (CPP fora do DAS)
    "IV": _partilha(
        "IRPJ CSLL COFINS PIS ISS",
        "18.80 15.20 17.67 3.83 44.50",
        "19.80 15.20 20.55 4.45 40.00",
        "20.80 15.20 19.73 4.27 40.00",
        "17.80 19.20 18.90 4.10 40.00",
        "18.80 19.20 18.08 3.92 40.00",
        "53.50 21.50 20.55 4.45 -",
    ),
    # Anexo V - serviços do art. 18, § 5º-I
    "V": _partilha(
        "IRPJ CSLL COFINS PIS CPP ISS",
        "25.00 15.00 14.10 3.05 28.85 14.00",
        "23.00 15.00 14.10 3.05 27.85 17.00",
        "24.00 15.00 14.92 3.23 23.85 19.00",
        "21.00 15.00 15.74 3.41 23.85 21.00",
        "23.00 12.50 14.10 3.05 23.85 23.50",
        "35.00 15.50 16.44 3.56 29.50 -",
    ),
}

# Nota (*) dos Anexos III e IV: "O percentual efetivo máximo devido ao ISS
# será de 5%". Na 5ª faixa, com efetiva acima de 14,92537% (III) ou de 12,5%
# (IV), o ISS fica em 5% e cada tributo federal leva (efetiva - 5%) x o
# percentual abaixo.
TETO_ISS_ATE_2026 = {
    "III": _partilha("IRPJ CSLL COFINS PIS CPP", "6.02 5.26 19.28 4.18 65.26")[0],
    "IV": _partilha("IRPJ CSLL COFINS PIS", "31.33 32.00 30.13 6.54")[0],
}

PARTILHA_2027_2028 = {
    # Anexo XVIII da LC 214 (Anexo I da LC 123) - Comércio
    "I": _partilha(
        "IRPJ CSLL CBS CPP ICMS IBS",
        "5.50 3.50 15.33 41.50 34.00 0.17",
        "5.50 3.50 15.33 41.50 34.00 0.17",
        "5.50 3.50 15.33 42.00 33.50 0.17",
        "5.50 3.50 15.33 42.00 33.50 0.17",
        "5.50 3.50 15.33 42.00 33.50 0.17",
        "13.58 10.06 34.02 42.34 - -",
    ),
    # Anexo XIX (Anexo II) - Indústria
    "II": _partilha(
        "IRPJ CSLL CBS CPP IPI ICMS IBS",
        "5.50 3.50 13.85 37.50 7.50 32.00 0.15",
        "5.50 3.50 13.85 37.50 7.50 32.00 0.15",
        "5.50 3.50 13.85 37.50 7.50 32.00 0.15",
        "5.50 3.50 13.85 37.50 7.50 32.00 0.15",
        "5.50 3.50 13.85 37.50 7.50 32.00 0.15",
        "8.53 7.53 25.22 23.59 35.13 - -",
    ),
    # Anexo XX (Anexo III), redação da LC 227/2026 - serviços e locação de bens móveis
    "III": _partilha(
        "IRPJ CSLL CBS CPP ISS IBS",
        "4.00 3.50 15.43 43.40 33.50 0.17",
        "4.00 3.50 16.91 43.40 32.00 0.19",
        "4.00 3.50 16.41 43.40 32.50 0.19",
        "4.00 3.50 16.41 43.40 32.50 0.19",
        "4.00 3.50 15.43 43.40 33.50 0.17",
        "35.09 15.04 19.29 30.58 - -",
    ),
    # Anexo XXI (Anexo IV) - serviços do art. 18, § 5º-C (CPP fora do DAS)
    "IV": _partilha(
        "IRPJ CSLL CBS ISS IBS",
        "18.80 15.20 21.26 44.50 0.24",
        "19.80 15.20 24.73 40.00 0.27",
        "20.80 15.20 23.74 40.00 0.26",
        "17.80 19.20 22.75 40.00 0.25",
        "18.80 19.20 21.76 40.00 0.24",
        "53.71 21.59 24.70 - -",
    ),
    # Anexo XXII (Anexo V) - serviços do art. 18, § 5º-I
    "V": _partilha(
        "IRPJ CSLL CBS CPP ISS IBS",
        "25.00 15.00 16.96 28.85 14.00 0.19",
        "23.00 15.00 16.96 27.85 17.00 0.19",
        "24.00 15.00 17.95 23.85 19.00 0.20",
        "21.00 15.00 18.94 23.85 21.00 0.21",
        "23.00 12.50 16.96 23.85 23.50 0.19",
        "35.10 15.54 19.78 29.58 - -",
    ),
}

# Nota (*) dos Anexos III e IV: "O percentual efetivo máximo devido ao ISS
# será de 5%". Na 5ª faixa, quando o ISS da tabela passar de 5% da receita,
# o ISS fica em 5% e cada outro tributo leva (alíquota efetiva - 5%) x o
# percentual abaixo.
TETO_ISS_2027_2028 = {
    "III": _partilha("IRPJ CSLL CBS CPP IBS", "6.02 5.26 23.20 65.26 0.26")[0],
    "IV": _partilha("IRPJ CSLL CBS IBS", "31.33 32.00 36.27 0.40")[0],
}

PARTILHA_DESDE_2029 = {
    2029: {  # ano-calendário 2029
        # Anexo XVIII (Anexo I) - Comércio
        "I": _partilha(
            "IRPJ CSLL CBS CPP ICMS IBS",
            "5.50 3.50 15.50 41.50 30.60 3.40",
            "5.50 3.50 15.50 41.50 30.60 3.40",
            "5.50 3.50 15.50 42.00 30.15 3.35",
            "5.50 3.50 15.50 42.00 30.15 3.35",
            "5.50 3.50 15.50 42.00 30.15 3.35",
            "13.50 10.00 34.40 42.10 - -",
        ),
        # Anexo XIX (Anexo II) - Indústria
        "II": _partilha(
            "IRPJ CSLL CBS CPP IPI ICMS IBS",
            "5.50 3.50 14.00 37.50 7.50 28.80 3.20",
            "5.50 3.50 14.00 37.50 7.50 28.80 3.20",
            "5.50 3.50 14.00 37.50 7.50 28.80 3.20",
            "5.50 3.50 14.00 37.50 7.50 28.80 3.20",
            "5.50 3.50 14.00 37.50 7.50 28.80 3.20",
            "8.50 7.50 25.50 23.50 35.00 - -",
        ),
        # Anexo XX (Anexo III), redação da LC 227/2026
        "III": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "4.00 3.50 15.60 43.40 30.15 3.35",
            "4.00 3.50 17.10 43.40 28.80 3.20",
            "4.00 3.50 16.60 43.40 29.25 3.25",
            "4.00 3.50 16.60 43.40 29.25 3.25",
            "4.00 3.50 15.60 43.40 30.15 3.35",
            "35.00 15.00 19.50 30.50 - -",
        ),
        # Anexo XXI (Anexo IV), redação da LC 227/2026 (CPP fora do DAS)
        "IV": _partilha(
            "IRPJ CSLL CBS ISS IBS",
            "18.80 15.20 21.50 40.05 4.45",
            "19.80 15.20 25.00 36.00 4.00",
            "20.80 15.20 24.00 36.00 4.00",
            "17.80 19.20 23.00 36.00 4.00",
            "18.80 19.20 22.00 36.00 4.00",
            "53.50 21.50 25.00 - -",
        ),
        # Anexo XXII (Anexo V)
        "V": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "25.00 15.00 17.15 28.85 12.60 1.40",
            "23.00 15.00 17.15 27.85 15.30 1.70",
            "24.00 15.00 18.15 23.85 17.10 1.90",
            "21.00 15.00 19.15 23.85 18.90 2.10",
            "23.00 12.50 17.15 23.85 21.15 2.35",
            "35.00 15.50 20.00 29.50 - -",
        ),
    },
    2030: {  # ano-calendário 2030
        # Anexo XVIII (Anexo I) - Comércio
        "I": _partilha(
            "IRPJ CSLL CBS CPP ICMS IBS",
            "5.50 3.50 15.50 41.50 27.20 6.80",
            "5.50 3.50 15.50 41.50 27.20 6.80",
            "5.50 3.50 15.50 42.00 26.80 6.70",
            "5.50 3.50 15.50 42.00 26.80 6.70",
            "5.50 3.50 15.50 42.00 26.80 6.70",
            "13.50 10.00 34.40 42.10 - -",
        ),
        # Anexo XIX (Anexo II) - Indústria
        "II": _partilha(
            "IRPJ CSLL CBS CPP IPI ICMS IBS",
            "5.50 3.50 14.00 37.50 7.50 25.60 6.40",
            "5.50 3.50 14.00 37.50 7.50 25.60 6.40",
            "5.50 3.50 14.00 37.50 7.50 25.60 6.40",
            "5.50 3.50 14.00 37.50 7.50 25.60 6.40",
            "5.50 3.50 14.00 37.50 7.50 25.60 6.40",
            "8.50 7.50 25.50 23.50 35.00 - -",
        ),
        # Anexo XX (Anexo III), redação da LC 227/2026
        "III": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "4.00 3.50 15.60 43.40 26.80 6.70",
            "4.00 3.50 17.10 43.40 25.60 6.40",
            "4.00 3.50 16.60 43.40 26.00 6.50",
            "4.00 3.50 16.60 43.40 26.00 6.50",
            "4.00 3.50 15.60 43.40 26.80 6.70",
            "35.00 15.00 19.50 30.50 - -",
        ),
        # Anexo XXI (Anexo IV), redação da LC 227/2026 (CPP fora do DAS)
        "IV": _partilha(
            "IRPJ CSLL CBS ISS IBS",
            "18.80 15.20 21.50 35.60 8.90",
            "19.80 15.20 25.00 32.00 8.00",
            "20.80 15.20 24.00 32.00 8.00",
            "17.80 19.20 23.00 32.00 8.00",
            "18.80 19.20 22.00 32.00 8.00",
            "53.50 21.50 25.00 - -",
        ),
        # Anexo XXII (Anexo V)
        "V": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "25.00 15.00 17.15 28.85 11.20 2.80",
            "23.00 15.00 17.15 27.85 13.60 3.40",
            "24.00 15.00 18.15 23.85 15.20 3.80",
            "21.00 15.00 19.15 23.85 16.80 4.20",
            "23.00 12.50 17.15 23.85 18.80 4.70",
            "35.00 15.50 20.00 29.50 - -",
        ),
    },
    2031: {  # ano-calendário 2031
        # Anexo XVIII (Anexo I) - Comércio
        "I": _partilha(
            "IRPJ CSLL CBS CPP ICMS IBS",
            "5.50 3.50 15.50 41.50 23.80 10.20",
            "5.50 3.50 15.50 41.50 23.80 10.20",
            "5.50 3.50 15.50 42.00 23.45 10.05",
            "5.50 3.50 15.50 42.00 23.45 10.05",
            "5.50 3.50 15.50 42.00 23.45 10.05",
            "13.50 10.00 34.40 42.10 - -",
        ),
        # Anexo XIX (Anexo II) - Indústria
        "II": _partilha(
            "IRPJ CSLL CBS CPP IPI ICMS IBS",
            "5.50 3.50 14.00 37.50 7.50 22.40 9.60",
            "5.50 3.50 14.00 37.50 7.50 22.40 9.60",
            "5.50 3.50 14.00 37.50 7.50 22.40 9.60",
            "5.50 3.50 14.00 37.50 7.50 22.40 9.60",
            "5.50 3.50 14.00 37.50 7.50 22.40 9.60",
            "8.50 7.50 25.50 23.50 35.00 - -",
        ),
        # Anexo XX (Anexo III), redação da LC 227/2026
        "III": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "4.00 3.50 15.60 43.40 23.45 10.05",
            "4.00 3.50 17.10 43.40 22.40 9.60",
            "4.00 3.50 16.60 43.40 22.75 9.75",
            "4.00 3.50 16.60 43.40 22.75 9.75",
            "4.00 3.50 15.60 43.40 23.45 10.05",
            "35.00 15.00 19.50 30.50 - -",
        ),
        # Anexo XXI (Anexo IV), redação da LC 227/2026 (CPP fora do DAS)
        "IV": _partilha(
            "IRPJ CSLL CBS ISS IBS",
            "18.80 15.20 21.50 31.15 13.35",
            "19.80 15.20 25.00 28.00 12.00",
            "20.80 15.20 24.00 28.00 12.00",
            "17.80 19.20 23.00 28.00 12.00",
            "18.80 19.20 22.00 28.00 12.00",
            "53.50 21.50 25.00 - -",
        ),
        # Anexo XXII (Anexo V)
        "V": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "25.00 15.00 17.15 28.85 9.80 4.20",
            "23.00 15.00 17.15 27.85 11.90 5.10",
            "24.00 15.00 18.15 23.85 13.30 5.70",
            "21.00 15.00 19.15 23.85 14.70 6.30",
            "23.00 12.50 17.15 23.85 16.45 7.05",
            "35.00 15.50 20.00 29.50 - -",
        ),
    },
    2032: {  # ano-calendário 2032
        # Anexo XVIII (Anexo I) - Comércio
        "I": _partilha(
            "IRPJ CSLL CBS CPP ICMS IBS",
            "5.50 3.50 15.50 41.50 20.40 13.60",
            "5.50 3.50 15.50 41.50 20.40 13.60",
            "5.50 3.50 15.50 42.00 20.10 13.40",
            "5.50 3.50 15.50 42.00 20.10 13.40",
            "5.50 3.50 15.50 42.00 20.10 13.40",
            "13.50 10.00 34.40 42.10 - -",
        ),
        # Anexo XIX (Anexo II) - Indústria
        "II": _partilha(
            "IRPJ CSLL CBS CPP IPI ICMS IBS",
            "5.50 3.50 14.00 37.50 7.50 19.20 12.80",
            "5.50 3.50 14.00 37.50 7.50 19.20 12.80",
            "5.50 3.50 14.00 37.50 7.50 19.20 12.80",
            "5.50 3.50 14.00 37.50 7.50 19.20 12.80",
            "5.50 3.50 14.00 37.50 7.50 19.20 12.80",
            "8.50 7.50 25.50 23.50 35.00 - -",
        ),
        # Anexo XX (Anexo III), redação da LC 227/2026
        "III": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "4.00 3.50 15.60 43.40 20.10 13.40",
            "4.00 3.50 17.10 43.40 19.20 12.80",
            "4.00 3.50 16.60 43.40 19.50 13.00",
            "4.00 3.50 16.60 43.40 19.50 13.00",
            "4.00 3.50 15.60 43.40 20.10 13.40",
            "35.00 15.00 19.50 30.50 - -",
        ),
        # Anexo XXI (Anexo IV), redação da LC 227/2026 (CPP fora do DAS)
        "IV": _partilha(
            "IRPJ CSLL CBS ISS IBS",
            "18.80 15.20 21.50 26.70 17.80",
            "19.80 15.20 25.00 24.00 16.00",
            "20.80 15.20 24.00 24.00 16.00",
            "17.80 19.20 23.00 24.00 16.00",
            "18.80 19.20 22.00 24.00 16.00",
            "53.50 21.50 25.00 - -",
        ),
        # Anexo XXII (Anexo V)
        "V": _partilha(
            "IRPJ CSLL CBS CPP ISS IBS",
            "25.00 15.00 17.15 28.85 8.40 5.60",
            "23.00 15.00 17.15 27.85 10.20 6.80",
            "24.00 15.00 18.15 23.85 11.40 7.60",
            "21.00 15.00 19.15 23.85 12.60 8.40",
            "23.00 12.50 17.15 23.85 14.10 9.40",
            "35.00 15.50 20.00 29.50 - -",
        ),
    },
    2033: {  # a partir de 2033
        # Anexo XVIII (Anexo I) - Comércio
        "I": _partilha(
            "IRPJ CSLL CBS CPP IBS",
            "5.50 3.50 15.50 41.50 34.00",
            "5.50 3.50 15.50 41.50 34.00",
            "5.50 3.50 15.50 42.00 33.50",
            "5.50 3.50 15.50 42.00 33.50",
            "5.50 3.50 15.50 42.00 33.50",
            "13.50 10.00 34.40 42.10 -",
        ),
        # Anexo XIX (Anexo II) - Indústria
        "II": _partilha(
            "IRPJ CSLL CBS CPP IPI IBS",
            "5.50 3.50 14.00 37.50 7.50 32.00",
            "5.50 3.50 14.00 37.50 7.50 32.00",
            "5.50 3.50 14.00 37.50 7.50 32.00",
            "5.50 3.50 14.00 37.50 7.50 32.00",
            "5.50 3.50 14.00 37.50 7.50 32.00",
            "8.50 7.50 25.50 23.50 35.00 -",
        ),
        # Anexo XX (Anexo III), redação da LC 227/2026
        "III": _partilha(
            "IRPJ CSLL CBS CPP IBS",
            "4.00 3.50 15.60 43.40 33.50",
            "4.00 3.50 17.10 43.40 32.00",
            "4.00 3.50 16.60 43.40 32.50",
            "4.00 3.50 16.60 43.40 32.50",
            "4.00 3.50 15.60 43.40 33.50",
            "35.00 15.00 19.50 30.50 -",
        ),
        # Anexo XXI (Anexo IV), redação da LC 227/2026 (CPP fora do DAS)
        "IV": _partilha(
            "IRPJ CSLL CBS IBS",
            "18.80 15.20 21.50 44.50",
            "19.80 15.20 25.00 40.00",
            "20.80 15.20 24.00 40.00",
            "17.80 19.20 23.00 40.00",
            "18.80 19.20 22.00 40.00",
            "53.50 21.50 25.00 -",
        ),
        # Anexo XXII (Anexo V)
        "V": _partilha(
            "IRPJ CSLL CBS CPP IBS",
            "25.00 15.00 17.15 28.85 14.00",
            "23.00 15.00 17.15 27.85 17.00",
            "24.00 15.00 18.15 23.85 19.00",
            "21.00 15.00 19.15 23.85 21.00",
            "23.00 12.50 17.15 23.85 23.50",
            "35.00 15.50 20.00 29.50 -",
        ),
    },
}

# Nota (*) dos Anexos III e IV, de 2029 a 2032: o ISS da 5ª faixa tem um teto
# que cai meio ponto por ano (4,5%, 4%, 3,5% e 3% da receita), e a diferença
# vai aos tributos federais e ao IBS pelos percentuais da nota. Ano: (teto,
# percentuais). De 2033 em diante não há ISS nem nota.
TETO_ISS_DESDE_2029 = {
    2029: (Decimal("0.045"), {
        "III": _partilha("IRPJ CSLL CBS CPP IBS", "5.73 5.01 22.33 62.13 4.80")[0],
        "IV": _partilha("IRPJ CSLL CBS IBS", "29.38 30.00 34.38 6.25")[0],
    }),
    2030: (Decimal("0.040"), {
        "III": _partilha("IRPJ CSLL CBS CPP IBS", "5.46 4.78 21.31 59.29 9.15")[0],
        "IV": _partilha("IRPJ CSLL CBS IBS", "27.65 28.24 32.35 11.76")[0],
    }),
    2031: (Decimal("0.035"), {
        "III": _partilha("IRPJ CSLL CBS CPP IBS", "5.23 4.57 20.38 56.69 13.13")[0],
        "IV": _partilha("IRPJ CSLL CBS IBS", "26.11 26.67 30.56 16.67")[0],
    }),
    2032: (Decimal("0.030"), {
        "III": _partilha("IRPJ CSLL CBS CPP IBS", "5.01 4.38 19.52 54.32 16.77")[0],
        "IV": _partilha("IRPJ CSLL CBS IBS", "24.74 25.26 28.95 21.05")[0],
    }),
}

__all__ = ["PARTILHA_ATE_2026", "TETO_ISS_ATE_2026", "PARTILHA_2027_2028",
           "TETO_ISS_2027_2028", "PARTILHA_DESDE_2029", "TETO_ISS_DESDE_2029"]
