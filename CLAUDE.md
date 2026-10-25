# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flask backend that lets a user control a mobile robot by voice/text (Portuguese/Spanish/English). A request is interpreted by an LLM, turned into a robot action, and sent to the robot over ROS 2 via rosbridge (`roslibpy`). A prebuilt frontend bundle is served from `api/static` and `api/templates/index.html` (no frontend source in this repo). Code comments are mostly in Spanish.

## Commands

No tests, linter, or README exist. Run from the repo root (paths such as `./assets/...`, `./api/services/...` and `local_docs` are cwd-relative):

```bash
pip install -r requirements.txt   # incomplete: langchain, langchain_ollama, langgraph, pandas, faiss, sentence_transformers, IPython are imported but not listed
python run.py                     # Flask dev server on :5000, config 'development'
```

Alembic migrations live in `api/migrations` (Flask-Migrate, configured with `directory='./api/migrations'`). `run.py` also calls `db.create_all()` on startup against `api/database/dev.db` (SQLite).

## Runtime dependencies (the app fails at import time without them)

- **rosbridge** reachable at `127.0.0.1:9090`. `api/utils/__init__.py` instantiates `ros_connection = RosClientManagerObject()` at import, and `api/routes/ollama_routes.py` creates `RosClientManager()` at import. The robot must expose ROS services such as `/get_status`, `/stop_all`, `/set_initial_pose`.
- **Ollama** running locally with `llama3.1` (chat) and `nomic-embed-text` (embeddings). `ollama_routes.py` builds `OllamaAIInterfaceConnection` and the LangGraph cycle at import time, and `rag_generation` rebuilds the FAISS index (`force_rebuild_index=True`) on every startup.
- OpenAI / Deepgram are only used by routes that are currently disabled (see below).

## Architecture

- `api/__init__.py` — `create_app(config_name)` app factory. Registers blueprints, CORS, Flask-Assets, DB and security. Configs (`development`, `production`, `testing`, `api`) are in `api/config.py`; they differ mainly in the SQLite file (`database/dev.db`, `app.db`, `test.db`).
- **Blueprint registration is selective.** Active: `index`, `user_routes` (user CRUD, no prefix), `ollama_routes` and `interact_routes` (prefix `/api`). `openia_routes` is imported but its `register_blueprint` is commented out, and `deepgram_routes` is commented out entirely. Enabling one means editing `create_app`.
- **Request pipeline (`POST /api/ollama_request`, body `{transcription, name, lastname}`):**
  `routes/ollama_routes.py` → `cycle_llm.invoke(...)` → a LangGraph `StateGraph` built in `services/ollama_service.py::OllamaAIInterfaceConnection.config_cycle`. The graph has an identificator node that routes to conversational, movement (evaluator → informative → final movement), or visual nodes. Agent prompts and Pydantic structured-output schemas are in `services/ollama_config/ollama_configurations.py`. The resulting `final_response` of `movement_response` or `visual_response` triggers `ros_client.execute_movement` / `execute_visual`.
- **RAG:** `utils/lcad_retrieval/` (`SentenceRetriever`, FAISS + `chunks.csv` in `retriever_data/pdf/`) indexes `local_docs/` (PDF/TXT) with Ollama embeddings. `local_docs/map_description.json` (`area_layout.offices`) describes the building map used by the movement agents.
- **ROS layer:** `utils/ros_connection.py` (`RosClientManager`) and `utils/ros_communication.py` (`RosClientManagerObject`) wrap `roslibpy` services/topics. They overlap, so check which one a route actually imports before editing (`ollama_routes` builds its own `RosClientManager` from the `ros_connection` module; `interact_routes` and the disabled OpenAI route use the global `ros_connection` instance from `api/utils/__init__.py`, a `RosClientManagerObject`, so the same name means two different things). `execute_movement` takes OpenAI-style `{"name": ..., "arguments": {...}}` dicts.
- **Robot function definitions are JSON, not code:** `services/functions/movement_functions/*.json` (tool schemas) and `services/service_msgs/srv/*.json` (ROS service message formats) are globbed at import in `services/__init__.py`, which also holds the OpenAI agent config and system prompts (`SYSTEM_DESC_P`, `SYSTEM_DESC_PE`). To add a robot action, add a JSON file there and handle it in the ROS client.
- **Per-user data:** `user_path/<Name_Lastname_ID>/{audio,transcription,ia}_<Name>` hold uploaded audio and transcripts; the latest recording goes to `assets/current-record/recording.wav`.

## Gotchas

- Importing `api.utils` or `api.routes.ollama_routes` has side effects (network connections, index rebuild), so any script or test that imports the app needs rosbridge and Ollama up, or those calls mocked.
- `config.py` contains a hardcoded fallback `SECRET_KEY` and admin email, and `RATE_LIMITER_OPTS` is set via `setup_security.py`. Use env vars (`SECRET_KEY`, `CSRF_SESSION_KEY`) outside local dev.
