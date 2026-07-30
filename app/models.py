from app import db

class Empresa(db.Model):
    __tablename__ = 'empresa'

    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)

    arquivos = db.relationship('ArquivoSPED', backref='empresa', lazy=True)

    def __repr__(self):
        return f'<Empresa {self.cnpj} - {self.nome}>'


class ArquivoSPED(db.Model):
    __tablename__ = 'arquivo_sped'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho = db.Column(db.String(500), nullable=False)
    periodo_apuracao = db.Column(db.String(7))
    processado = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ArquivoSPED {self.nome_arquivo}>'
