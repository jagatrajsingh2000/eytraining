# NutriGuard Local Development Runbook

This guide runs NutriGuard locally with:

- React frontend
- FastAPI backend
- AI orchestrator with LangGraph agents
- PostgreSQL through Docker
- Local outbox processing instead of Azure Service Bus
- Optional Gemini/OpenAI calls
- Local RAG and RAGAS evaluation

## 1. Local Ports

```text
Frontend:        http://localhost:3000
Backend API:     http://localhost:8000
AI Orchestrator: http://localhost:8001
PostgreSQL:      localhost:5434
```

Postgres uses host port `5434` to avoid conflicts with a local Postgres already using `5432`.

## 2. Start PostgreSQL

From repo root:

```bash
cd infra
docker compose up -d postgres
```

Check it is running:

```bash
docker ps | grep nutriguard-postgres
```

## 3. Backend Environment

Create or update `services/backend-api/.env`:

```env
DATABASE_URL=postgresql://nutriguard_user:nutriguard_pass@localhost:5434/nutriguard_db
AI_ORCHESTRATOR_URL=http://localhost:8001
CORS_ORIGINS=*
ENABLE_OUTBOX_PUBLISHER=true
OUTBOX_PUBLISH_INTERVAL_SECONDS=5
APP_TIMEZONE=Asia/Kolkata
JWT_SECRET=local-dev-jwt-secret-change-me
JWT_EXPIRES_MINUTES=1440
INTERNAL_API_KEY=local-dev-internal-key
```

For local development, `ENABLE_OUTBOX_PUBLISHER=true` means the backend will process meal events itself by calling the local AI orchestrator. Azure Service Bus is not needed locally.

## 4. AI Orchestrator Environment

Create or update `services/ai-orchestrator/.env`:

```env
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-3-flash-preview
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-4o-mini
USE_MOCK_RAG=true
LANGSMITH_TRACING=false
```

Runtime fallback order:

```text
Gemini -> OpenAI -> rule fallback
```

If you do not set Gemini/OpenAI keys, the app still runs, but reports use rule fallback.

## 5. Frontend Environment

Create or update `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Vite reads env vars at build/start time, so restart the frontend after changing this file.

## 6. Install Dependencies

Backend:

```bash
cd services/backend-api
../../.venv/bin/python -m pip install -r requirements.txt
```

AI orchestrator:

```bash
cd services/ai-orchestrator
../../.venv/bin/python -m pip install -r requirements.txt
```

Frontend:

```bash
cd frontend
npm install
```

Dev/test dependencies:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

## 7. Run Services

Terminal 1: AI orchestrator

```bash
cd services/ai-orchestrator
../../.venv/bin/python -m uvicorn app.main:app --reload --port 8001
```

Terminal 2: backend API

```bash
cd services/backend-api
../../.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Terminal 3: frontend

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

Open:

```text
http://localhost:3000
```

## 8. Smoke Checks

Backend health:

```bash
curl http://localhost:8000/health
```

AI orchestrator health:

```bash
curl http://localhost:8001/health
```

Expected response shape:

```json
{
  "status": "ok"
}
```

## 9. Admin Login

The backend seeds a local admin user at startup:

```text
Email: admin@nutrigaurd
Password: Admin123
```

Use this account to open the Admin dashboard and view:

- meals submitted
- reports completed
- failed reports
- API latency
- LLM fallback counts
- feedback metrics
- RAG/RAGAS evaluation results

## 10. Local End-To-End Flow

1. Start Postgres.
2. Start AI orchestrator on port `8001`.
3. Start backend on port `8000`.
4. Start frontend on port `3000`.
5. Sign up or log in.
6. Create/update profile.
7. Log meals with timing, foods, drinks, supplements, and notes.
8. Backend writes the meal to `meal_logs`.
9. Backend writes an outbox event.
10. Local outbox publisher calls AI orchestrator.
11. Orchestrator runs:
    - Meal Analyzer Agent
    - Health Risk Agent
    - Report Agent
12. Backend saves report and flags.
13. Frontend shows meal-level and combined daily reports.

## 11. Run Backend Unit Tests

```bash
cd services/backend-api
../../.venv/bin/python -m pytest
```

Current expected result:

```text
13 passed
```

## 12. Run RAG Retrieval Evaluation

This does not call OpenAI:

```bash
cd services/ai-orchestrator
../../.venv/bin/python app/rag/eval/run_ragas_eval.py --limit 3
```

## 13. Run RAGAS With OpenAI

Install RAGAS dependencies:

```bash
cd services/ai-orchestrator
../../.venv/bin/python -m pip install -r requirements-ragas.txt
```

Run RAGAS:

```bash
export OPENAI_API_KEY="<your-openai-api-key>"

../../.venv/bin/python app/rag/eval/run_ragas_eval.py \
  --ragas \
  --judge-provider openai \
  --judge-model gpt-4o-mini
```

Publish local RAGAS result to a running local backend:

```bash
export INTERNAL_API_KEY="local-dev-internal-key"

../../.venv/bin/python app/rag/eval/run_ragas_eval.py \
  --ragas \
  --judge-provider openai \
  --judge-model gpt-4o-mini \
  --publish \
  --backend-url http://localhost:8000 \
  --internal-api-key "$INTERNAL_API_KEY"
```

## 14. Troubleshooting

### Frontend Calls Hosted Backend Instead Of Local

Check `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Restart Vite after changing it.

### CORS Error

For local development, backend can use:

```env
CORS_ORIGINS=*
```

Restart backend after changing `.env`.

### Meal Stays In Processing

Check:

- AI orchestrator is running on `localhost:8001`.
- Backend has `ENABLE_OUTBOX_PUBLISHER=true`.
- Backend has `AI_ORCHESTRATOR_URL=http://localhost:8001`.
- Backend logs show the local outbox publisher running.

### AI Report Looks Like Fallback

Check orchestrator `.env`:

```env
GEMINI_API_KEY=<your-gemini-api-key>
OPENAI_API_KEY=<your-openai-api-key>
```

If Gemini fails or hits quota, OpenAI is used. If both fail, rule fallback is used.

### Do Not Commit Secrets

Keep `.env` files local. Do not commit API keys, database passwords, JWT secrets, or internal API keys.
