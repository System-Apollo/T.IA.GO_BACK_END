from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

 # Configuração do cache
cache = Cache(config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

def create_app():
    app = Flask(__name__)
    CORS(app)  # Permite o acesso da API por domínios diferentes
    

    # Configuração da aplicação
    app.config.from_pyfile('../config.py')
    
    # Inicializa o cache com a aplicação
    cache.init_app(app)

    # Importar as rotas
    from .routes import main
    app.register_blueprint(main)
    
    # Tornar o cache acessível globalmente
    with app.app_context():
        cache.init_app(app)

    return app
