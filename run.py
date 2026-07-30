import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('APP_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
