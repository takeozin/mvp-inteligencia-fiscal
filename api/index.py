import sys
import os

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app

app = create_app()

# Necessário para Vercel Serverless Functions
if __name__ == '__main__':
    app.run(debug=True)
