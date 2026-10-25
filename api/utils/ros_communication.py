"""Cliente ROS com filas de tarefas por tipo (movimento, visual, obrigatória), cada uma atendida por sua própria thread."""
import roslibpy
import threading
from typing import List
from time import sleep
from json import load as jload
from os import getcwd

# Serviços ROS agrupados pela fila que os executa
MOVECLASS = ["relative_move", "move_to_pose"]
VISUALCLASS = ["enable_object_detection", "object_to_detect"]
MANDATORYCLASS = ["stop_movement"]
INFORMATIONCLASS = ["reject_request"]

class RosClientManagerObject:
    """Conecta ao rosbridge e executa os serviços solicitados pelo agente, separados por tipo de tarefa."""
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9090,
        msj:str = "A solicitação foi recebida corretamente."
    ):
        """Abre a conexão com o rosbridge e registra os serviços base. Lança ValueError se não conectar."""
        self.host:str = host
        self.port:str = port
        self.services:dict = dict()
        self.moviment_list:list = list()
        self.visual_list:list = list()
        self.mandatory_list:list = list()
        # Ordens predefinidas (assets/system_orders) usadas no lugar das do agente se use_movement_system=True
        self.system_task_list: list = list()
        # Mensagem acumulada de resposta ao usuário (em português)
        self.message = msj

        # Indicam se a thread de cada fila está ativa
        self.moving_thread = False
        self.visual_thread = False
        self.mandatory_thread = False

        # Pedido de cancelar a fila de movimento
        self.stop_movement = False

        # Ativado ao receber a resposta de get_status
        self.response_event = threading.Event()

        try:
            self.ros_client = roslibpy.Ros(
                host = host,
                port = port
            )
            self.ros_client.run()
        except Exception as e:
            raise ValueError(f"Error al intentar la conexion. {e}")

        self.set_initial_services()
        self.set_inital_system_orders()

    def excecute_move_thread(self):
        """Inicia a thread de movimento se não houver uma ativa."""
        if not self.moving_thread:
            self.moving_thread = True
            thread_move = threading.Thread(target = self.execute_move_request)
            thread_move.start()

    def execute_move_request(self):
        """Esvazia a fila de movimento: aguarda o robô ficar 'available' e chama cada serviço em ordem."""
        def handle_response_get(response):
            self.serGet_result = response
            self.response_event.set()

        def your_callback_function(result):
            print(f"Service call result: {result}")
        request_get = roslibpy.ServiceRequest({
            'change': True
        })
        while self.moviment_list and not self.stop_movement:
            # Aguarda o robô ficar disponível
            while True:
                self.serGet_result = None
                self.response_event.clear()
                self.services['get_status'].call(request_get, handle_response_get)
                print("Intento de procesamiento")
                if not self.response_event.wait(timeout=2):
                    print("Timeout esperando la respuesta de get_status")
                    continue
                actual_state = self.serGet_result['status']
                if actual_state != "available":
                    continue
                break
            if self.stop_movement:
                break
            next_move = self.moviment_list.pop(0)
            self.append_service(next_move["service"])
            try:
                print(f"Calling service {next_move['service']} with args {next_move['args']}")
                service = self.services.get(next_move['service'])
                if service is not None:
                    request = roslibpy.ServiceRequest(next_move["args"])
                    service.call(request, your_callback_function)
                    sleep(1)
            except Exception as e:
                print(f"Failed to call service with {e}.")
        print("proceso de movimiento terminado")
        self.stop_movement = False
        self.moving_thread = False

    def excecute_visual_thread(self):
        """Inicia a thread visual se não houver uma ativa."""
        if not self.visual_thread:
            self.visual_thread = True
            thread_visual = threading.Thread(target = self.execute_visual_request)
            thread_visual.start()

    def execute_visual_request(self):
        """Esvazia a fila visual (detecção de objetos)."""
        while self.visual_list:
            next_visual = self.visual_list.pop(0)
            self.append_service(next_visual["service"])
            try:
                print(f"Calling service {next_visual['service']} with args {next_visual['args']}")
                service = self.services.get(next_visual['service'])
                if service is not None:
                    request = roslibpy.ServiceRequest(next_visual["args"])
                    service.call(request)
                    sleep(1)
            except Exception as e:
                print(f"Failed to call service with {e}.")
        print("proceso visual terminado")
        self.visual_thread = False

    def excecute_mandatory_thread(self):
        """Inicia a thread de tarefas obrigatórias (stop_movement) se não houver uma ativa."""
        if not self.mandatory_thread:
            self.mandatory_thread = True
            thread_mandatory = threading.Thread(target = self.execute_mandatory_request)
            thread_mandatory.start()

    def execute_mandatory_request(self):
        """Esvazia a fila obrigatória. stop_movement cancela e limpa a fila de movimento."""
        while self.mandatory_list:
            next_mandatory = self.mandatory_list.pop(0)
            self.append_service(next_mandatory["service"])
            if next_mandatory["service"] == "stop_movement":
                self.stop_movement = True
                self.moviment_list.clear()
            try:
                print(f"Calling service {next_mandatory['service']} with args {next_mandatory['args']}")
                service = self.services.get(next_mandatory['service'])
                if service is not None:
                    request = roslibpy.ServiceRequest(next_mandatory["args"])
                    service.call(request)
                    sleep(1)
            except Exception as e:
                print(f"Failed to call service with {e}.")
        print("proceso mandatorio terminado")
        self.mandatory_thread = False

    def set_initial_services(self):
        """Registra os serviços fixos do robô (estado, parada, pose inicial). 'stop_movement' usa /stop_all."""
        self.services['get_status'] = roslibpy.Service(self.ros_client, '/get_status', self.ros_client.get_service_type('/get_status'))
        self.services['change_status'] = roslibpy.Service(self.ros_client, '/change_status', self.ros_client.get_service_type('/change_status'))
        self.services['stop_all'] = roslibpy.Service(self.ros_client, '/stop_all', self.ros_client.get_service_type('/stop_all'))
        self.services['stop_movement'] = roslibpy.Service(self.ros_client, '/stop_all', self.ros_client.get_service_type('/stop_all'))
        self.services['set_initial_pose'] = roslibpy.Service(self.ros_client, '/set_initial_pose', self.ros_client.get_service_type('/set_initial_pose'))

    def set_inital_system_orders(self):
        """Carrega as ordens predefinidas; o caminho é relativo ao diretório de execução."""
        print(getcwd())
        with open("./assets/system_orders/system_orders_format.json", "r") as f:
            self.system_task_list = jload(f)

    # TODO: Melhorar a lógica da função seguinte
    def append_service(self, name_service: str):
        """Registra o serviço '/<name_service>' se ainda não estiver em self.services."""
        if name_service not in self.services:
            self.services[name_service] = roslibpy.Service(self.ros_client, '/'+name_service, self.ros_client.get_service_type('/'+name_service))
        return 

    def add_task(self, new_task_list: List, use_movement_system: bool = False):
        """Classifica cada tarefa ({'service', 'args'}) em sua fila e acumula em self.message o resumo para o usuário."""
        cant_move = 0
        cant_visual = 0
        cant_mandatory = 0
        if len(new_task_list) > 0:
            for i, new_task in enumerate(new_task_list):
                if str(new_task["service"]) in MOVECLASS:
                    if not use_movement_system or len(self.system_task_list) <= 0:
                        self.moviment_list.append(new_task)
                    else:
                        print(f"Tareas del sistema: {self.system_task_list}")
                        self.moviment_list.append(self.system_task_list.pop(0))
                    cant_move+=1
                elif str(new_task["service"]) in VISUALCLASS:
                    self.visual_list.append(new_task)
                    cant_visual+=1
                elif str(new_task["service"]) in MANDATORYCLASS and len(self.mandatory_list) <= 0:
                    self.mandatory_list.append(new_task)
                    cant_mandatory+=1
                else:
                    self.message+=f" A tarefa número {i+1} solicitada corresponde a uma tarefa fora das minhas habilidades."
            if cant_visual > 0 or cant_move > 0 or cant_mandatory > 0:
                self.message+=f" As solicitações dadas correspondem a {cant_move} tarefas de movimento, {cant_visual} tarefas visuais e {cant_mandatory} tarefas obrigatórias."                    
            return 
        self.message+=" Não há tarefas para adicionar."
        return

    def get_actual_task_list(self):
        """Imprime as tarefas pendentes de cada fila."""
        for i, task in enumerate(self.moviment_list):
            print(f"Tarefa de movimento: Tarefa N {i+1}: {task}")
        
        for i, task in enumerate(self.visual_list):
            print(f"Tarefa de visuais: Tarefa N {i+1}: {task}")
        
        for i, task in enumerate(self.mandatory_list):
            print(f"Tarefa de obrigatórias: Tarefa N {i+1}: {task}")

    def clean_message(self):
        self.message = ""

    def __del__(self):
        if self.ros_client.is_connected:
            #print("Closing ROS connection")
            self.ros_client.terminate()
        print("Closing ROS connection")