"""
Parser do EFD-Contribuições (SPED PIS/COFINS)
Foco: Extração dos dados necessários para o cálculo do Tema 69 STF
(Exclusão do ICMS da base de cálculo do PIS/COFINS)

Registros lidos:
  |0000| — Identificação da empresa e período
  |0150| — Tabela de cadastro do participante
  |C100| — Nota Fiscal (cabeçalho)  → VL_ICMS, VL_PIS, VL_COFINS por NF
  |C170| — Itens da NF              → VL_ICMS, VL_BC_PIS, ALIQ_PIS, VL_BC_COFINS, ALIQ_COFINS por item
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
    """Dados de uma NF de saída relevante para o Tema 69."""
    num_doc: str
    dt_doc: str
    vl_doc: float
    vl_icms: float
    vl_icms_st: float
    vl_pis: float
    vl_cofins: float
    # preenchidos a partir dos itens C170
    vl_bc_pis: float = 0.0
    vl_bc_cofins: float = 0.0
    aliq_pis: float = 0.0
    aliq_cofins: float = 0.0


@dataclass
class ResultadoParser:
    """Resultado completo da leitura de um arquivo SPED."""
    # Identificação
    cnpj_empresa: str = ''
    nome_empresa: str = ''
    periodo_ini: str = ''
    periodo_fim: str = ''
    regime_tributario: str = ''   # 1=Simples, 2=Lucro Presumido, 3=Lucro Real

    # Totais apurados diretamente dos registros
    total_notas_saida: int = 0
    receita_bruta_total: float = 0.0    # soma VL_DOC das NFs de saída válidas

    # ICMS
    icms_total_saidas: float = 0.0      # soma VL_ICMS (C100 saídas)
    icms_st_total_saidas: float = 0.0   # soma VL_ICMS_ST (C100 saídas)

    # PIS — conforme declarado
    vl_bc_pis_declarado: float = 0.0    # base de cálculo original declarada
    vl_pis_declarado: float = 0.0       # PIS pago conforme declarado
    aliq_pis_media: float = 0.0         # alíquota média efetiva PIS

    # COFINS — conforme declarado
    vl_bc_cofins_declarado: float = 0.0
    vl_cofins_declarado: float = 0.0
    aliq_cofins_media: float = 0.0

    # Totais do Bloco M (apuração oficial)
    m_vl_bc_pis: float = 0.0
    m_vl_pis_apurado: float = 0.0
    m_vl_bc_cofins: float = 0.0
    m_vl_cofins_apurado: float = 0.0

    # Lista de notas individuais (para auditoria)
    notas: list = field(default_factory=list)

    # Avisos e alertas do parser
    avisos: list = field(default_factory=list)


class SpedParser:
    """
    Lê um arquivo EFD-Contribuições linha a linha e extrai
    os dados necessários para o cálculo do Tema 69.
    """

    # Situações de NF que indicam documento válido (não cancelado)
    SITUACOES_VALIDAS = {'00', '01', '06', '07', '08'}

    def __init__(self, caminho_arquivo: str):
        self.caminho = caminho_arquivo
        self.resultado = ResultadoParser()
        self._nota_corrente: Optional[NotaFiscal] = None

    # ------------------------------------------------------------------ #
    #  Ponto de entrada                                                    #
    # ------------------------------------------------------------------ #

    def parse(self) -> ResultadoParser:
        """Executa a leitura completa do arquivo e retorna ResultadoParser."""
        try:
            with open(self.caminho, 'r', encoding='utf-8', errors='ignore') as f:
                for linha in f:
                    self._processar_linha(linha.strip())
        except FileNotFoundError:
            self.resultado.avisos.append(f'Arquivo não encontrado: {self.caminho}')
            return self.resultado

        # Fecha a última nota pendente
        self._fechar_nota_corrente()

        # Calcula médias de alíquota
        self._calcular_aliquotas_medias()

        return self.resultado

    # ------------------------------------------------------------------ #
    #  Despachante de linhas                                               #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    #  Registro |0000| — Abertura / Identificação                         #
    # ------------------------------------------------------------------ #

    def _ler_0000(self, campos: list):
        """
        Layout: |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|CPF|SUFRAMA|IND_PERFIL|IND_ATIV|
        Índices:   0     1       2       3      4      5    6    7    8       9          10
        """
        if len(campos) < 8:
            return

        dt_ini = campos[4].strip()   # DDMMAAAA
        dt_fim = campos[5].strip()

        self.resultado.nome_empresa = campos[6].strip() if len(campos) > 6 else ''
        self.resultado.cnpj_empresa = campos[7].strip() if len(campos) > 7 else ''

        if len(dt_ini) == 8:
            self.resultado.periodo_ini = f'{dt_ini[:2]}/{dt_ini[2:4]}/{dt_ini[4:]}'
        if len(dt_fim) == 8:
            self.resultado.periodo_fim = f'{dt_fim[:2]}/{dt_fim[2:4]}/{dt_fim[4:]}'

    # ------------------------------------------------------------------ #
    #  Registro |C100| — Nota Fiscal (cabeçalho)                          #
    # ------------------------------------------------------------------ #

    def _ler_c100(self, campos: list):
        """
        Layout EFD-Contribuições:
        |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|
          0     1        2        3        4        5       6    7       8
        |DT_DOC|DT_A_P|VL_DOC|VL_DESC|VL_BC_ICMS|VL_ICMS|VL_BC_ICMS_ST|VL_ICMS_ST|
           9      10    11      12       13          14       15             16
        |VL_IPI|VL_PIS|VL_COFINS|VL_PIS_ST|VL_COFINS_ST|
           17    18      19        20          21
        """
        if len(campos) < 20:
            return

        # Fecha nota anterior antes de abrir nova
        self._fechar_nota_corrente()

        ind_oper = campos[2].strip()   # 0=Entrada, 1=Saída
        cod_sit  = campos[6].strip()   # situação do documento

        # Para o Tema 69, nos interessa SAÍDAS (1) em situação válida
        if ind_oper != '1' or cod_sit not in self.SITUACOES_VALIDAS:
            self._nota_corrente = None
            return

        self._nota_corrente = NotaFiscal(
            num_doc     = campos[8].strip() if len(campos) > 8 else '',
            dt_doc      = campos[10].strip() if len(campos) > 10 else '',
            vl_doc      = _decimal(campos[12]) if len(campos) > 12 else 0.0,
            vl_icms     = _decimal(campos[15]) if len(campos) > 15 else 0.0,
            vl_icms_st  = _decimal(campos[17]) if len(campos) > 17 else 0.0,
            vl_pis      = _decimal(campos[19]) if len(campos) > 19 else 0.0,
            vl_cofins   = _decimal(campos[20]) if len(campos) > 20 else 0.0,
        )

    # ------------------------------------------------------------------ #
    #  Registro |C170| — Itens da Nota Fiscal                             #
    # ------------------------------------------------------------------ #

    def _ler_c170(self, campos: list):
        """
        Layout (campos relevantes):
        ...CST_PIS|VL_BC_PIS|ALIQ_PIS|QUANT_BC_PIS|ALIQ_PIS_R$|VL_PIS|
              25      26       27        28             29          30
           CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|QUANT_BC_COFINS|ALIQ_COFINS_R$|VL_COFINS|
               31         32          33            34              35             36
        """
        if self._nota_corrente is None:
            return

        if len(campos) < 30:
            return

        vl_bc_pis    = _decimal(campos[26]) if len(campos) > 26 else 0.0
        aliq_pis     = _decimal(campos[27]) if len(campos) > 27 else 0.0
        vl_bc_cofins = _decimal(campos[32]) if len(campos) > 32 else 0.0
        aliq_cofins  = _decimal(campos[33]) if len(campos) > 33 else 0.0

        self._nota_corrente.vl_bc_pis    += vl_bc_pis
        self._nota_corrente.vl_bc_cofins += vl_bc_cofins

        # Guarda a alíquota mais recente (não-nula)
        if aliq_pis > 0:
            self._nota_corrente.aliq_pis = aliq_pis
        if aliq_cofins > 0:
            self._nota_corrente.aliq_cofins = aliq_cofins

    # ------------------------------------------------------------------ #
    #  Registros |C181| e |C185| — PIS/COFINS por Documento               #
    # ------------------------------------------------------------------ #

    def _ler_c181(self, campos: list):
        """
        PIS por documento (regime não-cumulativo).
        |C181|IND_OPER|CST_PIS|CFOP|VL_BC_PIS|ALIQ_PIS|QUANT_BC_PIS|ALIQ_PIS_R$|VL_PIS|COD_CTA|
           0     1       2      3      4          5          6            7           8      9
        """
        if len(campos) < 9:
            return
        ind_oper = campos[2].strip()
        if ind_oper != '1':
            return
        self.resultado.vl_bc_pis_declarado += _decimal(campos[5])
        self.resultado.vl_pis_declarado    += _decimal(campos[9]) if len(campos) > 9 else _decimal(campos[8])

    def _ler_c185(self, campos: list):
        """
        COFINS por documento (regime não-cumulativo).
        Layout análogo ao C181.
        """
        if len(campos) < 9:
            return
        ind_oper = campos[2].strip()
        if ind_oper != '1':
            return
        self.resultado.vl_bc_cofins_declarado += _decimal(campos[5])
        self.resultado.vl_cofins_declarado    += _decimal(campos[9]) if len(campos) > 9 else _decimal(campos[8])

    # ------------------------------------------------------------------ #
    #  Registros do Bloco M — Apuração oficial                            #
    # ------------------------------------------------------------------ #

    def _ler_m100(self, campos: list):
        """
        |M100|COD_CONT|IND_COLUNAS|IND_PERIODO|VL_TOT_REC|VL_REC_CUMULAT|VL_REC_NCUMULAT|
          0     1        2           3            4           5               6
        |VL_REC_MOD_INDIR|VL_REC_EXCCL|VL_BC_CONT|ALIQ_PIS_COFINS|QUANT_BC_PIS_COFINS|VL_CONT_APUR|...
           7                8             9           10               11                   12
        """
        if len(campos) < 13:
            return
        self.resultado.m_vl_bc_pis      += _decimal(campos[10])
        self.resultado.m_vl_pis_apurado += _decimal(campos[13]) if len(campos) > 13 else _decimal(campos[12])

    def _ler_m200(self, campos: list):
        """
        |M200|VL_TOT_CONT_NC_PER|VL_TOT_CONT_CUM_PER|VL_TOT_CONT_NC_ANT|VL_TOT_CONT_CUM_ANT|
          0         1                  2                    3                    4
        |VL_TOT_CONT_NC_DEV|VL_TOT_CONT_CUM_DEV|VL_TOT_CONT_NC_REC|VL_TOT_CONT_CUM_REC|
              5                    6                   7                    8
        |VL_TOT_CONT_NC_RET|VL_TOT_CONT_CUM_RET|VL_TOT_CONT_NC_OBR|VL_TOT_CONT_CUM_OBR|
              9                   10                  11                   12
        |VL_TOT_CONT_CUM_PER_ANT|VL_TOT_REC_PIS|COD_REC|
                   13                  14           15
        """
        if len(campos) < 3:
            return
        # soma contribuição total apurada no período (NC + cumulativo)
        self.resultado.m_vl_pis_apurado = _decimal(campos[2]) + _decimal(campos[3]) if len(campos) > 3 else _decimal(campos[2])

    def _ler_m500(self, campos: list):
        """Análogo ao M100, mas para COFINS."""
        if len(campos) < 13:
            return
        self.resultado.m_vl_bc_cofins      += _decimal(campos[10])
        self.resultado.m_vl_cofins_apurado += _decimal(campos[13]) if len(campos) > 13 else _decimal(campos[12])

    def _ler_m600(self, campos: list):
        """Análogo ao M200, mas para COFINS."""
        if len(campos) < 3:
            return
        self.resultado.m_vl_cofins_apurado = _decimal(campos[2]) + _decimal(campos[3]) if len(campos) > 3 else _decimal(campos[2])

    # ------------------------------------------------------------------ #
    #  Helpers internos                                                    #
    # ------------------------------------------------------------------ #

    def _fechar_nota_corrente(self):
        """Finaliza a nota atual e acumula nos totais gerais."""
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
        """Calcula alíquota efetiva média de PIS e COFINS."""
        r = self.resultado

        # Alíquota média PIS
        if r.vl_bc_pis_declarado > 0:
            r.aliq_pis_media = round(r.vl_pis_declarado / r.vl_bc_pis_declarado * 100, 4)
        elif r.m_vl_bc_pis > 0:
            r.aliq_pis_media = round(r.m_vl_pis_apurado / r.m_vl_bc_pis * 100, 4)
        else:
            # fallback: alíquota mais comum (não-cumulativo padrão)
            r.aliq_pis_media = 1.65
            r.avisos.append(
                'Alíquota PIS não encontrada nos registros C170/M100; '
                'usando 1,65% como referência.'
            )

        # Alíquota média COFINS
        if r.vl_bc_cofins_declarado > 0:
            r.aliq_cofins_media = round(r.vl_cofins_declarado / r.vl_bc_cofins_declarado * 100, 4)
        elif r.m_vl_bc_cofins > 0:
            r.aliq_cofins_media = round(r.m_vl_cofins_apurado / r.m_vl_bc_cofins * 100, 4)
        else:
            r.aliq_cofins_media = 7.6
            r.avisos.append(
                'Alíquota COFINS não encontrada nos registros C170/M100; '
                'usando 7,60% como referência.'
            )
