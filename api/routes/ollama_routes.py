"""Endpoint principal: a solicitação do usuário passa pelo grafo de agentes e é executada no robô."""
from api.services.ollama_service import OllamaAIInterfaceConnection
from api.utils.ros_connection import RosClientManager
from flask import Blueprint
from flask import request
from flask import jsonify
import os

ollama_bp = Blueprint('ollama_bp', __name__)

# Criados ao importar o módulo: exigem Ollama e rosbridge ativos
ollama_client = OllamaAIInterfaceConnection(path_ret = "local_docs", path_map = "./local_docs/map_description.json")
ros_client = RosClientManager()
cycle_llm = ollama_client.config_cycle()

@ollama_bp.route("/ollama_request", methods = ["POST", "GET"])
def chatRequest():
    """Recebe {transcription, name, lastname}, invoca o grafo e devolve o texto de resposta ao usuário."""
    try:
        data = request.get_json()
        
        if not data or 'transcription' not in data or 'name' not in data or 'lastname' not in data:
                return jsonify({"Error": "Missing required fields (transcription, name, lastname)"}), 400
        
        name = str(data['name'])
        transcription = str(data['transcription'])

        if cycle_llm is None:
            raise ValueError("The object 'model_conversational' was not configured properly.")

        try:
            response = cycle_llm.invoke(input={"user_name": name, "user_request": transcription})
            if response is None:
                raise ValueError("Error. Response from ollama model is None.")
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error during invoke: {str(e)}")
            raise

        # Movimento: envia move_to_pose com as coordenadas do local (theta fixo em 0)
        if response['final_response'] == "movement_response":
            actual_response = response["response"]["movement_response"]
            try:
                movement_request = {"name": "move_to_pose", "arguments": {"x":  actual_response["objective_response"]['coordinates']['x'], "y": actual_response["objective_response"]['coordinates']['y'], "theta": 0.0}}
                ros_client.execute_movement(movement_request)
                response["final_response"] = "I am moving to the indicated location. Can I help you with anything else"  
            except Exception as e:
                print(e)
                response["final_response"] = "It was not possible to execute the requested movements. Can I help you with anything else?"


        # Visual: configura o objeto a detectar
        if response['final_response'] == "visual_response":
            actual_response = response["response"]["visual_response"]
            visual_request = {"name": "object_to_detect", "arguments": {"data": actual_response["object_selected"]}}
            ros_client.execute_visual(visual_request)

            if actual_response["text_response"] != "":
                response['final_response'] = actual_response["text_response"]
            else:
                response["final_response"] = f"The identification of {actual_response['object_selected']} has been successfully configured."
        return jsonify({
                'response': response['final_response'],
                'transcription': transcription,
            }), 200
    except Exception as e:
        return jsonify({
            "message": 'The request was not processed.',          
            "error": str(e)
            }), 500