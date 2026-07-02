# NutriGuard API Stress Testing

This folder contains a simple `requests`-based stress test for the local NutriGuard backend API.

For RAG quality, safety, and observability evaluation strategy, see `rag_evaluation_strategy.md`.

## What the Script Tests

The script runs complete user workflows concurrently:

- `GET /health`
- `POST /users/signup`
- `POST /users/login`
- `POST /users/{user_id}/profile`
- `GET /users/{user_id}/profile`
- `POST /users/{user_id}/profile/report`
- `POST /meals`
- `GET /meals/{meal_log_id}`
- `GET /meals/{meal_log_id}/report`
- `GET /users/{user_id}/meals`
- `GET /users/{user_id}/daily-report`
- `GET /users/{user_id}/daily-report/details`

Each virtual user creates a unique test account, saves a health profile, uploads a text health report, logs meals, then reads meal and report endpoints.

## Run Prerequisites

Start PostgreSQL:

```powershell
cd C:\Users\Administrator\Documents\NutriGuard\infra
docker compose up -d postgres
```

Start the AI orchestrator if you want the outbox publisher to process meals:

```powershell
cd C:\Users\Administrator\Documents\NutriGuard\services\ai-orchestrator
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8001
```

Start the backend:

```powershell
cd C:\Users\Administrator\Documents\NutriGuard\services\backend-api
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

## Run the Stress Test

From the repo root:

```powershell
cd C:\Users\Administrator\Documents\NutriGuard
.\services\backend-api\.venv\Scripts\python.exe .\test\stress_test_api.py
```

Run with more load:

```powershell
.\services\backend-api\.venv\Scripts\python.exe .\test\stress_test_api.py --users 20 --meals-per-user 5
```

Run against another backend URL:

```powershell
.\services\backend-api\.venv\Scripts\python.exe .\test\stress_test_api.py --base-url http://localhost:8000
```

## Stress Test Strategy

Start small, then increase load gradually:

| Stage | Users | Meals/User | Purpose |
|---|---:|---:|---|
| Smoke | 1 | 1 | Validate backend, database, and payloads |
| Baseline | 5 | 3 | Measure normal local latency |
| Load | 20 | 5 | Check concurrent signup/profile/meal writes |
| Pressure | 50 | 5 | Find database/API bottlenecks |
| Recovery | 10 | 2 | Run after failures or restarts |

## What to Watch

- Signup latency can be high because password hashing is intentionally expensive.
- Meal creation also creates outbox events, so the database write path is tested.
- Report endpoints may return `RECEIVED` or `PROCESSING` if the AI orchestrator has not completed meal processing yet.
- Failures, average latency, p95 latency, and max latency are printed by endpoint.

## Interpreting Results

Healthy local results should show:

- `0` failed requests for smoke and baseline runs.
- Low latency for read endpoints.
- Higher latency for signup due to password hashing.
- No consistent timeouts under the target local load.

If failures appear:

- Confirm backend is running on `http://localhost:8000`.
- Confirm PostgreSQL is running on `localhost:5434`.
- Confirm `services/backend-api/.env` has the correct `DATABASE_URL`.
- Reduce `--users` and retry to find the threshold.
