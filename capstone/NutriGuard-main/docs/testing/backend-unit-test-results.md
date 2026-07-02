# Backend Unit Test Results

## Scope

This test pass covers the FastAPI backend helper logic that supports user onboarding, admin observability, notification reminders, and RAG/RAGAS dashboard reporting.

## Test Structure

```text
services/backend-api/
  pytest.ini
  tests/
    conftest.py
    test_admin_metrics.py
    test_notifications.py
    test_users.py
```

## Latest Result

```text
Command: ../../.venv/bin/python -m pytest
Working directory: services/backend-api

13 passed in 0.51s
```

## Covered Areas

### Admin Metrics

- API latency aggregation:
  - total request count
  - average latency
  - p95 latency
  - max latency
  - endpoint grouping
  - latest status code per endpoint
- LLM fallback metrics:
  - Gemini fallback count
  - OpenAI answer count
  - OpenAI fallback count
  - rule fallback count
  - parse fallback count
  - per-agent breakdown
- RAG/RAGAS eval serialization for the admin dashboard.
- Admin-only access guard.

### Notifications

- Meal timestamp conversion into the app timezone.
- Fallback from `meal_time` to `created_at`.
- Notification response serialization.

### Users And Profile Helpers

- Password hashing and verification.
- Rejection of wrong or malformed password hashes.
- Health condition and supplement text normalization.
- Multiple goal normalization.
- Ordered de-duplication for profile arrays.

## How To Run

Install dev test dependencies once:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

Install backend runtime dependencies if the shared virtualenv is missing them:

```bash
cd services/backend-api
../../.venv/bin/python -m pip install -r requirements.txt
```

Run backend unit tests:

```bash
cd services/backend-api
../../.venv/bin/python -m pytest
```

## Notes

- Tests are configured service-locally because both backend and orchestrator use a top-level Python package named `app`.
- Running backend and orchestrator tests in separate service directories avoids import collisions.
- The current shared `.venv` may show dependency tension between backend and orchestrator packages. For cleaner long-term development, use separate virtualenvs per service.
