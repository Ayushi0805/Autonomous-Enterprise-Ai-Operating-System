# Autonomous Enterprise AI Operating System

A production-oriented Django project scaffold for an enterprise AI platform that combines GenAI, agentic workflows, RAG, NLP, CV, ML pipelines, automation, approvals, memory, and observability.

## What It Includes

- Django + Django REST Framework backend with JWT authentication.
- Multi-agent orchestration layer with Router, Planning, Retrieval, RAG, NLP, Vision, EDA, ML Training, Validation, Memory, Reporting, and Automation agents.
- Stateful workflow runs with shared agent state and execution logs.
- Upload support for PDFs, CSV/Excel datasets, images, audio, text, and other enterprise assets.
- RAG service with document parsing, chunking, semantic-search-ready interfaces, citations, and grounded answers.
- Automated EDA and ML training services using pandas and scikit-learn.
- Computer vision service for image metadata and OCR hooks.
- Human approval queue for enterprise governance.
- Memory records for user preferences, workflow history, and long-term context.
- Celery + Redis task execution.
- PostgreSQL primary database.
- Qdrant/Chroma-ready vector layer.
- FastAPI inference microservice.
- n8n automation integration placeholder.
- Docker Compose stack for Django, Celery, PostgreSQL, Redis, Qdrant, n8n, and FastAPI.

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
$env:USE_SQLITE="True"
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

For local development, SQLite is the default database. PostgreSQL is still available in Docker or by setting `USE_POSTGRES=True`.

## Run With Docker

```bash
docker compose up --build
```

Services:

- Django dashboard/API: `http://localhost:8000`
- FastAPI inference: `http://localhost:9000`
- n8n: `http://localhost:5678`
- Qdrant: `http://localhost:6333`

## Main API Flow

1. `POST /api/users/register/`
2. `POST /api/auth/token/`
3. `POST /api/workflows/assets/` with multipart `file`
4. `POST /api/workflows/runs/start/`

Example workflow payload:

```json
{
  "title": "Quarterly revenue intelligence",
  "query": "Analyze revenue risk, train a model, and generate recommendations",
  "asset_ids": [1],
  "require_approval": true
}
```

## Architecture Map

```text
Uploads / User Query
  -> Router Agent
  -> Planning Agent
  -> Retrieval / RAG / NLP / Vision / EDA / ML Agents
  -> Validation Agent
  -> Reporting Agent
  -> Human Approval
  -> Automation Agent / n8n / Notifications
```

## Next Production Steps

- Replace fallback RAG retrieval with Qdrant hybrid retrieval and reranking.
- Add OpenAI, Llama, or enterprise model gateway providers.
- Add LangGraph graph compilation around the current deterministic agent runner.
- Add Django Channels streaming for live agent traces.
- Add MLflow experiment persistence for model training runs.
- Add RBAC groups for analysts, managers, admins, and auditors.
