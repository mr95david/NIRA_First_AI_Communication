"""Versão OpenAI (desativada em create_app): function calling + fila de tarefas no ROS + arquivo da conversa."""
from api.services.openia_service import OpenAIInterface
from api.services.openai_functions import OpenAIInterfaceFunctions
from api.utils import RECORD_FOLDER
from api.utils import OPENIA_MODEL
from flask import Blueprint
from flask import request
from flask import jsonify
from api.models import users
from api.utils import ros_connection
from api import db
from glob import glob
import json
import os
import threading
import shutil


openia_bp = Blueprint('openia_bp', __name__)

OPEN_API = os.getenv('OPENIA_API_KEY')

# Versão anterior (JSON livre): OpenAIInterface(key = OPEN_API)
openia_client = OpenAIInterfaceFunctions(key = OPEN_API)

@openia_bp.route("/chat_request", methods = ["POST", "GET"])
def sendOrder():
    """Converte a transcrição em chamadas a serviços ROS, as enfileira e salva áudio, transcrição e resposta do usuário."""
    ros_connection.clean_message()
    try:
        data = request.get_json()

        if not data or 'transcription' not in data or 'name' not in data or 'lastname' not in data:
            return jsonify({"error": "Faltan campos obligatorios (transcription, name, lastname)"}), 400
        
        name = data['name']
        lastname = data['lastname']
        transcription = str(data['transcription'])
        id_test = str(data['istest'])

        existing_user = users.query.filter_by(name = name, lastname = lastname).first()

        if not existing_user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        generated_api_calls = openia_client.promptToCall(
            prompt = transcription
            )
        # istest escolhe entre as ordens do agente e as ordens predefinidas do sistema
        if id_test=="free_test" or id_test=="ai_test_gtp4":
            print("Uso de modelo de ordenes de usuario")
            ros_connection.add_task(generated_api_calls)
        else:
            print("Uso de modelo de ordenes de Sistema")
            ros_connection.add_task(generated_api_calls, use_movement_system=True)

        # Uma thread por fila; as já ativas não são duplicadas
        ros_connection.excecute_move_thread()
        ros_connection.excecute_visual_thread()
        ros_connection.excecute_mandatory_thread()

        path_user = existing_user.user_path
        path_audio = os.path.join(path_user, existing_user.audio_path)
        path_transcription = os.path.join(path_user, existing_user.transcription_path)
        path_ia = os.path.join(path_user, existing_user.ia_path)

        # Áudio enviado pelo frontend
        exists_audio_path = os.path.join(RECORD_FOLDER, "recording.wav") 
        if not os.path.exists(exists_audio_path):
            return jsonify({"error": "Audio file not found"}), 400

        # Copia o áudio para a pasta do usuário como conversacion_N.wav
        audio_files_ = sorted(glob(os.path.join(path_audio, 'conversacion_*.wav')))
        audio_num = len(audio_files_) + 1
        audio_filename = f'conversacion_{audio_num}.wav'

        new_audio_path = os.path.join(path_audio, audio_filename)
        shutil.copy(exists_audio_path, new_audio_path)

        # Adiciona a transcrição a conversations.json
        transcription_json_path = os.path.join(path_transcription, 'conversations.json')
        
        if os.path.exists(transcription_json_path):
            with open(transcription_json_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
        else:
            conversation_data = {}

        conversation_data[f'conversacion_{audio_num}'] = {'data': transcription}

        with open(transcription_json_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=4)
        
        # Salva a resposta do modelo como iaResponse_N.json
        existing_text_files = sorted(glob(os.path.join(path_ia, 'iaResponse_*.json')))
        text_num = len(existing_text_files) + 1
        text_filename = f'iaResponse_{text_num}.json'
        text_file_path = os.path.join(path_ia, text_filename)

        with open(text_file_path, 'w') as f:
            json.dump(generated_api_calls, f, indent=4)

        return jsonify({
            'message': ros_connection.message,
            'transcription': transcription,
            'orders_list': generated_api_calls
        }), 200

    except Exception as e:
        return jsonify({
            "message": 'A solicitação não foi processada.',          
            "error": str(e)
            }), 500