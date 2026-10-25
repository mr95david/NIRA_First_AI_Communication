# House Updates

Backend em Flask para controlar um robô móvel por linguagem natural (voz ou texto). Um grafo de agentes baseado em LLM local (Ollama + LangGraph) interpreta a solicitação do usuário, consulta documentos do edifício por RAG (FAISS) e envia a ordem ao robô via ROS 2 através do rosbridge.

```
Usuário ──► Frontend (api/static) ──► Flask ──► Agentes LangGraph (Ollama) ──► roslibpy ──► rosbridge ──► Robô (ROS 2)
                                                        ▲
                                              RAG: local_docs/ + FAISS
```

## Requisitos

| Componente | Versão / detalhe |
|---|---|
| Python | 3.10 (versão usada no desenvolvimento) |
| [Ollama](https://ollama.com) | Em execução em `localhost:11434`, com os modelos `llama3.1` e `nomic-embed-text` |
| rosbridge | `rosbridge_suite` (WebSocket) acessível em `127.0.0.1:9090` |
| Robô / simulador ROS 2 | Deve expor os serviços descritos em [Serviços ROS](#serviços-ros) |
| Hardware | Máquina capaz de executar o `llama3.1` (8B) localmente; recomenda-se GPU ou pelo menos 16 GB de RAM |

> A aplicação conecta-se ao rosbridge e ao Ollama **no momento da importação**. Se algum deles não estiver disponível, `python run.py` falha na inicialização.

## Instalação

```bash
# 1. Clonar
git clone <URL-DO-REPOSITORIO> house_updates
cd house_updates

# 2. Ambiente virtual
python3.10 -m venv .venv
source .venv/bin/activate

# 3. Dependências Python
pip install -r requirements.txt
pip install langchain langchain-core langchain-ollama langgraph ollama \
            pandas numpy faiss-cpu sentence-transformers pypdf pydantic ipython

# 4. Modelos do Ollama
ollama pull llama3.1
ollama pull nomic-embed-text

# 5. Pasta de dados dos usuários
mkdir -p user_path
```

Notas sobre as dependências:

- O `requirements.txt` está incompleto: não inclui os pacotes LangChain, LangGraph, FAISS nem pandas que o código importa; por isso o segundo `pip install` acima. Convém fixar as versões com `pip freeze` depois de validar o ambiente.
- O `cv-bridge` aparece no `requirements.txt`, mas é um pacote do ROS. Se o `pip` falhar ao instalá-lo, remova-o da lista ou instale-o pela sua distribuição do ROS.
- `openai` e `deepgram-sdk` só são usados em rotas atualmente desativadas (ver [Rotas desativadas](#rotas-desativadas)).

## Configuração

Variáveis de ambiente (todas opcionais em desenvolvimento local, obrigatórias em produção):

| Variável | Uso |
|---|---|
| `SECRET_KEY` | Chave de assinatura das sessões do Flask |
| `CSRF_SESSION_KEY` | Chave CSRF |
| `OPENIA_API_KEY` | Somente se `openia_routes` for ativado |
| `DEEPGRAM_API_KEY` | Somente se `deepgram_routes` for ativado |
| `HF_TOKEN` | Somente para `api/utils/lcad_retrieval/example.py` |
| `PORT` | Declarada em `run.py`, mas o `app.run()` atualmente não a usa (o servidor roda na porta 5000) |

Não guarde chaves no código nem as envie ao repositório. O `.gitignore` exclui o `.env`.

Ambientes disponíveis em `api/config.py`: `development` (padrão em `run.py`), `production`, `testing` e `api`. Cada um usa um arquivo SQLite diferente em `api/database/`.

## Execução

Ordem de inicialização:

1. Iniciar o robô ou simulador com o rosbridge: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`
2. Iniciar o Ollama: `ollama serve` (se ainda não estiver rodando como serviço)
3. A partir da raiz do repositório:

   ```bash
   python run.py
   ```

A interface fica em <http://127.0.0.1:5000>. Execute sempre a partir da raiz: várias rotas são relativas ao diretório de trabalho (`./assets`, `./api/services/...`, `local_docs`).

Na primeira execução, o banco de dados SQLite é criado e o índice FAISS é construído a partir de `local_docs/`. O índice é reconstruído a cada inicialização.

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Interface web |
| `GET` | `/index` | Verificação de estado |
| `POST` | `/api/ollama_request` | Solicitação ao agente. Corpo: `{"transcription": "...", "name": "...", "lastname": "..."}` |
| `POST` | `/api/panic` | Interrompe todo movimento do robô |
| `POST` | `/api/retinit_pose` | Reinicia a posição inicial no mapa |
| `GET` | `/users`, `/get_users` | Lista usuários |
| `POST` | `/set_user` | Cria usuário: `name`, `lastname`, `age`, `profession`, `sexo` |
| `DELETE` | `/delete_user` | Remove usuário |
| `GET` | `/validate_user` | Verifica se o usuário existe |

Exemplo:

```bash
curl -X POST http://127.0.0.1:5000/api/ollama_request \
  -H "Content-Type: application/json" \
  -d '{"transcription": "Vá até o laboratório", "name": "Elio", "lastname": "Triana"}'
```

Há um limite de requisições por IP (`200 per day`, `50 per hour`, em `RATE_LIMITER_OPTS`).

## Serviços ROS

O robô deve oferecer, entre outros, estes serviços (via rosbridge): `/get_status`, `/change_status`, `/stop_all`, `/set_initial_pose`, `/move_to_pose`, `/relative_move`, `/enable_object_detection` e `/object_to_detect`. Os formatos de mensagem estão em `api/services/service_msgs/srv/*.json`.

## Estrutura do projeto

```
run.py                       Ponto de entrada
api/
  __init__.py                Factory create_app(config_name)
  config.py                  Configurações por ambiente
  models.py                  Modelo SQLAlchemy (users)
  routes/                    Blueprints do Flask
  services/
    ollama_service.py        Grafo de agentes (LangGraph)
    ollama_config/           Prompts e esquemas de saída de cada agente
    functions/               Definição JSON das ações do robô
    service_msgs/            Formatos JSON dos serviços ROS
  utils/
    ros_*.py                 Clientes roslibpy
    lcad_retrieval/          RAG (FAISS + embeddings)
  static/, templates/        Frontend já compilado
  migrations/                Alembic (Flask-Migrate)
local_docs/                  Documentos e mapa que alimentam o RAG
user_path/                   Dados por usuário (ignorado pelo git)
assets/                      Gravações e formatos de ordens
```

## Adaptação a outro ambiente

- **Outro edifício:** substitua os documentos de `local_docs/` e o `map_description.json` (lê-se a chave `area_layout.offices`).
- **Nova ação do robô:** adicione sua definição JSON em `api/services/functions/movement_functions/`, o formato do serviço em `api/services/service_msgs/srv/`, e registre-a nas listas de classes de `api/utils/ros_communication.py` (`MOVECLASS`, `VISUALCLASS`, etc.).
- **Outro modelo:** altere `llama3.1` em `api/services/ollama_service.py` e `api/services/ollama_config/__init__.py`.

## Rotas desativadas

`openia_routes` (OpenAI com function calling) e `deepgram_routes` (transcrição de áudio) existem no código, mas não estão registradas em `create_app`. Para ativá-las, descomente o `register_blueprint` correspondente em `api/__init__.py` e defina suas chaves por variável de ambiente.

## Convenções de código

- Aplicação modular com *app factory* e um Blueprint por área em `api/routes/`.
- As ações do robô são definidas em JSON, não em código.
- Anotações de tipo em construtores e funções novas; comentários e docstrings em português do Brasil, concisos.
- Respostas JSON com `{"error": "..."}` e o código HTTP correspondente (400, 409, 500).
- Nomes de módulos e variáveis em `snake_case`. As funções de rota existentes misturam `camelCase` e `snake_case`; em código novo use `snake_case`.
- Valores sensíveis são lidos de variáveis de ambiente e nunca têm um valor padrão real.

## Testes

O repositório ainda não inclui testes automatizados. O `TestingConfig` (`create_app('testing')`) usa um banco `test.db` separado, mas importar `api.utils` ou `api.routes.ollama_routes` exige rosbridge e Ollama ativos, ou simulá-los.

## Licença

A definir. Adicione um arquivo `LICENSE` antes de publicar.
