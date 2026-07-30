"""
Motor de Cálculo — Tema 69 STF
RE 574.706: Exclusão do ICMS da base de cálculo do PIS/COFINS
"""
from dataclasses import dataclass

@dataclass
class ResultadoCalculo:
    receita_bruta_total: float
    icms_destacado: float
    icms_st: float
    vl_bc_pis_declarado: float
    aliq_pis: float
    vl_pis_declarado: float
    vl_bc_cofins_declarado: float
    aliq_cofins: float
    vl_cofins_declarado: float
    vl_bc_pis_corrigido: float = 0.0
    vl_pis_corrigido: float = 0.0
    credito_pis: float = 0.0
    vl_bc_cofins_corrigido: float = 0.0
    vl_cofins_corrigido: float = 0.0
    credito_cofins: float = 0.0
    credito_total: float = 0.0
    percentual_recuperacao: float = 0.0
    regime_calculo: str = ''
    avisos: list = None

    def __post_init__(self):
        if self.avisos is None:
            self.avisos = []


def calcular_tema_69(receita_bruta_total, icms_destacado, icms_st,
                     vl_bc_pis, aliq_pis, vl_pis_declarado,
                     vl_bc_cofins, aliq_cofins, vl_cofins_declarado):
    avisos = []
    aliq_pis_dec    = aliq_pis / 100
    aliq_cofins_dec = aliq_cofins / 100

    icms_excluir_pis    = min(icms_destacado, vl_bc_pis)
    icms_excluir_cofins = min(icms_destacado, vl_bc_cofins)

    vl_bc_pis_corrigido    = max(0.0, vl_bc_pis    - icms_excluir_pis)
    vl_bc_cofins_corrigido = max(0.0, vl_bc_cofins - icms_excluir_cofins)

    vl_pis_corrigido    = round(vl_bc_pis_corrigido    * aliq_pis_dec, 2)
    vl_cofins_corrigido = round(vl_bc_cofins_corrigido * aliq_cofins_dec, 2)

    credito_pis    = max(0.0, round(vl_pis_declarado    - vl_pis_corrigido, 2))
    credito_cofins = max(0.0, round(vl_cofins_declarado - vl_cofins_corrigido, 2))
    credito_total  = round(credito_pis + credito_cofins, 2)

    total_pago = vl_pis_declarado + vl_cofins_declarado
    percentual = round(credito_total / total_pago * 100, 2) if total_pago > 0 else 0.0

    if abs(aliq_pis - 0.65) < 0.01:
        regime = 'Cumulativo (Lucro Presumido/Simples)'
    elif abs(aliq_pis - 1.65) < 0.01:
        regime = 'Não-Cumulativo (Lucro Real)'
    else:
        regime = f'Misto/Específico (PIS {aliq_pis:.2f}% / COFINS {aliq_cofins:.2f}%)'

    if vl_pis_declarado == 0 and vl_cofins_declarado == 0:
        avisos.append('Atenção: PIS e COFINS declarados são zero. Verifique os registros C100.')

    return ResultadoCalculo(
        receita_bruta_total=round(receita_bruta_total, 2),
        icms_destacado=round(icms_destacado, 2),
        icms_st=round(icms_st, 2),
        vl_bc_pis_declarado=round(vl_bc_pis, 2),
        aliq_pis=aliq_pis,
        vl_pis_declarado=round(vl_pis_declarado, 2),
        vl_bc_cofins_declarado=round(vl_bc_cofins, 2),
        aliq_cofins=aliq_cofins,
        vl_cofins_declarado=round(vl_cofins_declarado, 2),
        vl_bc_pis_corrigido=round(vl_bc_pis_corrigido, 2),
        vl_pis_corrigido=vl_pis_corrigido,
        credito_pis=credito_pis,
        vl_bc_cofins_corrigido=round(vl_bc_cofins_corrigido, 2),
        vl_cofins_corrigido=vl_cofins_corrigido,
        credito_cofins=credito_cofins,
        credito_total=credito_total,
        percentual_recuperacao=percentual,
        regime_calculo=regime,
        avisos=avisos,
    )
