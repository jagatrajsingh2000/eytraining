# NutriGuard Challenges And Fixes

This document records the main production and integration challenges we faced while building and deploying NutriGuard, along with the fixes we applied.

The goal is to keep a practical learning log for debugging, demo preparation, and future production hardening.

## 1. Gemini Free-Tier Daily Limit

### Symptom

The AI orchestrator started returning repeated fallback-style reports instead of fresh Gemini-generated analysis.

In orchestrator logs, we saw quota errors like:

```text
quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
quota_dimensions {
  key: "model"
  value: "gemini-3-flash"
}
quota_value: 20
```

### Root Cause

The Gemini model was running on the free tier and hit the daily request quota.

Because the daily limit was small, repeated meal submissions, debugging, and stress testing quickly consumed the quota.

### Impact

- Meal reports became less personalized.
- The same fallback response could appear repeatedly.
- RAG and profile context were still available, but the LLM-generated output was limited.
- It became harder to validate real orchestration quality during demos.

### Fix Applied

We added provider fallback behavior in the AI orchestrator.

The provider chain now tries Gemini first, then uses OpenAI as fallback when Gemini fails or hits quota.

We also record fallback metric events so the admin dashboard can show what happened.

Tracked events include:

```text
gemini_fallback
openai_answer
openai_fallback
rule_fallback
llm_parse_fallback
```

These are visible in the Admin Metrics page under:

```text
LLM fallback by agent
```

### Operational Guidance

For demos:

- Keep Gemini calls low before the demo.
- Avoid running full workflow stress tests repeatedly.
- Use the read-only load test for API latency instead of creating many meals.
- Check Admin Metrics for fallback counts.
- Check orchestrator logs if reports look repeated.

For production:

- Move to a paid Gemini quota or use a more stable paid LLM provider.
- Keep OpenAI fallback enabled.
- Add alerting when Gemini fallback count crosses a threshold.
- Track fallback rate by agent.

## 2. Azure Service Bus Message Lock Expired

### Symptom

The AI orchestrator processed a Service Bus message, but crashed while completing it.

Log excerpt:

```text
azure.servicebus.exceptions.MessageLockLostError:
The lock on the message lock has expired.
```

The failure happened here:

```text
receiver.complete_message(message)
```

### Root Cause

Azure Service Bus locks a message for a limited time while a worker processes it.

Our orchestrator processing can take longer than the default lock window because it may include:

- Gemini call
- OpenAI fallback call
- RAG retrieval
- report generation
- backend `/internal/meal-results` save

When processing took too long, the lock expired before the worker called `complete_message`.

### Impact

- The orchestrator worker crashed.
- The same Service Bus message could be delivered again.
- Duplicate processing could happen.
- The backend may receive repeated meal result saves.

### Fix Applied

We updated:

```text
services/ai-orchestrator/app/worker.py
```

The worker now uses Azure Service Bus `AutoLockRenewer`.

New behavior:

```text
receive message
  -> register message with AutoLockRenewer
  -> process meal
  -> save result to backend
  -> complete message
```

We also added safe handling for `MessageLockLostError` so the worker logs the issue instead of crashing after processing.

### New Config

Optional environment variable:

```bash
SERVICE_BUS_LOCK_RENEWAL_SECONDS=300
```

Default:

```text
300 seconds
```

### Operational Guidance

If this happens again:

1. Check orchestrator logs.
2. Look for `MessageLockLostError`.
3. Check whether LLM calls are slow or failing.
4. Increase `SERVICE_BUS_LOCK_RENEWAL_SECONDS` if needed.
5. Confirm backend `/internal/meal-results` is returning `200`.

Useful command:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --follow
```

## 3. Internal API Key Mismatch

### Symptom

The orchestrator processed a meal but failed to save the result to the backend.

Log excerpt:

```text
401 Client Error: Unauthorized for url:
https://nutriguard-backend.../internal/meal-results
```

### Root Cause

The backend and orchestrator did not have matching `INTERNAL_API_KEY` values.

The backend protects internal endpoints with:

```text
x-internal-api-key
```

If the orchestrator sends a different key, the backend rejects the save request.

### Impact

- Meal status may stay processing.
- Daily report may not update.
- Agent latency and LLM fallback metrics are not saved.
- User sees stale or missing report data.

### Fix Applied

We confirmed the same `INTERNAL_API_KEY` must be configured in both Container Apps:

- `nutriguard-backend`
- `nutriguard-orchestrator`

### Operational Guidance

When updating secrets:

```bash
az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --secrets internal-api-key="$INTERNAL_API_KEY"
```

```bash
az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --secrets internal-api-key="$INTERNAL_API_KEY"
```

Then make sure env vars reference the secret:

```text
INTERNAL_API_KEY=secretref:internal-api-key
```

## 4. CORS While Testing From Another Laptop

### Symptom

Frontend worked locally on one machine, but API calls failed from another laptop.

Browser network tab showed CORS errors.

### Root Cause

The frontend origin changed when accessed from another laptop or through ngrok.

Examples:

```text
http://localhost:3000
http://192.168.1.78:3000
https://some-ngrok-url.ngrok-free.app
```

The backend CORS allowlist did not include every testing origin.

### Fix Applied

For development, we temporarily allowed broad CORS.

For production, the safer approach is to allow only:

- Azure Static Web Apps frontend URL
- local dev URL
- temporary ngrok URL if actively testing

### Operational Guidance

If browser says CORS but `curl` works, it is likely frontend origin configuration.

Check:

- frontend `VITE_API_BASE_URL`
- backend CORS config
- browser request origin
- whether the frontend build picked up the latest environment variable

## 5. Frontend Build Used Wrong API URL

### Symptom

Production frontend tried to call:

```text
http://localhost:8000
```

Browser showed:

```text
net::ERR_CONNECTION_REFUSED
```

### Root Cause

Vite reads environment variables at build time.

If `VITE_API_BASE_URL` is missing during GitHub Actions build, the deployed static frontend can still contain the local fallback URL.

### Fix Applied

We configured GitHub Actions to read:

```text
VITE_API_BASE_URL
```

from GitHub secrets.

### Operational Guidance

After changing `VITE_API_BASE_URL`:

1. Update GitHub secret.
2. Re-run frontend deployment.
3. Hard refresh browser.
4. Check browser network tab.

## 6. Observability Was Initially Too Hard To Inspect

### Symptom

We had logs in Azure, but it was not easy to answer product questions like:

- How many meals were submitted?
- How many reports completed?
- How many failed?
- How often did Gemini fallback happen?
- What is API latency?
- Which agent is slow?

### Root Cause

Raw Azure logs are useful for debugging, but not enough for demo/product metrics.

### Fix Applied

We added database-backed admin metrics:

- meals submitted per day
- reports completed
- failed reports
- average report processing time
- feedback liked/disliked
- missed meal notification count
- unread notification count
- Gemini/OpenAI fallback count
- API latency
- agent-wise latency
- RAGAS/RAG quality

These are visible in the Admin Metrics page.

### Operational Guidance

Use the dashboard first for product health.

Use Azure logs second for root-cause debugging.

## 7. RAGAS Result Was Not Visible In Dashboard

### Symptom

The dashboard showed:

```text
No RAG eval result yet
```

even after running local evaluation.

### Root Cause

The RAGAS script must publish results to the backend using:

```text
/internal/rag-eval-results
```

If the internal API key is missing or wrong, the result will not be saved.

### Fix Applied

We added backend storage for RAG eval runs and dashboard display for:

- retrieval hit rate
- context recall
- context precision
- faithfulness
- RAGAS context precision
- RAGAS context recall

### Operational Guidance

Run:

```bash
cd services/ai-orchestrator
python app/rag/eval/run_ragas_eval.py \
  --ragas \
  --judge-provider openai \
  --judge-model gpt-4o-mini \
  --publish \
  --backend-url "https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io" \
  --internal-api-key "$INTERNAL_API_KEY"
```

Then refresh Admin Metrics.

## Quick Debug Checklist

When something fails in production:

1. Check Admin Metrics date range.
2. Check API latency by endpoint.
3. Check agent latency by stage.
4. Check LLM fallback by agent.
5. Check orchestrator logs.
6. Check backend logs.
7. Confirm `INTERNAL_API_KEY`.
8. Confirm `VITE_API_BASE_URL`.
9. Confirm Service Bus queue has no stuck messages.
10. Confirm Gemini/OpenAI quota status.

## Useful Commands

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

Read-only API load test:

```bash
python test/load_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --endpoint /health \
  --requests 50 \
  --concurrency 5
```

Full workflow stress test:

```bash
python test/stress_test_api.py \
  --base-url https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io \
  --users 1 \
  --meals-per-user 1
```
