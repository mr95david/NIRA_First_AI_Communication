"""Rotas base: estado do serviço e entrega do frontend."""
from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import send_from_directory
from flask import Response
import os

index = Blueprint('main', __name__, static_folder='static', template_folder='index.html')


@index.route('/index')
def getIndex():
    """Verificação de estado."""
    try:
        return jsonify({
                'message': 'Aplicacion en linea. Lista para ser ejecutada',
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@index.route('/')
def getHome():
    """Serve o frontend compilado."""
    return render_template('index.html')
