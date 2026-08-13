"""
Script para criar o primeiro usuário administrador.

Uso:
    python seed_user.py

Execute na raiz do projeto com o ambiente virtual ativado.
"""

import getpass
from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    print("\n=== Criar Usuário — MVP Inteligência Fiscal ===\n")

    nome  = input("Nome completo: ").strip()
    email = input("E-mail: ").strip().lower()

    # Verifica duplicidade
    existente = Usuario.query.filter_by(email=email).first()
    if existente:
        print(f"\n⚠  Já existe um usuário com o e-mail '{email}'.")
        print(f"   Nome: {existente.nome} | Ativo: {existente.ativo}")
        sair = input("Deseja redefinir a senha deste usuário? (s/N): ").strip().lower()
        if sair == 's':
            senha = getpass.getpass("Nova senha (mín. 6 caracteres): ")
            if len(senha) < 6:
                print("❌ Senha muito curta. Cancelado.")
            else:
                existente.set_senha(senha)
                existente.ativo = True
                db.session.commit()
                print(f"\n✅ Senha do usuário '{existente.nome}' atualizada com sucesso!\n")
        else:
            print("Cancelado.")
    else:
        senha = getpass.getpass("Senha (mín. 6 caracteres): ")
        confirmacao = getpass.getpass("Confirmar senha: ")

        if len(senha) < 6:
            print("\n❌ Senha muito curta. Mínimo 6 caracteres.")
        elif senha != confirmacao:
            print("\n❌ As senhas não coincidem.")
        else:
            usuario = Usuario(nome=nome, email=email)
            usuario.set_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            print(f"\n✅ Usuário '{nome}' ({email}) criado com sucesso!")
            print(f"   Faça login em: http://localhost:5000/login\n")
