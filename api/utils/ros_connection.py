"""Cliente ROS síncrono: chama serviços de movimento e visão diretamente das rotas do Flask."""
import roslibpy
from typing import Any
from time import sleep

class RosClientManager:
    """Conexão com o rosbridge usada por ollama_routes. Bloqueia até o robô ficar disponível."""
    def __init__(self,
        host: str = "127.0.0.1",
        port: int = 9090,
        msj:str = "A solicitação foi recebida corretamente."
    ) -> None:
        
        self.host:str = host
        self.port:str = port

        # Serviços ROS já registrados, por nome
        self.services:dict = dict()

        try:
            self.ros_client = roslibpy.Ros(
                host = host,
                port = port
            )
            self.ros_client.run()
        except Exception as e:
            raise ValueError(f"Error al intentar la conexion. {e}")
    
        self.set_initial_services()

    def set_initial_services(self):
        """Registra os serviços fixos do robô (estado, parada, pose inicial)."""
        self.services['get_status'] = roslibpy.Service(self.ros_client, '/get_status', self.ros_client.get_service_type('/get_status'))
        self.services['change_status'] = roslibpy.Service(self.ros_client, '/change_status', self.ros_client.get_service_type('/change_status'))
        self.services['stop_all'] = roslibpy.Service(self.ros_client, '/stop_all', self.ros_client.get_service_type('/stop_all'))
        self.services['stop_movement'] = roslibpy.Service(self.ros_client, '/stop_all', self.ros_client.get_service_type('/stop_all'))
        self.services['set_initial_pose'] = roslibpy.Service(self.ros_client, '/set_initial_pose', self.ros_client.get_service_type('/set_initial_pose'))

    def append_service(self, name_service: str):
        """Registra o serviço '/<name_service>' se ainda não existir."""
        if name_service not in self.services:
            self.services[name_service] = roslibpy.Service(self.ros_client, '/'+name_service, self.ros_client.get_service_type('/'+name_service))
        return 

    def execute_movement(self, objective: Any):
        """Aguarda o robô ficar 'available' e chama o serviço {'name', 'arguments'}. Devolve True se não houve erro."""
        request_get = roslibpy.ServiceRequest({
                'change': True
            })

        def handle_response(response):
            self.serGet_result = response

        def callback_funct(resutl):
            print(f"Serivio disponible, llamado ejecutado: {resutl}")

        while True:
            self.serGet_result = None

            self.services['get_status'].call(request_get, handle_response)
            sleep(1)

            # ATENÇÃO: se a resposta demorar mais de 1 s, serGet_result continua None e falha
            actual_state = self.serGet_result['status']

            if actual_state != "available":
                continue

            break

        self.append_service(objective['name'])
        try:
            print(f"Calling service {objective['name']} with args {objective['arguments']}")
            service = self.services.get(objective['name'])
            if service is not None:
                request = roslibpy.ServiceRequest(objective['arguments'])
                service.call(request, callback_funct)
                sleep(1)
            return True
        except Exception as e:
            print(f"Failed to call service with {e}.")
            return False
        
    def execute_visual(self, visual_request: Any):
        """Chama o serviço visual {'name', 'arguments'} sem aguardar o estado do robô. Devolve True se não houve erro."""
        self.append_service(visual_request["name"])

        try:
            print(f"Calling service {visual_request['name']} with args {visual_request['arguments']}")
            service = self.services.get(visual_request['name'])
            if service is not None:
                request = roslibpy.ServiceRequest(visual_request['arguments'])
                service.call(request)
                sleep(1)
            return True
        except Exception as e:
            print(f"Failed to call service with {e}.")
            return False
