"""Limitador de requisições por IP."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def setup_security_measue_on_aplication(app):
    """Aplica os limites de RATE_LIMITER_OPTS ao app e devolve {"limiter": Limiter}."""
    limiter = Limiter(
        get_remote_address,
        app = app,
        default_limits = app.config['RATE_LIMITER_OPTS']
    )

    return {"limiter": limiter}