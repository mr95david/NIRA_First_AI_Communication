"""Cliente OpenAI com function calling (desativado em create_app)."""
from openai import OpenAI
from typing import Any
from typing import Dict
from typing import List
from . import api_funct
from . import CONFIG_AGENT
from . import SYSTEM_DESC_PE
import json

class OpenAIInterfaceFunctions:
    """Traduz uma solicitação em linguagem natural em chamadas das funções do robô (api_funct)."""
    def __init__(self, key: str, api: Any = api_funct) -> None:
        self.api_List = api
        self.chat_history_ = []
        self.system_prompt_ = SYSTEM_DESC_PE

        self.client = OpenAI(api_key = key)

    def promptToCall(self, prompt: str, params: dict = CONFIG_AGENT):
        """Devolve a lista [{'service', 'args'}] escolhida pelo modelo ([] se a API falhar)."""
        # Cópia para não alterar o CONFIG_AGENT global
        params = dict(params)
        params["messages"] = [
            {"role": "system", "content": self.system_prompt_},
            {"role": "user", "content": prompt},
        ]

        params["tools"] = self.api_List

        try:
            response = self.client.chat.completions.create(
                **params
            )
        except Exception as e:
            print(f"Oops! Something went wrong with {e}.")
            return []

        final_content = response.choices[0].message.tool_calls
        return self.post_process_response(final_content)

    def post_process_response(self, chat_response:list):
        """Converte os tool_calls para o formato {'service', 'args'} usado pelo cliente ROS."""
        transform_response= []
        for iter in chat_response:
            dict_temp=dict()
            dict_temp["service"] = iter.function.name
            dict_temp["args"] = json.loads(iter.function.arguments)

            # O modelo devolve o booleano como texto
            if iter.function.name == "enable_object_detection":
                 dict_temp["args"]['data'] = dict_temp["args"]['data'] == "True"

            # Corrige a chave 'linear:' (com dois-pontos) que o modelo às vezes gera
            if "linear:" in dict_temp["args"].keys():
                dict_temp["args"]['linear'] = dict_temp["args"].pop('linear:')

            transform_response.append(dict_temp)
        return transform_response
