from functools import wraps
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from app import db
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)


# ─────────────────────────────────────────────
# Decorator de proteção de rotas
# ─────────────────────────────────────────────

def login_required(f):
    """Redireciona para /login se não houver sessão ativa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Faça login para acessar esta página.', 'erro')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Rotas
# ─────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já estiver logado, vai direto para o sistema
    if 'usuario_id' in session:
        return redirect(url_for('empresa.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email, ativo=True).first()

        if usuario and usuario.check_senha(senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            session['usuario_email'] = usuario.email
            session.permanent = True
            flash(f'Bem-vindo, {usuario.nome}!', 'sucesso')
            return redirect(url_for('empresa.index'))

        flash('E-mail ou senha incorretos.', 'erro')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada com sucesso.', 'sucesso')
    return redirect(url_for('auth.login'))


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Cadastro de novo usuário. Desative esta rota após criar os usuários necessários."""
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmacao = request.form.get('confirmacao', '')

        # Validações básicas
        if not nome or not email or not senha:
            flash('Preencha todos os campos.', 'erro')
        elif senha != confirmacao:
            flash('As senhas não coincidem.', 'erro')
        elif len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'erro')
        elif Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'erro')
        else:
            novo = Usuario(nome=nome, email=email)
            novo.set_senha(senha)
            db.session.add(novo)
            db.session.commit()
            flash(f'Usuário "{nome}" criado com sucesso! Faça login.', 'sucesso')
            return redirect(url_for('auth.login'))

    return render_template('registro.html')
