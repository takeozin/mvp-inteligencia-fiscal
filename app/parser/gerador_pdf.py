"""
Gerador de Relatório PDF — Tema 69 STF
Utiliza ReportLab para montar o relatório de recuperação tributária.
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


# ─── Cores ───────────────────────────────────────────────────────────────────
VERDE_ESCURO  = colors.HexColor('#1b5e20')
VERDE_MEDIO   = colors.HexColor('#2e7d32')
VERDE_CLARO   = colors.HexColor('#e8f5e9')
CINZA_HEADER  = colors.HexColor('#455a64')
CINZA_LINHA   = colors.HexColor('#eceff1')
BRANCO        = colors.white
PRETO         = colors.black
VERMELHO_ICMS = colors.HexColor('#c62828')


def _moeda(valor) -> str:
    """Formata float/Decimal como R$ 1.234,56"""
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        v = 0.0
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _pct(valor) -> str:
    try:
        return f'{float(valor or 0):.4f}%'
    except (TypeError, ValueError):
        return '0,0000%'


def gerar_relatorio_pdf(sped, parser, calculo, pasta_saida: str) -> str:
    """
    Gera o relatório em PDF e retorna o caminho completo do arquivo gerado.

    Args:
        sped:        objeto ArquivoSPED
        parser:      objeto ResultadoParser
        calculo:     objeto ResultadoCalculo
        pasta_saida: diretório onde salvar o PDF

    Returns:
        Caminho absoluto do arquivo PDF gerado.
    """
    os.makedirs(pasta_saida, exist_ok=True)
    nome_arquivo = (
        f'relatorio_tema69_{sped.empresa_id}_{sped.id}_'
        f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )
    caminho = os.path.join(pasta_saida, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title='Relatório Tema 69 STF',
        author='MVP Inteligência Fiscal',
    )

    estilos = getSampleStyleSheet()
    story = []

    # ── Estilos personalizados ────────────────────────────────────────────────
    titulo_doc = ParagraphStyle(
        'TituloDoc', parent=estilos['Title'],
        fontSize=16, textColor=VERDE_ESCURO, spaceAfter=4,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
    )
    subtitulo_doc = ParagraphStyle(
        'SubTituloDoc', parent=estilos['Normal'],
        fontSize=11, textColor=CINZA_HEADER, spaceAfter=2,
        alignment=TA_CENTER,
    )
    secao = ParagraphStyle(
        'Secao', parent=estilos['Normal'],
        fontSize=11, textColor=VERDE_ESCURO, fontName='Helvetica-Bold',
        spaceBefore=14, spaceAfter=4,
    )
    normal = ParagraphStyle(
        'NormalCustom', parent=estilos['Normal'],
        fontSize=9, leading=13,
    )
    normal_c = ParagraphStyle(
        'NormalC', parent=normal, alignment=TA_CENTER,
    )
    normal_d = ParagraphStyle(
        'NormalD', parent=normal, alignment=TA_RIGHT,
    )
    nota_rodape = ParagraphStyle(
        'Nota', parent=normal,
        fontSize=8, textColor=colors.gray, leading=11,
    )
    destaque_bold = ParagraphStyle(
        'DestaqueBold', parent=normal,
        fontName='Helvetica-Bold',
    )
    label_credito = ParagraphStyle(
        'LabelCredito', parent=estilos['Normal'],
        fontSize=10, textColor=VERDE_MEDIO, fontName='Helvetica-Bold',
        alignment=TA_CENTER,
    )
    valor_credito = ParagraphStyle(
        'ValorCredito', parent=estilos['Normal'],
        fontSize=22, textColor=VERDE_ESCURO, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=2,
    )
    pct_estilo = ParagraphStyle(
        'PctEstilo', parent=estilos['Normal'],
        fontSize=18, textColor=VERDE_MEDIO, fontName='Helvetica-Bold',
        alignment=TA_CENTER,
    )

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    story.append(Paragraph('RELATÓRIO DE RECUPERAÇÃO TRIBUTÁRIA', titulo_doc))
    story.append(Paragraph('Exclusão do ICMS da Base do PIS e COFINS', subtitulo_doc))
    story.append(Paragraph(
        'Fundamento: RE 574.706 (STF) — Tema 69 — Modulação: ADC 18',
        subtitulo_doc
    ))
    story.append(HRFlowable(width='100%', thickness=2, color=VERDE_ESCURO, spaceAfter=10))

    # ── 1. Identificação ─────────────────────────────────────────────────────
    story.append(Paragraph('1. Identificação da Empresa e Período', secao))
    dados_id = [
        ['Empresa:', parser.nome_empresa or sped.empresa.nome],
        ['CNPJ:', parser.cnpj_empresa or sped.empresa.cnpj],
        ['Período de Apuração:', f'{parser.periodo_ini} a {parser.periodo_fim}'],
        ['Regime de Tributação:', calculo.regime_calculo or '—'],
        ['Arquivo SPED Analisado:', sped.nome_arquivo],
        ['Data de Emissão do Relatório:', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]
    t_id = Table(dados_id, colWidths=[5 * cm, 11 * cm])
    t_id.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [CINZA_LINHA, BRANCO]),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_id)

    # ── 2. Dados Extraídos do SPED ───────────────────────────────────────────
    story.append(Paragraph('2. Dados Extraídos das Notas Fiscais de Saída', secao))
    dados_nf = [
        ['Descrição', 'Valor'],
        ['Total de NFs de Saída Analisadas', str(parser.total_notas_saida or 0)],
        ['Receita Bruta Total', _moeda(parser.receita_bruta_total)],
        ['ICMS Destacado nas NFs de Saída', _moeda(parser.icms_total_saidas)],
        ['ICMS-ST nas NFs de Saída (informativo)', _moeda(parser.icms_st_total_saidas)],
    ]
    t_nf = Table(dados_nf, colWidths=[11 * cm, 5 * cm])
    t_nf.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0), CINZA_HEADER),
        ('TEXTCOLOR',   (0, 0), (-1, 0), BRANCO),
        ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CINZA_LINHA, BRANCO]),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('ALIGN',       (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        # Destaque linha ICMS
        ('TEXTCOLOR',   (1, 3), (1, 3), VERMELHO_ICMS),
        ('FONTNAME',    (1, 3), (1, 3), 'Helvetica-Bold'),
    ]))
    story.append(t_nf)

    # ── 3. PIS e COFINS Declarados ───────────────────────────────────────────
    story.append(Paragraph('3. PIS e COFINS Conforme Declarado', secao))
    dados_dec = [
        ['Tributo', 'Base de Cálculo', 'Alíquota', 'Valor Pago'],
        ['PIS',
         _moeda(calculo.vl_bc_pis_declarado),
         _pct(calculo.aliq_pis),
         _moeda(calculo.vl_pis_declarado)],
        ['COFINS',
         _moeda(calculo.vl_bc_cofins_declarado),
         _pct(calculo.aliq_cofins),
         _moeda(calculo.vl_cofins_declarado)],
        ['TOTAL',
         _moeda(float(calculo.vl_bc_pis_declarado or 0) + float(calculo.vl_bc_cofins_declarado or 0)),
         '—',
         _moeda(float(calculo.vl_pis_declarado or 0) + float(calculo.vl_cofins_declarado or 0))],
    ]
    t_dec = Table(dados_dec, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
    t_dec.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0), CINZA_HEADER),
        ('TEXTCOLOR',   (0, 0), (-1, 0), BRANCO),
        ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',    (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [CINZA_LINHA, BRANCO]),
        ('BACKGROUND',  (0, -1), (-1, -1), colors.HexColor('#cfd8dc')),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('ALIGN',       (1, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_dec)

    # ── 4. Cálculo Corrigido (Tema 69) ───────────────────────────────────────
    story.append(Paragraph('4. Recálculo com Exclusão do ICMS (Tema 69)', secao))
    dados_corr = [
        ['', 'PIS', 'COFINS'],
        ['Base Declarada',
         _moeda(calculo.vl_bc_pis_declarado),
         _moeda(calculo.vl_bc_cofins_declarado)],
        ['(−) ICMS Excluído',
         _moeda(float(calculo.vl_bc_pis_declarado or 0) - float(calculo.vl_bc_pis_corrigido or 0)),
         _moeda(float(calculo.vl_bc_cofins_declarado or 0) - float(calculo.vl_bc_cofins_corrigido or 0))],
        ['Base Corrigida',
         _moeda(calculo.vl_bc_pis_corrigido),
         _moeda(calculo.vl_bc_cofins_corrigido)],
        ['Tributo Devido (correto)',
         _moeda(calculo.vl_pis_corrigido),
         _moeda(calculo.vl_cofins_corrigido)],
        ['Tributo Pago (declarado)',
         _moeda(calculo.vl_pis_declarado),
         _moeda(calculo.vl_cofins_declarado)],
        ['CRÉDITO APURADO',
         _moeda(calculo.credito_pis),
         _moeda(calculo.credito_cofins)],
    ]
    t_corr = Table(dados_corr, colWidths=[6 * cm, 5 * cm, 5 * cm])
    t_corr.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0), CINZA_HEADER),
        ('TEXTCOLOR',   (0, 0), (-1, 0), BRANCO),
        ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',    (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [CINZA_LINHA, BRANCO]),
        ('BACKGROUND',  (0, -1), (-1, -1), VERDE_CLARO),
        ('TEXTCOLOR',   (0, -1), (-1, -1), VERDE_ESCURO),
        ('FONTNAME',    (0, 2), (0, 2), 'Helvetica-Bold'),
        ('TEXTCOLOR',   (1, 2), (-1, 2), VERMELHO_ICMS),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('ALIGN',       (1, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_corr)

    # ── 5. Crédito Total (destaque) ──────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    cred_pct = float(calculo.percentual_recuperacao or 0)
    cred_total = float(calculo.credito_total or 0)

    box_data = [
        [
            Paragraph('CRÉDITO TOTAL APURADO (Tema 69)', label_credito),
            Paragraph('% sobre o total pago', label_credito),
        ],
        [
            Paragraph(_moeda(cred_total), valor_credito),
            Paragraph(f'{cred_pct:.2f}%', pct_estilo),
        ],
        [
            Paragraph(
                f'Crédito PIS: {_moeda(calculo.credito_pis)}  +  '
                f'Crédito COFINS: {_moeda(calculo.credito_cofins)}',
                normal_c
            ),
            Paragraph(' ', normal),
        ],
    ]
    t_box = Table(box_data, colWidths=[10 * cm, 6 * cm])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), VERDE_CLARO),
        ('BOX',        (0, 0), (-1, -1), 2, VERDE_MEDIO),
        ('INNERGRID',  (0, 0), (-1, -1), 0.5, VERDE_MEDIO),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('SPAN',      (0, 2), (1, 2)),
    ]))
    story.append(KeepTogether([t_box]))

    # ── 6. Avisos ─────────────────────────────────────────────────────────────
    avisos_texto = (calculo.avisos or '').strip()
    if avisos_texto:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph('⚠ Observações e Avisos', secao))
        for aviso in avisos_texto.split('\n'):
            if aviso.strip():
                story.append(Paragraph(f'• {aviso.strip()}', normal))

    # ── 7. Nota de Rodapé ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey, spaceAfter=6))
    story.append(Paragraph(
        'Este relatório foi gerado automaticamente pelo sistema MVP Inteligência Fiscal com base nos '
        'dados constantes do arquivo SPED EFD-Contribuições informado pela empresa. Os valores '
        'apresentados têm caráter estimativo e devem ser validados por profissional habilitado '
        'antes de qualquer ação administrativa ou judicial.<br/>'
        'Fundamento legal: RE 574.706 (Tema 69 STF) — Trânsito em julgado em 15/03/2017 — '
        'Modulação: ADC 18 (créditos exigíveis a partir de 15/03/2017 ressalvadas ações judiciais '
        'e administrativas anteriores).',
        nota_rodape
    ))
    story.append(Paragraph(
        f'Emitido em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle('EmissaoStyle', parent=nota_rodape, alignment=TA_RIGHT, spaceBefore=4)
    ))

    doc.build(story)
    return caminho
