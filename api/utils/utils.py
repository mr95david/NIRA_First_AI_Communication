"""Utilitários de validação e leitura de arquivos."""
from ast import literal_eval
from json import load

def check_list(data):
    """Devolve (é_lista, dados). Aceita uma lista ou uma string que contenha uma lista literal."""
    validate_list = False
    parsed_data = data
    if isinstance(data, str):
        try:
            parsed_data = literal_eval(data)
            if isinstance(parsed_data, list):
                validate_list = True
            else:
                validate_list = False
        except:
            validate_list = False
    elif isinstance(data, list):
        validate_list = True
    else:
        validate_list = False
    return validate_list, parsed_data

def get_json_info(jsonPath: str):
    """Lê um JSON; se falhar, imprime o erro e devolve ''."""
    data = ""
    try:
        with open(jsonPath, 'r', encoding = 'utf-8') as file:
            data = load(file) 
    except Exception as e:
        print(f"Error en la lectura del archivo json. {e}")
    return data