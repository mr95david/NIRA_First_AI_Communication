"""Ações diretas sobre o robô, sem passar pelo agente."""
from flask import Blueprint
from flask import request
from flask import jsonify
from api.utils import ros_connection
from api.utils.utils_functions import getInitialPose
import roslibpy

interact_bp = Blueprint('interact_bp', __name__)

@interact_bp.route('/panic', methods = ["POST"])
def stopAll():
    """Botão de pânico: chama /stop_all."""
    try:
        response = ros_connection.services["stop_all"].call(roslibpy.ServiceRequest({}))
        return jsonify({
            'message': 'All movements stopped',
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@interact_bp.route('/retinit_pose', methods = ["POST"])
def retinit_pose():
    """Reinicia a pose do robô no mapa para a pose inicial padrão."""
    try:
        pose_inicial = getInitialPose()
        response = ros_connection.services["set_initial_pose"].call(roslibpy.ServiceRequest({"pose" : pose_inicial}))
        return jsonify({
            'message': 'Assigned position initialized successfully.',
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500