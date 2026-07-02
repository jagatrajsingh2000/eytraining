# Production Debugging Runbook

This runbook is for debugging NutriGuard on Azure.

Production services:

- Frontend: Azure Static Web Apps
- Backend API: Azure Container Apps
- AI orchestrator worker: Azure Container Apps
- Queue: Azure Service Bus `meal-events`
- Database: Azure PostgreSQL Flexible Server
- Logs: Azure Container Apps log stream and Log Analytics
- Product metrics: NutriGuard Admin dashboard

## 1. First Triage

Start with three questions:

1. Is the frontend calling the correct backend URL?
2. Is the backend healthy?
3. Is the orchestrator processing Service Bus messages and saving results back to backend?

Backend health:

```bash
BACKEND_API_FQDN=$(az containerapp show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

curl "https://$BACKEND_API_FQDN/health"
```

Expected:

```json
{
  "status": "ok",
  "service": "backend-api"
}
```

## 2. Check Container App Status

Backend:

```bash
az containerapp revision list \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --query "[].{name:name, active:properties.active, healthState:properties.healthState, provisioningState:properties.provisioningState}" \
  --output table
```

Orchestrator:

```bash
az containerapp revision list \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --query "[].{name:name, active:properties.active, healthState:properties.healthState, provisioningState:properties.provisioningState}" \
  --output table
```

Healthy target:

```text
Active: True
HealthState: Healthy
ProvisioningState: Provisioned
```

## 3. Check Service Bus Queue

```bash
az servicebus queue show \
  --resource-group rg-nutriguard-demo \
  --namespace-name sb-nutriguard-demo \
  --name meal-events \
  --query "{active:countDetails.activeMessageCount,deadLetter:countDetails.deadLetterMessageCount,scheduled:countDetails.scheduledMessageCount}" \
  --output table
```

How to read it:

- `active > 0`: messages are waiting. Orchestrator may be stopped, crashing, or unable to keep up.
- `deadLetter > 0`: messages failed too many times. Inspect orchestrator logs.
- `active = 0` and reports still missing: backend may not be publishing events, or reports may be failing while saving.

## 4. Check Logs In Azure Portal

For live logs:

1. Azure Portal
2. Container Apps
3. Open `nutriguard-backend` or `nutriguard-orchestrator`
4. Monitoring
5. Log stream

Important: the Container Apps Environment log stream shows platform events first. For app logs, open the specific Container App log stream or query Log Analytics.

## 5. Check Logs With CLI

Backend:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --tail 100
```

Orchestrator:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --tail 100
```

Follow live logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --follow
```

## 6. Common Production Issues

### Issue: Frontend Shows Network Or CORS Errors

Check the frontend build-time API URL:

- GitHub secret: `VITE_API_BASE_URL`
- Static Web App workflow should pass it during build.

Expected value:

```text
https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io
```

Backend CORS for demo:

```bash
az containerapp show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --query "properties.template.containers[0].env[?name=='CORS_ORIGINS']" \
  --output table
```

For demo mode, `CORS_ORIGINS=*` is allowed.

### Issue: Meal Stays In Processing

Check queue:

```bash
az servicebus queue show \
  --resource-group rg-nutriguard-demo \
  --namespace-name sb-nutriguard-demo \
  --name meal-events \
  --query "{active:countDetails.activeMessageCount,deadLetter:countDetails.deadLetterMessageCount}" \
  --output table
```

Then check orchestrator logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --tail 100
```

If logs show:

```text
401 Client Error: Unauthorized for url: .../internal/meal-results
```

Then backend and orchestrator have different `INTERNAL_API_KEY` values.

Fix by setting the same generated key on both:

```bash
INTERNAL_API_KEY=$(openssl rand -hex 32)

az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --secrets internal-api-key="$INTERNAL_API_KEY"

az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --set-env-vars INTERNAL_API_KEY=secretref:internal-api-key

az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --secrets internal-api-key="$INTERNAL_API_KEY"

az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --set-env-vars INTERNAL_API_KEY=secretref:internal-api-key
```

### Issue: Reports Are Generic Or Repeating

Check Admin dashboard:

- Gemini fallbacks
- OpenAI answers
- OpenAI fallbacks
- Rule fallbacks
- Fallback by agent

Meaning:

- High `Gemini fallbacks`: Gemini quota, key, model, or API issue.
- High `OpenAI answers`: Gemini failed but OpenAI recovered.
- High `OpenAI fallbacks`: both Gemini and OpenAI are failing.
- High `Rule fallbacks`: user is receiving deterministic fallback reports.

Check orchestrator env:

```bash
az containerapp show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --query "properties.template.containers[0].env" \
  --output table
```

Required:

```text
GEMINI_API_KEY or GEMINI_API_KEYS
OPENAI_API_KEY
BACKEND_API_URL
INTERNAL_API_KEY
SERVICE_BUS_CONNECTION_STRING
SERVICE_BUS_QUEUE_NAME
```

### Issue: Backend Is Slow

Use Admin dashboard first:

- API requests
- Avg API latency
- P95 API latency
- Slowest API
- Endpoint latency table

This latency is measured inside FastAPI using `time.perf_counter()` around each request. It does not include browser network time or Azure edge time.

### Issue: RAG Quality Looks Bad

Use Admin dashboard:

- RAG hit rate
- RAGAS/RAG quality panel
- Context recall
- Context precision
- Faithfulness, if RAGAS was run with OpenAI

Publish a fresh RAGAS run:

```bash
cd services/ai-orchestrator

export OPENAI_API_KEY="<your-openai-api-key>"
export INTERNAL_API_KEY="<production-internal-api-key>"

../../.venv/bin/python app/rag/eval/run_ragas_eval.py \
  --ragas \
  --judge-provider openai \
  --judge-model gpt-4o-mini \
  --publish \
  --backend-url "https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io" \
  --internal-api-key "$INTERNAL_API_KEY"
```

## 7. Use Trace IDs

Meal submissions include `trace_id`.

Trace ID appears in:

- backend meal response
- backend logs
- Service Bus event payload
- orchestrator logs
- internal meal result save logs

Search logs by trace ID when debugging one failed meal.

Example log line:

```text
Processing meal event trace_id=<id> meal_log_id=<id> user_id=<id>
Saved meal result trace_id=<id> meal_log_id=<id> backend_status=200
```

If you see `Processing meal event` but not `Saved meal result`, the failure is inside orchestrator or the internal backend callback.

## 8. Admin Dashboard Debug Checklist

Login:

```text
Email: admin@nutrigaurd
Password: Admin123
```

Check:

- Date range selector is correct.
- Meals submitted increased after test meal.
- Reports completed increased after orchestrator processing.
- Failed reports is not increasing.
- Missed meal nudges are reasonable.
- Feedback liked/disliked is being collected.
- API p95 is acceptable.
- Gemini/OpenAI/rule fallback counts explain report quality.
- RAGAS panel has latest published evaluation.

## 9. Restart Container Apps

Container Apps usually creates a new revision on env/image updates. If you need a manual restart, update a harmless env var:

```bash
az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --set-env-vars RESTART_MARKER="$(date +%s)"
```

Backend:

```bash
az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --set-env-vars RESTART_MARKER="$(date +%s)"
```

## 10. Roll Forward With GitHub Actions

The normal fix path is:

1. Make code/config fix.
2. Commit and push to `main`.
3. GitHub Actions builds and pushes images.
4. GitHub Actions updates backend and orchestrator Container Apps.

Workflow:

```text
.github/workflows/deploy.yml
```

It triggers on changes under:

```text
services/backend-api/**
services/ai-orchestrator/**
.github/workflows/deploy.yml
```

## 11. Keep Cost Low While Debugging

- Prefer Admin dashboard metrics before enabling expensive monitoring.
- Use log stream only while actively debugging.
- Keep Log Analytics retention low enough for demo needs.
- Avoid repeatedly running OpenAI RAGAS unless you need fresh quality metrics.
- Keep Container Apps `min-replicas=0` for low traffic demo mode.
