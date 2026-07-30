import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Empresa, ArquivoSPED

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
                    if len(campos) > 4:
                        dt_ini = campos[4]  # formato DDMMAAAA
                        if len(dt_ini) == 8:
                            return f'{dt_ini[2:4]}/{dt_ini[4:]}'
                    break
    except Exception:
        pass
    return 'N/D'


@sped_bp.route('/empresa/<int:empresa_id>/upload', methods=['GET', 'POST'])
def upload_sped(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)

    if request.method == 'POST':
        arquivo = request.files.get('arquivo_sped')

        if not arquivo or arquivo.filename == '':
            flash('Nenhum arquivo selecionado.', 'erro')
            return redirect(url_for('sped.upload_sped', empresa_id=empresa_id))

        if not extensao_valida(arquivo.filename):
            flash('Extensão inválida. Envie um arquivo .txt, .sped ou .efd.', 'erro')
            return redirect(url_for('sped.upload_sped', empresa_id=empresa_id))

        nome_original = secure_filename(arquivo.filename)
        nome_unico = f'{uuid.uuid4().hex}_{nome_original}'
        pasta_empresa = os.path.join(current_app.config['UPLOAD_FOLDER'], str(empresa_id))
        os.makedirs(pasta_empresa, exist_ok=True)
        caminho_completo = os.path.join(pasta_empresa, nome_unico)

        arquivo.save(caminho_completo)

        periodo = detectar_periodo(caminho_completo)

        registro = ArquivoSPED(
            empresa_id=empresa_id,
            nome_arquivo=nome_original,
            caminho=caminho_completo,
            periodo_apuracao=periodo,
            processado=False
        )
        db.session.add(registro)
        db.session.commit()

        flash(f'Arquivo "{nome_original}" enviado! Período detectado: {periodo}', 'sucesso')
        return redirect(url_for('empresa.detalhe_empresa', empresa_id=empresa_id))

    return render_template('sped/upload.html', empresa=empresa)


@sped_bp.route('/sped/<int:sped_id>/excluir', methods=['POST'])
def excluir_sped(sped_id):
    sped = ArquivoSPED.query.get_or_404(sped_id)
    empresa_id = sped.empresa_id

    try:
        if os.path.exists(sped.caminho):
            os.remove(sped.caminho)
    except OSError:
        pass

    db.session.delete(sped)
    db.session.commit()

    flash(f'Arquivo "{sped.nome_arquivo}" removido.', 'sucesso')
    return redirect(url_for('empresa.detalhe_empresa', empresa_id=empresa_id))
