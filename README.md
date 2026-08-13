# MVP Inteligência Fiscal — Tema 69 STF

Sistema web projetado para leitura de arquivos SPED EFD-Contribuições e cálculo automatizado de recuperação tributária focado na exclusão do ICMS da base de cálculo do PIS/COFINS (Tema 69 STF).

## 🚀 Tecnologias e Stack
- **Backend:** Python 3.12 + Flask
- **Banco de Dados:** PostgreSQL (Supabase) via SQLAlchemy e psycopg2
- **Frontend:** HTML5, CSS e templates Jinja2
- **Geração de Documentos:**
  - PDF: ReportLab
  - DOCX (Minuta): python-docx
- **Infraestrutura / Deploy:** Vercel (Serverless Functions)

## 📦 Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/takeozin/mvp-inteligencia-fiscal.git
cd mvp-inteligencia-fiscal

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o .env
cp .env.example .env
# Edite o .env com sua URL do PostgreSQL (DATABASE_URL)

# 4. Rode a aplicação localmente
python run.py
```
Acesse: `http://localhost:5000`

## ☁️ Deploy na Vercel
A aplicação está otimizada para Serverless Functions na Vercel:
- **`api/index.py`:** Ponto de entrada (WSGI) para a Vercel.
- **Armazenamento Volátil:** Utilização de `/tmp` em produção para lidar com uploads e geração de arquivos temporários, respeitando as restrições de *filesystem* da Vercel.
- **Variáveis de Ambiente Essenciais (Vercel):**
  - `DATABASE_URL`: Configure utilizando o *Connection Pooler IPv4* do Supabase (porta `6543`), pois o ambiente serverless da Vercel possui problemas com resolução direta via IPv6.
  - `VERCEL`: Configure como `1` para ativar o modo de produção (usa o `/tmp`).

## 📂 Estrutura Principal
```text
app/
  __init__.py       # Factory da aplicação Flask
  models.py         # Modelos de dados (Empresa, ArquivoSPED, Resultados)
  routes/           # Blueprints de rotas (empresa, sped, calculo)
  templates/        # Views construídas com Jinja2
  parser/           # Lógica do SPED, Calculadora, Geradores PDF/DOCX
api/
  index.py          # Entrypoint para Vercel Serverless
run.py              # Ponto de entrada (Desenvolvimento Local)
vercel.json         # Configurações de rotas para deploy
```

## ✅ Etapas do MVP
- [x] Etapa 1: Setup + Cadastro de empresa
- [x] Etapa 2: Upload do arquivo SPED
- [x] Etapa 3: Parser do EFD-Contribuições (Blocos C, M)
- [x] Etapa 4: Motor de cálculo (Tema 69 STF)
- [x] Etapa 5: Relatório Analítico em PDF
- [x] Etapa 6: Minuta de Parecer Jurídico em Word (.docx)
- [x] Etapa 7: Migração de banco local (SQLite) para PostgreSQL (Supabase)
- [x] Etapa 8: Deploy final (Serverless) na Vercel
