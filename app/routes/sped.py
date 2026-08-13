import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from app import db
from app.models import Empresa, ArquivoSPED, ResultadoParser
from app.parser.sped_parser import SpedParser
from app.routes.auth import login_required, get_empresa_ou_404

sped_bp = Blueprint('sped', __name__)

EXTENSOES_PERMITIDAS = {'.txt', '.sped', '.efd'}


def extensao_valida(nome_arquivo: str) -> bool:
    _, ext = os.path.splitext(nome_arquivo.lower())
    return ext in EXTENSOES_PERMITIDAS


def detectar_periodo(caminho_arquivo: str) -> str:
    """
    Lê as primeiras linhas do arquivo e tenta extrair o período
    do registro |0000| do SPED (campo DT_INI, posição 3).
    Retorna string no formato MM/AAAA ou 'N/D'.
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
            for linha in f:
                linha = linha.strip()
                if linha.startswith('|0000|'):
                    campos = linha.split('|')
                    # |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|...
                    # índice: 0=vazio 1=0000 2=COD_VER 3=COD_FIN 4=DT_INI
                    if len(campos) > 4:
                        dt_ini = campos[4]  # formato DDMMAAAA
                        if len(dt_ini) == 8:
                            return f'{dt_ini[2:4]}/{dt_ini[4:]}'
                    break
    except Exception:
        pass
    return 'N/D'


@sped_bp.route('/empresa/<int:empresa_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_sped(empresa_id):
    empresa = get_empresa_ou_404(empresa_id)

    if request.method == 'POST':
        arquivo = request.files.get('arquivo_sped')

        # Validações básicas
        if not arquivo or arquivo.filename == '':
            flash('Nenhum arquivo selecionado.', 'erro')
            return redirect(url_for('sped.upload_sped', empresa_id=empresa_id))

        if not extensao_valida(arquivo.filename):
            flash(
                f'Extensão inválida. Envie um arquivo .txt, .sped ou .efd.',
                'erro'
            )
            return redirect(url_for('sped.upload_sped', empresa_id=empresa_id))

        # Gera nome único para evitar colisão
        nome_original = secure_filename(arquivo.filename)
        nome_unico = f'{uuid.uuid4().hex}_{nome_original}'
        pasta_empresa = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            str(empresa_id)
        )
        os.makedirs(pasta_empresa, exist_ok=True)
        caminho_completo = os.path.join(pasta_empresa, nome_unico)

        arquivo.save(caminho_completo)

        # Detecta o período de apuração lendo o registro |0000|
        periodo = detectar_periodo(caminho_completo)

        # Persiste no banco
        registro = ArquivoSPED(
            empresa_id=empresa_id,
            nome_arquivo=nome_original,
            caminho=caminho_completo,
            periodo_apuracao=periodo,
            processado=False
        )
        db.session.add(registro)
        db.session.commit()

        flash(
            f'Arquivo "{nome_original}" enviado com sucesso! Período detectado: {periodo}',
            'sucesso'
        )
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=empresa_id))

    return render_template('sped/upload.html', empresa=empresa)


@sped_bp.route('/sped/<int:sped_id>/excluir', methods=['POST'])
@login_required
def excluir_sped(sped_id):
    sped = ArquivoSPED.query.get_or_404(sped_id)
    # Valida que a empresa do SPED pertence ao usuário logado
    get_empresa_ou_404(sped.empresa_id)
    empresa_id = sped.empresa_id

    # Remove o arquivo físico
    try:
        if os.path.exists(sped.caminho):
            os.remove(sped.caminho)
    except OSError:
        pass  # segue mesmo se o arquivo não existir

    db.session.delete(sped)
    db.session.commit()

    flash(f'Arquivo "{sped.nome_arquivo}" removido.', 'sucesso')
    return redirect(url_for('empresa.detalhe_empresa', empresa_id=empresa_id))


@sped_bp.route('/sped/<int:sped_id>/processar', methods=['POST'])
@login_required
def processar_sped(sped_id):
    """Executa o parser no arquivo SPED e salva o resultado no banco."""
    sped = ArquivoSPED.query.get_or_404(sped_id)
    # Valida que a empresa do SPED pertence ao usuário logado
    get_empresa_ou_404(sped.empresa_id)

    if not os.path.exists(sped.caminho):
        flash('Arquivo físico não encontrado no servidor.', 'erro')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=sped.empresa_id))

    try:
        parser = SpedParser(sped.caminho)
        dados = parser.parse()

        # Remove resultado anterior, se existir
        resultado_anterior = ResultadoParser.query.filter_by(arquivo_id=sped_id).first()
        if resultado_anterior:
            db.session.delete(resultado_anterior)
            db.session.flush()

        resultado = ResultadoParser(
            arquivo_id              = sped_id,
            nome_empresa            = dados.nome_empresa,
            cnpj_empresa            = dados.cnpj_empresa,
            periodo_ini             = dados.periodo_ini,
            periodo_fim             = dados.periodo_fim,
            total_notas_saida       = dados.total_notas_saida,
            receita_bruta_total     = round(dados.receita_bruta_total, 2),
            icms_total_saidas       = round(dados.icms_total_saidas, 2),
            icms_st_total_saidas    = round(dados.icms_st_total_saidas, 2),
            vl_bc_pis_declarado     = round(dados.vl_bc_pis_declarado, 2),
            vl_pis_declarado        = round(dados.vl_pis_declarado, 2),
            aliq_pis_media          = round(dados.aliq_pis_media, 4),
            vl_bc_cofins_declarado  = round(dados.vl_bc_cofins_declarado, 2),
            vl_cofins_declarado     = round(dados.vl_cofins_declarado, 2),
            aliq_cofins_media       = round(dados.aliq_cofins_media, 4),
            m_vl_bc_pis             = round(dados.m_vl_bc_pis, 2),
            m_vl_pis_apurado        = round(dados.m_vl_pis_apurado, 2),
            m_vl_bc_cofins          = round(dados.m_vl_bc_cofins, 2),
            m_vl_cofins_apurado     = round(dados.m_vl_cofins_apurado, 2),
            avisos                  = '\n'.join(dados.avisos),
        )

        db.session.add(resultado)

        # Marca arquivo como processado
        sped.processado = True
        db.session.commit()

        flash(f'Arquivo "{sped.nome_arquivo}" processado com sucesso! '
              f'{dados.total_notas_saida} notas de saída lidas.', 'sucesso')
        return redirect(url_for('sped.resultado_sped', sped_id=sped_id))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar arquivo: {str(e)}', 'erro')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=sped.empresa_id))


@sped_bp.route('/sped/<int:sped_id>/resultado')
@login_required
def resultado_sped(sped_id):
    """Exibe o resultado da leitura do SPED."""
    sped = ArquivoSPED.query.get_or_404(sped_id)
    # Valida ownership
    get_empresa_ou_404(sped.empresa_id)
    resultado = ResultadoParser.query.filter_by(arquivo_id=sped_id).first_or_404()
    return render_template('sped/resultado.html', sped=sped, r=resultado)
