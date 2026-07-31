    # Configurar pastas absolutas baseadas na raiz do projeto (ou /tmp se estiver na Vercel)
    if os.getenv('VERCEL') == '1':
        base_dir = '/tmp'
    else:
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
