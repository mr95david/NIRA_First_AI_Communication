"""Versão anterior (desativada): o modelo responde com uma lista JSON livre em vez de usar function calling."""
from openai import OpenAI
from typing import Any
from typing import Dict
from typing import List
from . import api_
import json

class OpenAIInterface:
    """Cliente de chat com histórico; `api` é o esquema de serviços incluído no prompt."""
    def __init__(self, key: str, api: Any = api_) -> None:
        self.api_ = api
        self.chat_history_ = []
        self.system_prompt_ = f"\
            Use this JSON schema to achieve the user's goals:\n\
            {str(api)}\n\
            Respond as a list of JSON objects.\
            Do not include explanations or conversation in the response.\
        "

        self.client = OpenAI(api_key = key)

    def promptToApiCalls(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.8) -> List[Dict]:
        """Envia o prompt com o histórico e devolve a lista de chamadas a serviços ([] se a API falhar)."""
        self.chat_history_.append(  # prompt extraído de https://github.com/Significant-Gravitas/Auto-GPT/blob/master/autogpt/prompts/default_prompts.py
            {
                "role": "user",
                "content": f"\
                    {prompt}\n\
                    Respond only with the output in the exact format specified in the system prompt, with no explanation or conversation.\
                ",
            }
        )

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": self.system_prompt_}]
                + self.chat_history_,
                temperature=temperature,
                n=1,
            )
        except Exception as e:
            print(f"Oops! Something went wrong with {e}.")
            self.chat_history_.pop()
            return []

        self.chat_history_.append(
            {"role": "assistant", "content": response.choices[0].message.content}
        )

        content = self.chat_history_[-1]["content"]
        return self.post_process_response_(content)

    def post_process_response_(self, gpt_response: str) -> List[Dict]:
        """Converte o texto da resposta em lista de dicts (aspas simples -> duplas)."""
        gpt_response = gpt_response.replace("'", '"')
        gpt_response = json.loads(gpt_response)

        if isinstance(gpt_response, list):
            return gpt_response
        else:
            return [gpt_response]