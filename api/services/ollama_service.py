"""Grafo de agentes (LangGraph) que interpreta a solicitação do usuário com Ollama e apoio de RAG."""
from .ollama_config.ollama_configurations import IDENTIFICATOR_AGENT
from .ollama_config.ollama_configurations import IDENTIFICATOR_REQUEST
from .ollama_config.ollama_configurations import IdentificatorResponse
from .ollama_config.ollama_configurations import MOVEMENT_EVALUATOR_AGENT
from .ollama_config.ollama_configurations import MOVEMENT_EVALUATOR_REQUEST
from .ollama_config.ollama_configurations import GuideResponse
from .ollama_config.ollama_configurations import MOVEMENT_INFORMATIVE_AGENT
from .ollama_config.ollama_configurations import MOVEMENT_INFORMATIVE_REQUEST
from .ollama_config.ollama_configurations import InfoResponse
from .ollama_config.ollama_configurations import MOVEMENT_INFORMATIVE_AGENT
from .ollama_config.ollama_configurations import MOVEMENT_INFORMATIVE_REQUEST
from .ollama_config.ollama_configurations import InfoResponse
from .ollama_config.ollama_configurations import CONVERSATIONAL_AGENT
from .ollama_config.ollama_configurations import CONVERSATIONAL_RESPONSE
from .ollama_config.ollama_configurations import VISUAL_AGENT
from .ollama_config.ollama_configurations import VISUAL_RESPONSE
from .ollama_config.ollama_configurations import VisualResponseState
from .ollama_config.ollama_configurations import FINAL_MOVEMENT_AGENT
from .ollama_config.ollama_configurations import FINAL_MOVEMENT_RESPONSE
from .ollama_config.ollama_configurations import GeneralResponseState
from langchain_ollama import ChatOllama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import START
from langgraph.graph import END
from langgraph.graph import StateGraph
from typing import Literal
from api.utils.utils import check_list
from api.utils.utils import get_json_info
from api.utils.lcad_retrieval.lcad_retriever import SentenceRetriever
# Sem uso atual
from IPython.display import Image, display

class OllamaAIInterfaceConnection:
    """Prepara o modelo, o RAG de `path_ret` e o mapa `path_map`; o grafo é construído com config_cycle()."""
    def __init__(self, path_ret:str, path_map:str) -> None:
        self.callback_manager = CallbackManager([StreamingStdOutCallbackHandler])
        self.client_connection = ChatOllama(
            model = "llama3.1",
            temperature = 0.0,
            #callback_manager = self.callback_manager,
            num_predict = 512,
            seed = None
        )

        self.llm_personalized_cycle = None
        self.rag_generation(path_retriever = path_ret)
        self.map_description = self.read_map(path_map = path_map)
        
    def config_agent(self, system_config:str, user_config:str, structured_output = None):
        """Monta uma cadeia prompt -> modelo; com `structured_output` devolve um objeto Pydantic, senão, texto."""
        system_prompt = SystemMessagePromptTemplate.from_template(system_config)
        user_prompt = HumanMessagePromptTemplate.from_template(user_config)

        chat_msg = ChatPromptTemplate.from_messages([
            system_prompt,
            user_prompt
        ])

        if structured_output is not None:
            modelo_structured = self.client_connection.with_structured_output(structured_output)
        
            model = chat_msg | modelo_structured
            return model
        
        model = chat_msg | self.client_connection | StrOutputParser()
        return model
    
    def rag_generation(self, path_retriever: str):
        """Indexa os documentos de `path_retriever` (reconstrói o índice a cada inicialização)."""
        pdf_retriever = SentenceRetriever(use_ollama=True, encoder_model_id="nomic-embed-text")
        pdf_retriever.init_pdf_retriever(
            input_dir="./"+path_retriever, 
            data_dir="retriever_data/pdf/", 
            chunk_size=500,
            overlap_chunks=50,
            force_rebuild_index=True
        )
        self.pdf_retriever = pdf_retriever

    def read_map(self, path_map: str):
        """Devolve a lista de salas (area_layout.offices) do JSON do mapa."""
        map_description = get_json_info(path_map)
        map_description = map_description["area_layout"]["offices"]
        return map_description

    def config_cycle(self):
        """Constrói e compila o grafo: identificator -> conversation | movement | visualization -> response_generation."""
        # Agentes (cadeias prompt + modelo) de cada nó
        identificator_node = self.config_agent(
            system_config=IDENTIFICATOR_AGENT,
            user_config=IDENTIFICATOR_REQUEST,
            structured_output = IdentificatorResponse
        )

        conversator_node = self.config_agent(
            system_config=CONVERSATIONAL_AGENT,
            user_config=CONVERSATIONAL_RESPONSE
        )

        evaluator_node = self.config_agent(
            system_config=MOVEMENT_EVALUATOR_AGENT,
            user_config=MOVEMENT_EVALUATOR_REQUEST,
            structured_output = GuideResponse
        )
        informative_node = self.config_agent(
            system_config=MOVEMENT_INFORMATIVE_AGENT,
            user_config=MOVEMENT_INFORMATIVE_REQUEST,
            structured_output = InfoResponse
        )

        response_final_movement = self.config_agent(
            system_config=FINAL_MOVEMENT_AGENT,
            user_config=FINAL_MOVEMENT_RESPONSE
        )

        visual_node = self.config_agent(
            system_config = VISUAL_AGENT,
            user_config = VISUAL_RESPONSE,
            structured_output = VisualResponseState
        )

        # Nós e roteadores do grafo
        def identificator_state(state: GeneralResponseState):
            response = identificator_node.invoke(
                {"request": state["user_request"]}
            )

            if bool(response.is_conversation):
                return {
                    "type_request": "conversation"
                }
            if bool(response.is_movement):
                return {
                    "type_request": "movement"
                }
            
            if bool(response.is_visual):
                return {
                    "type_request": "visualization"
                }
        # Escolhe o ramo conforme type_request
        def identificator_router(state: GeneralResponseState) -> Literal["conversation", "movement", "visualization"]: 
            return state["type_request"]
        
        def conversator_state(state: GeneralResponseState):
            response = conversator_node.invoke(
                {
                    "request": state["user_request"],
                    "name": state["user_name"]
                }
            )

            return {
                "response": {
                    "conversation_response": response
                }
            }
        
        def movement_state(state: GeneralResponseState):
            # Avalia se a solicitação é um movimento válido
            response = evaluator_node.invoke({
                "request": state["user_request"]
            })

            get_validation, out_value = check_list(response.direct_requests)
            if not get_validation:
                out_value = [out_value]

            new_dict = dict({
                        "validate_request": bool(response.is_valid_request),
                        "direct_requests": out_value[0]
                    })

            return {
                "response": {
                    "movement_response": new_dict
                }
            }
        # Solicitação válida -> informativo; inválida -> resposta final
        def movement_router(state: GeneralResponseState) -> Literal["not_valid", "valid"]:
            actual_response = state["response"]["movement_response"]

            if actual_response["validate_request"]:
                return "valid"
            else:
                return "not_valid"
        
        # Recupera contexto (RAG) e extrai o local de destino
        def informative_sate(state: GeneralResponseState):
            actual_response = state["response"]["movement_response"]

            original_request_retrieval = self.pdf_retriever.get_context(state['user_request'], top_k=3)
            processed_request_retrieval = self.pdf_retriever.get_context(actual_response['direct_requests'], top_k=3)
            context_value = "\n\nRetrieved Context Fragment: \n\n".join(list(set(original_request_retrieval + processed_request_retrieval)))
            
            info_response = informative_node.invoke({
                "context": context_value,
                "objective": actual_response['direct_requests']
            })
            
            actual_response["objective_name"] = info_response.objective_name
            actual_response["place_search"] = info_response.name_place
            
            return {
                "response": {
                    "movement_response": actual_response
                }
            }
        
        # Busca o local no mapa; objective_response fica None se não existir
        def planner_state(state: GeneralResponseState):
            actual_response = state["response"]["movement_response"]
            map_coordinates = None
            for area in self.map_description:
                if area.get("name").upper() == actual_response["place_search"].upper():
                    map_coordinates = area
            
            try:
                actual_response["objective_response"] = map_coordinates["central_point"]
            except Exception as e:
                print(f"Error. The target was not found in the existing information. {e}")
                actual_response["objective_response"] = None
                return {
                    "response": {
                        "movement_response": actual_response
                    }
                }
            
            return {
                    "response": {
                        "movement_response": actual_response
                    }
                }
        
        def visual_state(state: GeneralResponseState):
            response = visual_node.invoke({
                "request": state["user_request"]
            })
            

            return {
                "response": {
                    "visual_response": {
                        "object_selected": response.object_selected,
                        "text_response": response.text_response
                    }
                }
            }
        
        # Conversa: devolve o texto. Movimento/visual: devolve o rótulo que a rota processa
        def final_response_state(state: GeneralResponseState):
            if "conversation_response" in list(state["response"].keys()):
                return {
                    "final_response": state["response"]["conversation_response"]
                }
            if "movement_response" in list(state["response"].keys()):
                actual_response = state["response"]["movement_response"]
                
                return {
                    "final_response": "movement_response"
                }
            if "visual_response" in list(state["response"].keys()):
                return {
                    "final_response": "visual_response"
                }


        # Montagem do grafo
        graph = StateGraph(GeneralResponseState)
        graph.add_node("identificator", identificator_state)
        graph.add_node("conversation", conversator_state)
        graph.add_node("movement", movement_state)
        graph.add_node("informative_movement", informative_sate)
        graph.add_node("planner_movement", planner_state)
        graph.add_node("visualization", visual_state)
        graph.add_node("response_generation", final_response_state)
        graph.add_edge(START, "identificator")
        graph.add_conditional_edges(
            "identificator", identificator_router,
            {"conversation": "conversation", "movement": "movement", "visualization": "visualization"}
        )
        graph.add_edge("conversation", "response_generation")
        graph.add_conditional_edges(
            "movement", movement_router,
            {"valid": "informative_movement", "not_valid": "response_generation"}
        )
        graph.add_edge("informative_movement", "planner_movement")
        graph.add_edge("planner_movement", "response_generation")
        graph.add_edge("visualization", "response_generation")
        graph.add_edge("response_generation", END)

        generalllm = graph.compile()
        return generalllm