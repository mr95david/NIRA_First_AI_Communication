"""Caminhos e conexão global com o ROS. Os caminhos são relativos ao diretório de execução (raiz do repositório)."""
from api.utils.ros_communication import RosClientManagerObject
import os

# Pasta da gravação atual (criada se não existir)
RECORD_FOLDER = './assets/current-record'
os.makedirs(RECORD_FOLDER, exist_ok = True)

# Arquivo de áudio enviado pelo frontend
RECORD_FILE = "./assets/current-record/recording.wav"

# Formatos JSON de serviços ROS
SERVICE_PATH = "./api/services/service_msgs/srv"
# Definições de funções (tools) para a OpenAI
FUNCTIONS_PATH = "./api/services/functions/movement_functions"

# Modelo da OpenAI (versão desativada)
OPENIA_MODEL:str = "gpt-4o-mini"

# Instância única usada pelas rotas (conecta com o rosbridge ao importar)
ros_connection = RosClientManagerObject()