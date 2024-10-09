from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # Permite o acesso da API por domínios diferentes

    # Configuração da aplicação
    app.config.from_pyfile('../config.py')

    # Importar as rotas
    from .routes import main
    app.register_blueprint(main)

    return app
