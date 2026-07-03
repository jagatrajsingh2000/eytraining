# Adding New Observability

This document records the steps performed to add load testing and agent-wise latency observability to NutriGuard.

It is written as an implementation playbook so the same pattern can be reused when we add new observability signals later.

## Goal

Add observability for:

1. Backend API latency.
2. AI orchestrator agent latency.
3. Load testing.
4. LLM token usage and estimated cost.
5. Published load-test reports in the admin dashboard.
6. Admin dashboard visibility.
7. Unit test coverage for the new metrics.

## Step 1: Reuse Existing Metric Storage

Before adding new tables, we checked the current backend flow.

The backend already stores metric events from orchestrator results in:

```text
services/backend-api/app/routes/meals.py
```

Existing behavior:

```text
orchestrator result
  -> result.metric_events
  -> backend /internal/meal-results
  -> MetricEvent table
```

So we did not add a new database table.

Why:

- `MetricEvent.payload` is already JSON.
- Agent latency can fit naturally as another event type.
- No DB migration is required.

## Step 2: Add A Shared Orchestrator Metrics Helper

Created:

```text
services/ai-orchestrator/app/observability/metrics.py
```

This helper provides:

- `start_timer()`
- `metric_event(...)`
- `agent_latency_event(...)`

The agent latency event shape is:

```json
{
  "name": "agent_latency",
  "source": "health_risk",
  "payload": {
    "duration_ms": 841.22,
    "status": "llm",
    "trace_id": "request-trace-id",
    "meal_log_id": 12
  }
}
```

Why:

- Keeps latency event formatting DRY.
- Makes all agents emit the same event shape.
- Keeps future observability events easy to add.

## Step 3: Emit Agent Latency From Each Agent

Updated these orchestrator agents:

```text
services/ai-orchestrator/app/agents/meal_analyzer_agent.py
services/ai-orchestrator/app/agents/health_risk_agent.py
services/ai-orchestrator/app/agents/report_agent.py
```

For each agent, the implementation pattern is:

```text
start timer
run LLM or fallback logic
append existing LLM metric events
append agent_latency event
return updated state
```

The `status` field is:

- `llm` when the LLM provider chain succeeds.
- `fallback` when the agent uses local fallback logic.

Why:

- We can see which agent is slow.
- We can compare LLM success versus fallback execution.
- The same trace id and meal id connect the full lifecycle.

## Step 4: Aggregate Agent Latency In The Backend

Updated:

```text
services/backend-api/app/routes/admin.py
```

Added:

```python
agent_latency_metrics(metric_events)
```

This aggregates:

- total agent runs
- average latency
- p95 latency
- max latency
- latency by agent
- fallback count by agent

The `/admin/metrics` response now includes:

```json
{
  "agent_latency": {
    "total_runs": 3,
    "average_ms": 120,
    "p95_ms": 180,
    "max_ms": 180,
    "by_agent": [
      {
        "agent": "meal_analyzer",
        "count": 2,
        "average_ms": 150,
        "p95_ms": 180,
        "max_ms": 180,
        "fallback_count": 1
      }
    ]
  }
}
```

Why:

- The frontend should not calculate observability summaries.
- Backend aggregation keeps the dashboard payload simple.
- The admin date filter automatically applies to agent latency because these are stored as `MetricEvent` rows.

## Step 5: Add Token Usage And Estimated Cost

Updated:

```text
services/ai-orchestrator/app/llm/gemini_client.py
services/ai-orchestrator/app/llm/openai_client.py
services/ai-orchestrator/app/llm/provider_chain.py
services/ai-orchestrator/app/llm/token_cost.py
```

The LLM clients now return usage metadata when the provider exposes it.

The provider chain emits:

```json
{
  "name": "llm_token_usage",
  "source": "report",
  "payload": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "input_tokens": 1200,
    "output_tokens": 350,
    "total_tokens": 1550,
    "estimated_cost_usd": 0.00039
  }
}
```

Cost is estimated from hardcoded per-1M-token constants:

```text
OPENAI_INPUT_COST_PER_1M=0.15
OPENAI_OUTPUT_COST_PER_1M=0.60
GEMINI_INPUT_COST_PER_1M=0.0
GEMINI_OUTPUT_COST_PER_1M=0.0
```

These live in:

```text
services/ai-orchestrator/app/llm/token_cost.py
```

Why:

- Gemini is currently treated as free-tier cost unless we configure paid pricing.
- OpenAI fallback has an estimated cost by default.
- The demo deployment does not need extra cost-related environment variables.

## Step 6: Aggregate Token Cost In The Backend

Updated:

```text
services/backend-api/app/routes/admin.py
```

Added:

```python
token_cost_metrics(metric_events)
```

This aggregates:

- LLM calls
- input tokens
- output tokens
- total tokens
- estimated cost
- usage by provider
- usage by agent

Why:

- Admin dashboard can show token/cost without reading raw logs.
- We can compare Gemini versus OpenAI usage.
- We can see which agent is spending the most tokens.

## Step 7: Show Agent Latency And Token Cost In Admin Dashboard

Updated:

```text
frontend/src/pages/AdminPage.jsx
```

Added metric cards:

- Agent runs
- Avg agent latency
- P95 agent latency
- Slowest agent

Added a table:

```text
Agent latency by stage
```

Added token-cost tables:

```text
Token cost by provider
Token cost by agent
```

The table shows:

- agent name
- run count
- avg latency
- p95 latency
- max latency
- fallback count
- LLM calls
- input/output tokens
- total tokens
- estimated cost

Why:

- Admin users can see whether latency is in the API layer or the AI workflow.
- Agent-level breakdown helps identify whether `meal_analyzer`, `health_risk`, or `report` is slow.
- Token cost makes demo and production spend visible.

## Step 8: Add Read-Only Load Testing

Created:

```text
test/load_test_api.py
```

This script sends concurrent GET requests and prints latency stats.

It is intentionally read-only by default:

```text
GET /health
```

Why:

- It gives cheap API latency signal.
- It does not create meals.
- It does not trigger Service Bus.
- It does not burn Gemini/OpenAI quota.

Local command:

```bash
python test/load_test_api.py \
  --base-url http://localhost:8000 \
  --endpoint /health \
  --requests 50 \
  --concurrency 5
```

Hosted command:

```bash
python test/load_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --endpoint /health \
  --requests 50 \
  --concurrency 5
```

Output example:

```json
{
  "requests": 50,
  "success": 50,
  "failed": 0,
  "average_ms": 88.42,
  "p95_ms": 142.11,
  "max_ms": 201.37
}
```

## Step 9: Publish Load Test Results To Dashboard

Updated:

```text
test/load_test_api.py
services/backend-api/app/routes/admin.py
frontend/src/pages/AdminPage.jsx
```

The load-test script can now publish its summary to the backend:

```bash
python test/load_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --endpoint /health \
  --requests 50 \
  --concurrency 5 \
  --publish \
  --internal-api-key "$INTERNAL_API_KEY"
```

If Python cannot verify your local/proxy certificate chain, use the explicit insecure flag for demo testing:

```bash
python test/load_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --endpoint /health \
  --requests 50 \
  --concurrency 5 \
  --publish \
  --internal-api-key "$INTERNAL_API_KEY" \
  --insecure-skip-tls-verify
```

Use this flag only for local/demo troubleshooting, not as a default production habit.

The script sends the summary to:

```text
POST /internal/load-test-results
```

The backend stores it as a `MetricEvent`:

```json
{
  "name": "load_test_result",
  "source": "load_test_api",
  "payload": {
    "base_url": "https://nutriguard-backend...",
    "endpoint": "/health",
    "requests": 50,
    "concurrency": 5,
    "success": 50,
    "failed": 0,
    "average_ms": 88.42,
    "p95_ms": 142.11,
    "max_ms": 201.37
  }
}
```

The admin dashboard shows:

- latest load p95
- requests
- concurrency
- success/failure count
- average latency
- p95 latency
- max latency
- target endpoint
- published timestamp

Why:

- We can prove backend latency from a repeatable script.
- The dashboard keeps the latest report visible for demo and review.
- No schema migration is needed because we reuse `MetricEvent`.

Authenticated profile endpoint load test:

```bash
python test/load_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --profile \
  --profile-user-id 1 \
  --email "user@example.com" \
  --password "UserPassword123" \
  --requests 50 \
  --concurrency 5 \
  --publish \
  --internal-api-key "$INTERNAL_API_KEY"
```

Why this needs a token:

- `GET /users/{user_id}/profile` is user-protected.
- The script can fetch the JWT automatically with `--email` and `--password`.
- You can still pass `--token` directly if you already have a valid JWT.
- This scenario is useful for testing authenticated DB-backed read latency.

## Step 10: Keep Full Workflow Stress Test Separate

Existing file:

```text
test/stress_test_api.py
```

This script exercises:

- signup
- login
- profile creation
- health report upload
- meal logging
- report endpoints

Use it only when we want full workflow load.

Why:

- It creates test users and meal rows.
- It may trigger Service Bus and the orchestrator.
- It can use paid LLM quota indirectly.

Small local run:

```bash
python test/stress_test_api.py \
  --base-url http://localhost:8000 \
  --users 3 \
  --meals-per-user 2
```

Very small production run:

```bash
python test/stress_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --users 1 \
  --meals-per-user 1
```

## Step 11: Add Unit Test Coverage

Updated:

```text
services/backend-api/tests/test_admin_metrics.py
```

Added test coverage for:

```python
agent_latency_metrics(...)
token_cost_metrics(...)
serialize_latest_load_test(...)
```

The test verifies:

- total runs
- average latency
- p95 latency
- max latency
- grouping by agent
- fallback counts
- token totals
- cost totals
- provider grouping
- agent grouping
- latest load-test result selection

Why:

- Admin metrics are product-facing.
- A small aggregation bug would make the dashboard misleading.

## Step 12: Verify The Changes

Backend tests:

```bash
cd services/backend-api
../../.venv/bin/python -m pytest
```

Result:

```text
14 passed
```

Orchestrator compile check:

```bash
cd services/ai-orchestrator
../../.venv/bin/python -m compileall app
```

Frontend build:

```bash
cd frontend
npm run build
```

Result:

```text
✓ built
```

Load test CLI help:

```bash
python3 test/load_test_api.py --help
```

## Step 13: How To Confirm In The UI

1. Deploy backend and orchestrator.
2. Submit a meal.
3. Wait for the orchestrator to process the Service Bus message.
4. Log in as admin.
5. Open Admin Metrics.
6. Select the correct date range.
7. Click `Apply`.

Expected dashboard sections:

- API latency by endpoint
- Agent latency by stage
- Token cost by provider
- Token cost by agent
- Latest load test
- LLM fallback by agent
- RAGAS / RAG quality
- Product metrics

## Step 14: Azure Log Checks

Backend logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --follow
```

Orchestrator logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --follow
```

Historical Log Analytics query:

```kusto
ContainerAppConsoleLogs_CL
| where ContainerAppName_s in ("nutriguard-backend", "nutriguard-orchestrator")
| order by TimeGenerated desc
| take 100
```

## Step 15: Troubleshooting

No API latency in dashboard:

- Run the read-only load test.
- Refresh the Admin Metrics date range.
- Confirm backend middleware is deployed.

No agent latency in dashboard:

- Submit a meal.
- Wait for the orchestrator to finish.
- Check orchestrator logs.
- Confirm backend and orchestrator share the same `INTERNAL_API_KEY`.
- If `/internal/meal-results` returns `401`, the backend rejected the result and did not save metrics.

No token cost in dashboard:

- Submit a new meal after deploying token-cost tracking.
- Confirm the orchestrator result contains `llm_token_usage`.
- Check whether the meal used only local rule fallback; full LLM failure will not produce token usage.
- Confirm `/internal/meal-results` is returning `200`.

No load test result in dashboard:

- Run `test/load_test_api.py` with `--publish`.
- Pass the correct `--internal-api-key`.
- Make sure the Admin Metrics date range includes the publish date.
- Confirm `/internal/load-test-results` returns `{"status": "saved"}`.

High API latency:

- Check Container Apps cold starts.
- Check Postgres connection time.
- Check endpoint-level p95 in Admin Metrics.

High agent latency:

- Check agent latency by stage.
- Check Gemini/OpenAI quota errors.
- Check fallback counts.
- Compare `meal_analyzer`, `health_risk`, and `report` rows.

Load test failures:

- Start with `/health`.
- Reduce concurrency.
- Check backend URL.
- Check CORS only if requests are coming from browser; the Python load test does not use browser CORS.

## Files Changed

```text
services/ai-orchestrator/app/observability/metrics.py
services/ai-orchestrator/app/llm/token_cost.py
services/ai-orchestrator/app/llm/gemini_client.py
services/ai-orchestrator/app/llm/openai_client.py
services/ai-orchestrator/app/llm/provider_chain.py
services/ai-orchestrator/app/agents/meal_analyzer_agent.py
services/ai-orchestrator/app/agents/health_risk_agent.py
services/ai-orchestrator/app/agents/report_agent.py
services/backend-api/app/routes/admin.py
services/backend-api/tests/test_admin_metrics.py
frontend/src/pages/AdminPage.jsx
test/load_test_api.py
docs/adding_new_observibility.md
```
