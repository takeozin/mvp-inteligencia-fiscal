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


class ResultadoParser(db.Model):
    """Armazena o resultado da leitura e extraçãoo de dados de um arquivo SPED."""
    __tablename__ = 'resultado_parser'

    id = db.Column(db.Integer, primary_key=True)
    arquivo_id = db.Column(db.Integer, db.ForeignKey('arquivo_sped.id'), nullable=False, unique=True)

    nome_empresa    = db.Column(db.String(200))
    cnpj_empresa    = db.Column(db.String(18))
    periodo_ini     = db.Column(db.String(10))
    periodo_fim     = db.Column(db.String(10))

    total_notas_saida     = db.Column(db.Integer, default=0)
    receita_bruta_total   = db.Column(db.Numeric(18, 2), default=0)
    icms_total_saidas     = db.Column(db.Numeric(18, 2), default=0)
    icms_st_total_saidas  = db.Column(db.Numeric(18, 2), default=0)

    vl_bc_pis_declarado   = db.Column(db.Numeric(18, 2), default=0)
    vl_pis_declarado      = db.Column(db.Numeric(18, 2), default=0)
    aliq_pis_media        = db.Column(db.Numeric(8, 4), default=0)

    vl_bc_cofins_declarado  = db.Column(db.Numeric(18, 2), default=0)
    vl_cofins_declarado     = db.Column(db.Numeric(18, 2), default=0)
    aliq_cofins_media       = db.Column(db.Numeric(8, 4), default=0)

    m_vl_bc_pis       = db.Column(db.Numeric(18, 2), default=0)
    m_vl_pis_apurado  = db.Column(db.Numeric(18, 2), default=0)
    m_vl_bc_cofins    = db.Column(db.Numeric(18, 2), default=0)
    m_vl_cofins_apurado = db.Column(db.Numeric(18, 2), default=0)

    avisos = db.Column(db.Text, default='')

    arquivo = db.relationship('ArquivoSPED', backref=db.backref('resultado', uselist=False))

    def __repr__(self):
        return f'<ResultadoParser arquivo_id={self.arquivo_id}>'
