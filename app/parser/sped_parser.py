"""
Parser do EFD-Contribuições (SPED PIS/COFINS)
Foco: Extração dos dados necessários para o cálculo do Tema 69 STF
(Exclusão do ICMS da base de cálculo do PIS/COFINS)

Registros lidos:
  |0000| — Identificação da empresa e período
  |C100| — Nota Fiscal (cabeçalho)  → VL_ICMS, VL_PIS, VL_COFINS por NF
  |C170| — Itens da NF              → VL_ICMS, VL_BC_PIS, ALIQ_PIS, VL_BC_COFINS, ALIQ_COFINS
  |C181| — PIS por documento (regime não-cumulativo)
  |C185| — COFINS por documento (regime não-cumulativo)
  |M100| — Consolidação PIS/PASEP por CST
  |M200| — Total PIS/PASEP do período
  |M500| — Consolidação COFINS por CST
  |M600| — Total COFINS do período
"""

import re
from dataclasses import dataclass, field
from typing import Optional


def _decimal(valor: str) -> float:
    """Converte string brasileira (vírgula) para float."""
    if not valor or valor.strip() == '':
        return 0.0
    try:
        return float(valor.strip().replace(',', '.'))
    except ValueError:
        return 0.0


@dataclass
class NotaFiscal:
    num_doc: str
    dt_doc: str
    vl_doc: float
    vl_icms: float
    vl_icms_st: float
    vl_pis: float
    vl_cofins: float
    vl_bc_pis: float = 0.0
    vl_bc_cofins: float = 0.0
    aliq_pis: float = 0.0
    aliq_cofins: float = 0.0


@dataclass
class ResultadoParser:
    cnpj_empresa: str = ''
    nome_empresa: str = ''
    periodo_ini: str = ''
    periodo_fim: str = ''
    regime_tributario: str = ''
    total_notas_saida: int = 0
    receita_bruta_total: float = 0.0
    icms_total_saidas: float = 0.0
    icms_st_total_saidas: float = 0.0
    vl_bc_pis_declarado: float = 0.0
    vl_pis_declarado: float = 0.0
    aliq_pis_media: float = 0.0
    vl_bc_cofins_declarado: float = 0.0
    vl_cofins_declarado: float = 0.0
    aliq_cofins_media: float = 0.0
    m_vl_bc_pis: float = 0.0
    m_vl_pis_apurado: float = 0.0
    m_vl_bc_cofins: float = 0.0
    m_vl_cofins_apurado: float = 0.0
    notas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)


class SpedParser:
    SITUACOES_VALIDAS = {'00', '01', '06', '07', '08'}

    def __init__(self, caminho_arquivo: str):
        self.caminho = caminho_arquivo
        self.resultado = ResultadoParser()
        self._nota_corrente: Optional[NotaFiscal] = None

    def parse(self) -> ResultadoParser:
        try:
            with open(self.caminho, 'r', encoding='utf-8', errors='ignore') as f:
                for linha in f:
                    self._processar_linha(linha.strip())
        except FileNotFoundError:
            self.resultado.avisos.append(f'Arquivo não encontrado: {self.caminho}')
            return self.resultado

        self._fechar_nota_corrente()
        self._calcular_aliquotas_medias()
        return self.resultado

    def _processar_linha(self, linha: str):
        if not linha.startswith('|'):
            return
        campos = linha.split('|')
        if len(campos) < 2:
            return
        tipo = campos[1].strip().upper()
        dispatch = {
            '0000': self._ler_0000,
            'C100': self._ler_c100,
            'C170': self._ler_c170,
            'C181': self._ler_c181,
            'C185': self._ler_c185,
            'M100': self._ler_m100,
            'M200': self._ler_m200,
            'M500': self._ler_m500,
            'M600': self._ler_m600,
        }
        handler = dispatch.get(tipo)
        if handler:
            handler(campos)

    def _ler_0000(self, campos):
        if len(campos) < 8:
            return
        dt_ini = campos[4].strip()
        dt_fim = campos[5].strip()
        self.resultado.nome_empresa = campos[6].strip() if len(campos) > 6 else ''
        self.resultado.cnpj_empresa = campos[7].strip() if len(campos) > 7 else ''
        if len(dt_ini) == 8:
            self.resultado.periodo_ini = f'{dt_ini[:2]}/{dt_ini[2:4]}/{dt_ini[4:]}'
        if len(dt_fim) == 8:
            self.resultado.periodo_fim = f'{dt_fim[:2]}/{dt_fim[2:4]}/{dt_fim[4:]}'

    def _ler_c100(self, campos):
        if len(campos) < 20:
            return
        self._fechar_nota_corrente()
        ind_oper = campos[2].strip()
        cod_sit  = campos[6].strip()
        if ind_oper != '1' or cod_sit not in self.SITUACOES_VALIDAS:
            self._nota_corrente = None
            return
        self._nota_corrente = NotaFiscal(
            num_doc    = campos[8].strip() if len(campos) > 8 else '',
            dt_doc     = campos[10].strip() if len(campos) > 10 else '',
            vl_doc     = _decimal(campos[12]) if len(campos) > 12 else 0.0,
            vl_icms    = _decimal(campos[15]) if len(campos) > 15 else 0.0,
            vl_icms_st = _decimal(campos[17]) if len(campos) > 17 else 0.0,
            vl_pis     = _decimal(campos[19]) if len(campos) > 19 else 0.0,
            vl_cofins  = _decimal(campos[20]) if len(campos) > 20 else 0.0,
        )

    def _ler_c170(self, campos):
        if self._nota_corrente is None or len(campos) < 30:
            return
        self._nota_corrente.vl_bc_pis    += _decimal(campos[26]) if len(campos) > 26 else 0.0
        self._nota_corrente.vl_bc_cofins += _decimal(campos[32]) if len(campos) > 32 else 0.0
        if len(campos) > 27 and _decimal(campos[27]) > 0:
            self._nota_corrente.aliq_pis = _decimal(campos[27])
        if len(campos) > 33 and _decimal(campos[33]) > 0:
            self._nota_corrente.aliq_cofins = _decimal(campos[33])

    def _ler_c181(self, campos):
        if len(campos) < 9 or campos[2].strip() != '1':
            return
        self.resultado.vl_bc_pis_declarado += _decimal(campos[5])
        self.resultado.vl_pis_declarado    += _decimal(campos[9]) if len(campos) > 9 else _decimal(campos[8])

    def _ler_c185(self, campos):
        if len(campos) < 9 or campos[2].strip() != '1':
            return
        self.resultado.vl_bc_cofins_declarado += _decimal(campos[5])
        self.resultado.vl_cofins_declarado    += _decimal(campos[9]) if len(campos) > 9 else _decimal(campos[8])

    def _ler_m100(self, campos):
        if len(campos) < 13:
            return
        self.resultado.m_vl_bc_pis      += _decimal(campos[10])
        self.resultado.m_vl_pis_apurado += _decimal(campos[13]) if len(campos) > 13 else _decimal(campos[12])

    def _ler_m200(self, campos):
        if len(campos) < 3:
            return
        self.resultado.m_vl_pis_apurado = _decimal(campos[2]) + (_decimal(campos[3]) if len(campos) > 3 else 0)

    def _ler_m500(self, campos):
        if len(campos) < 13:
            return
        self.resultado.m_vl_bc_cofins      += _decimal(campos[10])
        self.resultado.m_vl_cofins_apurado += _decimal(campos[13]) if len(campos) > 13 else _decimal(campos[12])

    def _ler_m600(self, campos):
        if len(campos) < 3:
            return
        self.resultado.m_vl_cofins_apurado = _decimal(campos[2]) + (_decimal(campos[3]) if len(campos) > 3 else 0)

    def _fechar_nota_corrente(self):
        if self._nota_corrente is None:
            return
        n = self._nota_corrente
        self.resultado.total_notas_saida      += 1
        self.resultado.receita_bruta_total    += n.vl_doc
        self.resultado.icms_total_saidas      += n.vl_icms
        self.resultado.icms_st_total_saidas   += n.vl_icms_st
        self.resultado.vl_pis_declarado       += n.vl_pis
        self.resultado.vl_cofins_declarado    += n.vl_cofins
        self.resultado.vl_bc_pis_declarado    += n.vl_bc_pis
        self.resultado.vl_bc_cofins_declarado += n.vl_bc_cofins
        self.resultado.notas.append(n)
        self._nota_corrente = None

    def _calcular_aliquotas_medias(self):
        r = self.resultado
        if r.vl_bc_pis_declarado > 0:
            r.aliq_pis_media = round(r.vl_pis_declarado / r.vl_bc_pis_declarado * 100, 4)
        elif r.m_vl_bc_pis > 0:
            r.aliq_pis_media = round(r.m_vl_pis_apurado / r.m_vl_bc_pis * 100, 4)
        else:
            r.aliq_pis_media = 1.65
            r.avisos.append('Alíquota PIS não encontrada; usando 1,65% como referência.')

        if r.vl_bc_cofins_declarado > 0:
            r.aliq_cofins_media = round(r.vl_cofins_declarado / r.vl_bc_cofins_declarado * 100, 4)
        elif r.m_vl_bc_cofins > 0:
            r.aliq_cofins_media = round(r.m_vl_cofins_apurado / r.m_vl_bc_cofins * 100, 4)
        else:
            r.aliq_cofins_media = 7.6
            r.avisos.append('Alíquota COFINS não encontrada; usando 7,60% como referência.')
