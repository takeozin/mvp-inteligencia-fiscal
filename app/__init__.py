import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv('APP_SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fiscal_mvp.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads/')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.getenv('RELATORIO_OUTPUT_FOLDER', 'relatorios/'), exist_ok=True)
    os.makedirs('pareceres/', exist_ok=True)

    db.init_app(app)

    from app.routes.empresa import empresa_bp
    from app.routes.sped import sped_bp
    app.register_blueprint(empresa_bp)
    app.register_blueprint(sped_bp)

    with app.app_context():
        db.create_all()

    return app
