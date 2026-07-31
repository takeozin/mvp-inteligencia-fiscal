import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configurações
    app.secret_key = os.getenv('APP_SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fiscal_mvp.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurar pastas absolutas baseadas na raiz do projeto (ou /tmp se estiver na Vercel)
    if os.getenv('VERCEL') == '1':
        base_dir = '/tmp'
    else:
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, os.getenv('UPLOAD_FOLDER', 'uploads/'))
    app.config['RELATORIO_OUTPUT_FOLDER'] = os.path.join(base_dir, os.getenv('RELATORIO_OUTPUT_FOLDER', 'relatorios/'))
    app.config['PARECER_OUTPUT_FOLDER'] = os.path.join(base_dir, 'pareceres/')
    
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    # Garante que as pastas necessárias existam
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RELATORIO_OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PARECER_OUTPUT_FOLDER'], exist_ok=True)

    db.init_app(app)

    # Registra blueprints
    from app.routes.empresa import empresa_bp
    from app.routes.sped import sped_bp
    from app.routes.calculo import calculo_bp
    app.register_blueprint(empresa_bp)
    app.register_blueprint(sped_bp)
    app.register_blueprint(calculo_bp)

    # Cria tabelas se não existirem
    with app.app_context():
        db.create_all()

    return app
