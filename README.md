# MVP Inteligência Fiscal — Tema 69 STF

Sistema para leitura de arquivos SPED EFD-Contribuições e cálculo de recuperação tributária pela exclusão do ICMS da base de cálculo do PIS/COFINS.

## Stack
- **Backend:** Python 3.12 + Flask
- **Banco:** SQLite (dev) / PostgreSQL (produção)
- **PDF:** ReportLab

## Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/takeozin/mvp-inteligencia-fiscal.git
cd mvp-inteligencia-fiscal

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o .env
cp .env.example .env
# Edite o .env com suas configurações

# 4. Rode a aplicação
python run.py
```

Acesse: http://localhost:5000

## Estrutura
```
app/
  __init__.py       # Factory da aplicação Flask
  models.py         # Modelos do banco (Empresa, ArquivoSPED)
  routes/           # Blueprints de rotas
  templates/        # Templates Jinja2
uploads/            # Arquivos SPED enviados (não versionado)
relatorios/         # PDFs gerados (não versionado)
pareceres/          # Documentos jurídicos (não versionado)
run.py              # Ponto de entrada
```

## Etapas do MVP
- [x] Etapa 1: Setup + Cadastro de empresa
- [ ] Etapa 2: Upload do arquivo SPED
- [ ] Etapa 3: Parser do EFD-Contribuições
- [ ] Etapa 4: Motor de cálculo (Tema 69)
- [ ] Etapa 5: Relatório em PDF
- [ ] Etapa 6: Minuta de parecer jurídico
