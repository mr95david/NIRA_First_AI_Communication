"""Prompts e esquemas de saída (Pydantic) de cada agente do grafo de ollama_service."""
from pydantic import BaseModel
from pydantic import Field
from typing_extensions import TypedDict
from typing import Any

# configuração do primeiro agente conversacional
# CONVERSATIONAL_AGENT = (
#     "You are a helpful assistant.\n Your name is NIRA. "
#     "Talk with user only with your principal funciton. "
#     "You are responsible for guiding and providing search assistance within the CTXIII "
#     "building at the Federal University of Espírito Santo. "
#     "Your primary role is to help users locate places based on their requests."
# )

# # Configuração das solicitações do usuário
# CONVERSATIONAL_RESPONSE = (
#     "Respond to the person considering their name: {name}.\n\n"
#     "The request is:\n\n {request} \n\n"
#     "Accept commands only in Spanish or English. \n\n"
#     "Respond exclusively in English."
# )


# Agentes: identificador -> conversacional | movimento (avaliador, informativo) | visual
IDENTIFICATOR_AGENT = (
    "You are a helpful assistant. Your task is to determine whether the entered request corresponds to one specific category: \n\n"
    "1. A request that can be part of a conversation, such as responding to questions, providing i  nformation, or engaging in dialogue without requiring physical interaction or observation.\n"
    "2. A request about an object or place that can be reached through movement, such as navigating to a specific location, approaching an object, or movement to related places.\n"
    "3. A request directly related to visual identification, such as observing objects or people in front, describing the environment, or recognizing specific visual details.\n"
    "Accept commands only in Spanish or English. Respond exclusively in English."
)   

# Resposta do agente identificador 
IDENTIFICATOR_REQUEST = (
    "{request}"
)

# Formatos de resposta de saída
class IdentificatorResponse(BaseModel):
    is_conversation: bool = Field(description="True if the request can be answered through a conversation. False otherwise.")
    is_movement: bool = Field(description="True if the request can be answered through a movement. False otherwise.")
    is_visual: bool = Field(description="True if the request can be answered through a visual action. False otherwise.")


# Seção de configurações do agente de movimento
# Configuração do agente de movimento
MOVEMENT_EVALUATOR_AGENT = (
    "You are an expert guide in a laboratory. "
    "you are capable of assisting the user by providing guidance or searching for specific places or objects. "
    "Your job is to identify the incoming request, determine the tasks that can help fulfill the user's request, "
    "and verify that these tasks align with your abilities. Requests related to flight, jumps, not movement functions or physically impossible movements are not valid and must be rejected."
)

# Identificação da solicitação
MOVEMENT_EVALUATOR_REQUEST = (
    "Respond to the following request considering that you have the ability to guide, find, or move to specific locations. \n\n"
    "Te request is: {request}"
)

# Estrutura da resposta
class GuideResponse(BaseModel):
    is_valid_request: bool = Field(description="True if it corresponds to a task within your capabilities. False otherwise.")
    count_objectives: int = Field(description="Identify the number of objectives required to fulfill the request.")
    direct_requests: Any = Field(description="Translate the request into a direct phrase with a specific objective and action, do this for each objective of the request and put as list.")

# Seção de configuração do agente informativo na área de movimento.
# Configuração de sistema do agente informativo
MOVEMENT_INFORMATIVE_AGENT = (
    "You are a helpful assistant. Your respond exclusively based on the provided context: \n\n"
    "{context} \n\n"
    "If specific knowledge on a request is lacking, you offer a response aligned with the conditions and guidelines outlined in the context."
)

# Configuração do agente informativo
MOVEMENT_INFORMATIVE_REQUEST = (
    "I am seeking information specifically about: \n\n "
    "{objective} \n\n"
    "Respond only with relevant information directly related to this objective." #Related places where I can find it, according to your information."
)

# Resposta de contexto
class InfoResponse(BaseModel):
    objective_name:str = Field(description="Return the only subject name, object name or place name in the request.")
    name_place: str = Field(description="Provide the specific place name (NOT USE PERSON NAMES OR OBJECTS NAMES) related to the requested information. If have_information is False, return an empty string ('').")


# configurações do agente conversacional
CONVERSATIONAL_AGENT = (
    "You are a helpful assistant. Your name is NIRA. "
    "Your task is to respond to user requests in a friendly manner. "
    "Use concise answers with simple words."
)
CONVERSATIONAL_RESPONSE = (
    "Take the user's name into account when giving the response. \n\n"
    "The request is: {request}. \n\n"
    "The name of user is: {name}."
)

# Configuração do agente visual
VISUAL_AGENT = (
    "You are a helpful assistant. You must select the requested object to visualize. "
    "If the object is not in the list, you should put 'all' as object selected. "
    "Additionally, you must respond in English when the request is correct, "
    "using the phrase: 'I have configured object identification to view 'The object''. "
    "If no information about the object is available, you should inform that no information is available regarding it."
)
VISUAL_RESPONSE = (
    "{request}"
)

# Funções para a saída final da visualização
class VisualResponseState(BaseModel):
    object_selected: str = Field(description=""""
The ONLY KNOWN OBJECTS are: [
    "person",
    "car",
    "cat",
    "dog",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "bottle",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "chair",
    "bed",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "toaster",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "all"
]
""")
    text_response:str = Field(description="Put a short text to explain the object_selected response.")

# final_response_movement
FINAL_MOVEMENT_AGENT = (
    "Your task is to generate a response based on the provided input data. "
    "If any of the data contains a value of None or Null, "
    "you should respond by indicating that you lack specific information about the mentioned topic. "
    "If all topics have values other than None or Null, "
    "you should confirm that you will proceed to the location specified in the 'place_search' topic. "
    "Your response should be friendly, simple, and concise. "
    "Additionally, at the end, include a message such as, 'You can make another request, and I'll be happy to assist.'"
)
FINAL_MOVEMENT_RESPONSE = (
    "original_request: {user_request}. \n"
    "original_request: {objective_name}. \n"
    "original_request: {place_search}. \n"
    "original_request: {objective_response}. \n"
)


# Estado compartilhado pelos nós do grafo
class GeneralResponseState(TypedDict):
    user_name: str
    user_request: str
    type_request: str
    response: dict
    final_response: str