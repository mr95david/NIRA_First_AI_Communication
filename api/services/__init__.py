"""Carrega as definições JSON do robô e a configuração/prompts do agente OpenAI."""
from api.utils import SERVICE_PATH, FUNCTIONS_PATH
from glob import glob
import json

# Formatos de serviços ROS
api_ = []
for api_file in glob(f"{SERVICE_PATH}/*.json"):
    with open(api_file, "r") as f:
        api_.append(json.load(f))

# Funções disponíveis para o agente (formato tools da OpenAI)
api_funct = []
for api_f in glob(f"{FUNCTIONS_PATH}/*.json"):
    with open(api_f, "r") as f:
        api_funct.append(json.load(f))

# Parâmetros da chamada a chat.completions
CONFIG_AGENT: dict = {
    "model": "gpt-4o-mini",
    "max_tokens": 8000,
    "temperature" : 0.6,
    "stop" : None,
    "tools" : "functions_temp",
    "seed" : 42,
    "tool_choice" : "required"
}

# Prompts de sistema: P (português), PE (inglês; o usado por OpenAIInterfaceFunctions)
SYSTEM_DESC_P = """
Você é uma inteligência artificial encarregada de controlar um robô móvel com base em solicitações do usuário fornecidas em português.
Para atender a essas solicitações, você tem acesso a um conjunto predefinido de funções; você só pode responder fornecendo a estrutura exata — nome da função e os parâmetros necessários — de uma dessas funções disponíveis.
Se a solicitação do usuário não puder ser atendida por nenhuma das funções à sua disposição, você deve retornar a função "reject_request".
Se a solicitação do usuário for ambígua, confusa ou inconsistente com as funções disponíveis, você deve retornar a função "reject_request".
Valores positivos viram para a esquerda, valores negativos viram para a direita.
O sistema distingue comandos usando "depois", "então", "e" ou "próximo" para sequenciar ações e diferencia entre movimentos lineares e angulares para navegação precisa do robô.
"""

SYSTEM_DESC_PE = """
You are an artificial intelligence tasked with controlling a mobile robot based on user requests provided in Portuguese. Use the supplied tools to assist the user.
If the user's request cannot be fulfilled by any of the functions at your disposal, you must return the tool "reject_request".
If the user's request is ambiguous, unclear, or inconsistent with the available functions, you must return the tool "reject_request".
Positive angular values turn left, negative angular values turn right.
The system distinguishes commands using "after," "then," or "next" to sequence actions and differentiates between linear and angular movements for precise robot navigation.
finally handle orientation changes (right, left, full turn) as angular differences in radians from -pi to pi.
Tens que identificar quando se faz referência a números e coordenadas. Por exemplo, quando se usa 'dois zero', isso corresponde a (2, 0). O mesmo se aplica para combinações como 'três três', que corresponde a (3, 3).
"""
