from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models import ArquivoSPED, ResultadoParser, ResultadoCalculo
from app.parser.calculadora import calcular_tema_69

calculo_bp = Blueprint('calculo', __name__)


@calculo_bp.route('/sped/<int:sped_id>/calcular', methods=['POST'])
def calcular(sped_id):
    sped = ArquivoSPED.query.get_or_404(sped_id)
    parser = ResultadoParser.query.filter_by(arquivo_id=sped_id).first()
    if not parser:
        flash('Arquivo ainda não foi processado.', 'erro')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=sped.empresa_id))
    try:
        resultado = calcular_tema_69(
            receita_bruta_total=float(parser.receita_bruta_total or 0),
            icms_destacado=float(parser.icms_total_saidas or 0),
            icms_st=float(parser.icms_st_total_saidas or 0),
            vl_bc_pis=float(parser.vl_bc_pis_declarado or 0),
            aliq_pis=float(parser.aliq_pis_media or 1.65),
            vl_pis_declarado=float(parser.vl_pis_declarado or 0),
            vl_bc_cofins=float(parser.vl_bc_cofins_declarado or 0),
            aliq_cofins=float(parser.aliq_cofins_media or 7.6),
            vl_cofins_declarado=float(parser.vl_cofins_declarado or 0),
        )
        anterior = ResultadoCalculo.query.filter_by(arquivo_id=sped_id).first()
        if anterior:
            db.session.delete(anterior)
            db.session.flush()
        calculo = ResultadoCalculo(
            arquivo_id=sped_id, regime_calculo=resultado.regime_calculo,
            receita_bruta_total=resultado.receita_bruta_total,
            icms_destacado=resultado.icms_destacado, icms_st=resultado.icms_st,
            aliq_pis=resultado.aliq_pis,
            vl_bc_pis_declarado=resultado.vl_bc_pis_declarado,
            vl_pis_declarado=resultado.vl_pis_declarado,
            vl_bc_pis_corrigido=resultado.vl_bc_pis_corrigido,
            vl_pis_corrigido=resultado.vl_pis_corrigido,
            credito_pis=resultado.credito_pis,
            aliq_cofins=resultado.aliq_cofins,
            vl_bc_cofins_declarado=resultado.vl_bc_cofins_declarado,
            vl_cofins_declarado=resultado.vl_cofins_declarado,
            vl_bc_cofins_corrigido=resultado.vl_bc_cofins_corrigido,
            vl_cofins_corrigido=resultado.vl_cofins_corrigido,
            credito_cofins=resultado.credito_cofins,
            credito_total=resultado.credito_total,
            percentual_recuperacao=resultado.percentual_recuperacao,
            avisos='\n'.join(resultado.avisos),
        )
        db.session.add(calculo)
        db.session.commit()
        flash(f'Cálculo concluído! Crédito: R$ {resultado.credito_total:,.2f}', 'sucesso')
        return redirect(url_for('calculo.ver_calculo', sped_id=sped_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro no cálculo: {str(e)}', 'erro')
        return redirect(url_for('sped.resultado_sped', sped_id=sped_id))


@calculo_bp.route('/sped/<int:sped_id>/calculo')
def ver_calculo(sped_id):
    sped = ArquivoSPED.query.get_or_404(sped_id)
    parser = ResultadoParser.query.filter_by(arquivo_id=sped_id).first_or_404()
    c = ResultadoCalculo.query.filter_by(arquivo_id=sped_id).first_or_404()
    return render_template('calculo/resultado.html', sped=sped, parser=parser, c=c)
