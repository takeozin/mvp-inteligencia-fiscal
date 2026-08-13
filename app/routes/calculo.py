from flask import Blueprint, render_template, redirect, url_for, flash, send_file, current_app
from app import db
from app.models import ArquivoSPED, ResultadoParser, ResultadoCalculo
from app.parser.calculadora import calcular_tema_69
from app.routes.auth import login_required, get_empresa_ou_404

calculo_bp = Blueprint('calculo', __name__)


@calculo_bp.route('/sped/<int:sped_id>/calcular', methods=['POST'])
@login_required
def calcular(sped_id):
    """Executa o motor de cálculo do Tema 69 sobre o resultado do parser."""
    sped = ArquivoSPED.query.get_or_404(sped_id)
    get_empresa_ou_404(sped.empresa_id)
    parser = ResultadoParser.query.filter_by(arquivo_id=sped_id).first()

    if not parser:
        flash('Arquivo ainda não foi processado. Execute o parser primeiro.', 'erro')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=sped.empresa_id))

    try:
        resultado = calcular_tema_69(
            receita_bruta_total = float(parser.receita_bruta_total or 0),
            icms_destacado      = float(parser.icms_total_saidas or 0),
            icms_st             = float(parser.icms_st_total_saidas or 0),
            vl_bc_pis           = float(parser.vl_bc_pis_declarado or 0),
            aliq_pis            = float(parser.aliq_pis_media or 1.65),
            vl_pis_declarado    = float(parser.vl_pis_declarado or 0),
            vl_bc_cofins        = float(parser.vl_bc_cofins_declarado or 0),
            aliq_cofins         = float(parser.aliq_cofins_media or 7.6),
            vl_cofins_declarado = float(parser.vl_cofins_declarado or 0),
        )

        # Remove cálculo anterior se existir
        anterior = ResultadoCalculo.query.filter_by(arquivo_id=sped_id).first()
        if anterior:
            db.session.delete(anterior)
            db.session.flush()

        calculo = ResultadoCalculo(
            arquivo_id             = sped_id,
            regime_calculo         = resultado.regime_calculo,
            receita_bruta_total    = resultado.receita_bruta_total,
            icms_destacado         = resultado.icms_destacado,
            icms_st                = resultado.icms_st,
            aliq_pis               = resultado.aliq_pis,
            vl_bc_pis_declarado    = resultado.vl_bc_pis_declarado,
            vl_pis_declarado       = resultado.vl_pis_declarado,
            vl_bc_pis_corrigido    = resultado.vl_bc_pis_corrigido,
            vl_pis_corrigido       = resultado.vl_pis_corrigido,
            credito_pis            = resultado.credito_pis,
            aliq_cofins            = resultado.aliq_cofins,
            vl_bc_cofins_declarado = resultado.vl_bc_cofins_declarado,
            vl_cofins_declarado    = resultado.vl_cofins_declarado,
            vl_bc_cofins_corrigido = resultado.vl_bc_cofins_corrigido,
            vl_cofins_corrigido    = resultado.vl_cofins_corrigido,
            credito_cofins         = resultado.credito_cofins,
            credito_total          = resultado.credito_total,
            percentual_recuperacao = resultado.percentual_recuperacao,
            avisos                 = '\n'.join(resultado.avisos),
        )

        db.session.add(calculo)
        db.session.commit()

        flash(
            f'Cálculo concluído! Crédito apurado: R$ {resultado.credito_total:,.2f}',
            'sucesso'
        )
        return redirect(url_for('calculo.ver_calculo', sped_id=sped_id))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro no cálculo: {str(e)}', 'erro')
        return redirect(url_for('sped.resultado_sped', sped_id=sped_id))


@calculo_bp.route('/sped/<int:sped_id>/calculo')
@login_required
def ver_calculo(sped_id):
    """Exibe o resultado do cálculo do Tema 69."""
    sped = ArquivoSPED.query.get_or_404(sped_id)
    get_empresa_ou_404(sped.empresa_id)
    parser = ResultadoParser.query.filter_by(arquivo_id=sped_id).first_or_404()
    c = ResultadoCalculo.query.filter_by(arquivo_id=sped_id).first_or_404()
    return render_template('calculo/resultado.html', sped=sped, parser=parser, c=c)


@calculo_bp.route('/sped/<int:sped_id>/pdf', methods=['POST'])
@login_required
def gerar_pdf(sped_id):
    """Gera o relatório em PDF e envia para download."""
    sped   = ArquivoSPED.query.get_or_404(sped_id)
    get_empresa_ou_404(sped.empresa_id)
    parser = ResultadoParser.query.filter_by(arquivo_id=sped_id).first()
    c      = ResultadoCalculo.query.filter_by(arquivo_id=sped_id).first()

    if not parser or not c:
        flash('Execute o parser e o cálculo antes de gerar o PDF.', 'erro')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=sped.empresa_id))

    try:
        from app.parser.gerador_pdf import gerar_relatorio_pdf
        pasta = current_app.config['RELATORIO_OUTPUT_FOLDER']
        caminho_pdf = gerar_relatorio_pdf(sped, parser, c, pasta)

        nome_download = (
            f'Relatorio_Tema69_{sped.empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")}'
            f'_{sped.id}.pdf'
        )
        return send_file(
            caminho_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nome_download,
        )

    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'erro')
        return redirect(url_for('calculo.ver_calculo', sped_id=sped_id))


@calculo_bp.route('/sped/<int:sped_id>/parecer', methods=['POST'])
@login_required
def gerar_parecer(sped_id):
    """Gera a Minuta de Parecer em Word e envia para download."""
    sped   = ArquivoSPED.query.get_or_404(sped_id)
    get_empresa_ou_404(sped.empresa_id)
    parser = ResultadoParser.query.filter_by(arquivo_id=sped_id).first()
    c      = ResultadoCalculo.query.filter_by(arquivo_id=sped_id).first()

    if not parser or not c:
        flash('Execute o parser e o cálculo antes de gerar o Parecer.', 'erro')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=sped.empresa_id))

    try:
        from app.parser.gerador_parecer import gerar_parecer_docx
        pasta = current_app.config['PARECER_OUTPUT_FOLDER']
        caminho_docx = gerar_parecer_docx(sped, parser, c, pasta)

        nome_download = (
            f'Minuta_Parecer_Tema69_{sped.empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")}'
            f'_{sped.id}.docx'
        )
        return send_file(
            caminho_docx,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=nome_download,
        )

    except Exception as e:
        flash(f'Erro ao gerar Parecer Word: {str(e)}', 'erro')
        return redirect(url_for('calculo.ver_calculo', sped_id=sped_id))
