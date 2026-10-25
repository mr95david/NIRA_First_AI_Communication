"""Factory da aplicação Flask."""
from flask import Flask
from flask_assets import Environment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from api.config import config
from api.setup_security import setup_security_measue_on_aplication

# Extensões compartilhadas com models e routes
db = SQLAlchemy()
migration = Migrate(directory = './api/migrations')

# Atribuído em create_app (rate limiter)
security = None

def create_app(config_name: str) -> Flask:
    """Cria o app com a configuração de `config_name` e registra os blueprints ativos."""
    global security

    app = Flask(__name__)
    CORS(app)
    assets = Environment(app)
    app.config.from_object(config[config_name])
    security = setup_security_measue_on_aplication(app)
    db.init_app(app)
    migration.init_app(app, db)

    # Os imports das rotas ficam aqui: ollama_routes conecta com Ollama e ROS ao ser importado
    from api.routes.index import index
    from api.routes.user_routes import user_bp
    # from api.routes.deepgram_routes import deepgram_bp
    # from api.routes.openia_routes import openia_bp  # exige OPENIA_API_KEY ao importar
    from api.routes.interact_routes import interact_bp
    from api.routes.ollama_routes import ollama_bp
    # openia_bp e deepgram_bp estão desativados (descomentar para usá-los)
    app.register_blueprint(user_bp)
    app.register_blueprint(index)
    app.register_blueprint(ollama_bp, url_prefix='/api')
    # app.register_blueprint(openia_bp, url_prefix='/api')
    app.register_blueprint(interact_bp, url_prefix='/api')

    return app
