"""Ponto de entrada: cria o app (ambiente 'development'), garante as tabelas e sobe o servidor."""
from api import create_app
# Importar api.utils abre a conexão com o rosbridge
from api.utils import ros_connection
from api import db
import os

# Ambientes disponíveis em api/config.py: development, production, testing, api
app = create_app(config_name = 'development')
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # app.run(debug=True, host='0.0.0.0', port=5000)  # expor na rede local
    app.run(debug=True, port=port)
    del ros_connection