import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Empresa

empresa_bp = Blueprint('empresa', __name__)


def formatar_cnpj(cnpj_raw: str) -> str:
    numeros = re.sub(r'\D', '', cnpj_raw)
    if len(numeros) != 14:
        return cnpj_raw
    return f'{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}'


def validar_cnpj(cnpj: str) -> bool:
    numeros = re.sub(r'\D', '', cnpj)
    if len(numeros) != 14 or numeros == numeros[0] * 14:
        return False

    def calcular_digito(nums, pesos):
        total = sum(int(n) * p for n, p in zip(nums, pesos))
        resto = total % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    d1 = calcular_digito(numeros[:12], pesos1)
    d2 = calcular_digito(numeros[:13], pesos2)

    return int(numeros[12]) == d1 and int(numeros[13]) == d2


@empresa_bp.route('/')
def index():
    empresas = Empresa.query.order_by(Empresa.nome).all()
    return render_template('index.html', empresas=empresas)


@empresa_bp.route('/empresa/nova', methods=['GET', 'POST'])
def nova_empresa():
    if request.method == 'POST':
        cnpj_raw = request.form.get('cnpj', '').strip()
        nome = request.form.get('nome', '').strip()

        if not cnpj_raw or not nome:
            flash('CNPJ e Nome são obrigatórios.', 'erro')
            return render_template('empresa/form.html')

        if not validar_cnpj(cnpj_raw):
            flash('CNPJ inválido. Verifique os dígitos informados.', 'erro')
            return render_template('empresa/form.html', cnpj=cnpj_raw, nome=nome)

        cnpj_formatado = formatar_cnpj(cnpj_raw)

        existente = Empresa.query.filter_by(cnpj=cnpj_formatado).first()
        if existente:
            flash(f'CNPJ {cnpj_formatado} já cadastrado para "{existente.nome}".', 'erro')
            return render_template('empresa/form.html', cnpj=cnpj_raw, nome=nome)

        empresa = Empresa(cnpj=cnpj_formatado, nome=nome)
        db.session.add(empresa)
        db.session.commit()

        flash(f'Empresa "{nome}" cadastrada com sucesso!', 'sucesso')
        return redirect(url_for('empresa.index'))

    return render_template('empresa/form.html')


@empresa_bp.route('/empresa/<int:empresa_id>')
def detalhe_empresa(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    return render_template('empresa/detalhe.html', empresa=empresa)


@empresa_bp.route('/empresa/<int:empresa_id>/excluir', methods=['POST'])
def excluir_empresa(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    nome = empresa.nome
    db.session.delete(empresa)
    db.session.commit()
    flash(f'Empresa "{nome}" excluída.', 'sucesso')
    return redirect(url_for('empresa.index'))
