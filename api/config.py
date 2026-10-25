import os

# Diretório da aplicação
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """Valores comuns; cada ambiente herda e define seu banco de dados."""
    # Defina SECRET_KEY no ambiente; o valor padrão serve apenas para desenvolvimento local
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')

    DATABASE_CONNECT_OPTIONS = {}

    # Desativa o sistema de eventos do Flask-SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    THREADS_PER_PAGE = 2

    WTF_CSRF_ENABLED = True

    CSRF_SESSION_KEY = os.getenv('CSRF_SESSION_KEY')

    # Limites por IP (Flask-Limiter, ver setup_security.py)
    RATE_LIMITER_OPTS = [ '200 per day', '50 per hour']

    # Configuração de e-mail
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = 'you-will-never-guess@gmail.com'
    # MAIL_PASSWORD = 'you-will-never-guess'

    # Administradores
    ADMINS = ['eliotrianar95@gmail.com']

    # Configuração de sessão
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    # Tamanho da senha (sem uso atual)
    PASSWORD_CHECKER_MIN = 2
    PASSWORD_CHECKER_MAX = 5

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database/app.db')


class DevelopmentConfig(Config):
    """Desenvolvimento: debug ativo e banco dev.db."""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database/dev.db')
    DEBUG = True


class APIConfig(Config):
    """Uso como API: compartilha o dev.db e desativa o CSRF."""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database/dev.db')
    WTF_CSRF_ENABLED = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database/test.db')


config = {
    'base': Config,
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'api': APIConfig,
}