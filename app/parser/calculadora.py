"""
Motor de Cálculo — Tema 69 STF
RE 574.706: Exclusão do ICMS da base de cálculo do PIS/COFINS

Fundamento legal:
  O STF fixou a tese de que o ICMS não compõe a base de cálculo do
  PIS e da COFINS, pois não representa receita ou faturamento da empresa,
  mas sim montante destinado aos cofres públicos estaduais.

Metodologia de cálculo (conforme orientação do STF e Receita Federal):
  1. Base corrigida PIS    = Base declarada PIS    - ICMS destacado nas NFs
  2. Base corrigida COFINS = Base declarada COFINS - ICMS destacado nas NFs
  3. PIS  correto  = Base corrigida PIS    × alíquota PIS
  4. COFINS correto = Base corrigida COFINS × alíquota COFINS
  5. Crédito PIS    = PIS declarado  - PIS correto
  6. Crédito COFINS = COFINS declarado - COFINS correto
  7. Crédito Total  = Crédito PIS + Crédito COFINS

Nota: o ICMS a ser excluído é o ICMS destacado nas notas de SAÍDA
(receita bruta), não o ICMS-ST, que tem tratamento diferenciado.
"""

from dataclasses import dataclass


@dataclass
class ResultadoCalculo:
    """Resultado completo do cálculo do Tema 69."""

    # Dados de entrada (espelhados do parser)
    receita_bruta_total: float
    icms_destacado: float         # ICMS a ser excluído da base
    icms_st: float                # ICMS-ST (informativo)

    # PIS — conforme declarado
    vl_bc_pis_declarado: float
    aliq_pis: float
    vl_pis_declarado: float

    # COFINS — conforme declarado
    vl_bc_cofins_declarado: float
    aliq_cofins: float
    vl_cofins_declarado: float

    # PIS — após exclusão do ICMS (calculado)
    vl_bc_pis_corrigido: float = 0.0
    vl_pis_corrigido: float = 0.0
    credito_pis: float = 0.0

    # COFINS — após exclusão do ICMS (calculado)
    vl_bc_cofins_corrigido: float = 0.0
    vl_cofins_corrigido: float = 0.0
    credito_cofins: float = 0.0

    # Totais
    credito_total: float = 0.0
    percentual_recuperacao: float = 0.0   # % do crédito sobre o total pago

    # Indicadores qualitativos
    regime_calculo: str = ''     # 'cumulative' | 'non_cumulative' | 'mixed'
    avisos: list = None

    def __post_init__(self):
        if self.avisos is None:
            self.avisos = []


def calcular_tema_69(
    receita_bruta_total: float,
    icms_destacado: float,
    icms_st: float,
    vl_bc_pis: float,
    aliq_pis: float,
    vl_pis_declarado: float,
    vl_bc_cofins: float,
    aliq_cofins: float,
    vl_cofins_declarado: float,
) -> ResultadoCalculo:
    """
    Executa o cálculo do crédito tributário pelo Tema 69.

    Args:
        receita_bruta_total: Receita bruta total do período (R$)
        icms_destacado: ICMS destacado nas NFs de saída (R$) — valor a excluir
        icms_st: ICMS-ST das NFs (R$) — informativo, não entra no cálculo principal
        vl_bc_pis: Base de cálculo do PIS conforme declarado (R$)
        aliq_pis: Alíquota PIS em percentual (ex: 1.65 para 1,65%)
        vl_pis_declarado: PIS pago conforme apuração original (R$)
        vl_bc_cofins: Base de cálculo do COFINS conforme declarado (R$)
        aliq_cofins: Alíquota COFINS em percentual (ex: 7.60 para 7,60%)
        vl_cofins_declarado: COFINS pago conforme apuração original (R$)

    Returns:
        ResultadoCalculo com todos os valores originais e corrigidos.
    """
    avisos = []
    aliq_pis_dec    = aliq_pis / 100
    aliq_cofins_dec = aliq_cofins / 100

    # ------------------------------------------------------------------ #
    # Determina o ICMS a ser efetivamente excluído                        #
    # ------------------------------------------------------------------ #
    # O ICMS a excluir não pode ser maior que a base declarada
    icms_excluir_pis    = min(icms_destacado, vl_bc_pis)
    icms_excluir_cofins = min(icms_destacado, vl_bc_cofins)

    if icms_destacado > vl_bc_pis:
        avisos.append(
            f'ICMS destacado (R$ {icms_destacado:,.2f}) é maior que a base PIS '
            f'(R$ {vl_bc_pis:,.2f}). Usando a base como limite para PIS.'
        )
    if icms_destacado > vl_bc_cofins:
        avisos.append(
            f'ICMS destacado (R$ {icms_destacado:,.2f}) é maior que a base COFINS '
            f'(R$ {vl_bc_cofins:,.2f}). Usando a base como limite para COFINS.'
        )

    # ------------------------------------------------------------------ #
    # Bases corrigidas (após exclusão do ICMS)                            #
    # ------------------------------------------------------------------ #
    vl_bc_pis_corrigido    = max(0.0, vl_bc_pis    - icms_excluir_pis)
    vl_bc_cofins_corrigido = max(0.0, vl_bc_cofins - icms_excluir_cofins)

    # ------------------------------------------------------------------ #
    # Tributos recalculados sobre a base corrigida                        #
    # ------------------------------------------------------------------ #
    vl_pis_corrigido    = round(vl_bc_pis_corrigido    * aliq_pis_dec, 2)
    vl_cofins_corrigido = round(vl_bc_cofins_corrigido * aliq_cofins_dec, 2)

    # ------------------------------------------------------------------ #
    # Créditos apurados                                                   #
    # ------------------------------------------------------------------ #
    credito_pis    = max(0.0, round(vl_pis_declarado    - vl_pis_corrigido, 2))
    credito_cofins = max(0.0, round(vl_cofins_declarado - vl_cofins_corrigido, 2))
    credito_total  = round(credito_pis + credito_cofins, 2)

    # Também pode ser calculado diretamente:
    # credito_pis    ≈ icms_excluir_pis    × aliq_pis_dec
    # credito_cofins ≈ icms_excluir_cofins × aliq_cofins_dec

    # ------------------------------------------------------------------ #
    # Percentual de recuperação                                           #
    # ------------------------------------------------------------------ #
    total_pago = vl_pis_declarado + vl_cofins_declarado
    percentual = round(credito_total / total_pago * 100, 2) if total_pago > 0 else 0.0

    # ------------------------------------------------------------------ #
    # Identifica regime de tributação pela alíquota                       #
    # ------------------------------------------------------------------ #
    if abs(aliq_pis - 0.65) < 0.01 and abs(aliq_cofins - 3.0) < 0.01:
        regime = 'Cumulativo (Lucro Presumido/Simples)'
    elif abs(aliq_pis - 1.65) < 0.01 and abs(aliq_cofins - 7.6) < 0.01:
        regime = 'Não-Cumulativo (Lucro Real)'
    else:
        regime = f'Misto/Específico (PIS {aliq_pis:.2f}% / COFINS {aliq_cofins:.2f}%)'

    if vl_pis_declarado == 0 and vl_cofins_declarado == 0:
        avisos.append(
            'Atenção: valores de PIS e COFINS declarados são zero. '
            'O crédito apurado será zero. Verifique se o arquivo SPED '
            'contém registros C100 (saídas) com os campos VL_PIS e VL_COFINS preenchidos.'
        )

    return ResultadoCalculo(
        receita_bruta_total     = round(receita_bruta_total, 2),
        icms_destacado          = round(icms_destacado, 2),
        icms_st                 = round(icms_st, 2),
        vl_bc_pis_declarado     = round(vl_bc_pis, 2),
        aliq_pis                = aliq_pis,
        vl_pis_declarado        = round(vl_pis_declarado, 2),
        vl_bc_cofins_declarado  = round(vl_bc_cofins, 2),
        aliq_cofins             = aliq_cofins,
        vl_cofins_declarado     = round(vl_cofins_declarado, 2),
        vl_bc_pis_corrigido     = round(vl_bc_pis_corrigido, 2),
        vl_pis_corrigido        = vl_pis_corrigido,
        credito_pis             = credito_pis,
        vl_bc_cofins_corrigido  = round(vl_bc_cofins_corrigido, 2),
        vl_cofins_corrigido     = vl_cofins_corrigido,
        credito_cofins          = credito_cofins,
        credito_total           = credito_total,
        percentual_recuperacao  = percentual,
        regime_calculo          = regime,
        avisos                  = avisos,
    )
