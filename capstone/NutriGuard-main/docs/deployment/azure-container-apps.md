# NutriGuard Azure Deployment

This guide captures the working low-cost Azure deployment path we used for NutriGuard.

## Target Architecture

- Frontend: Azure Static Web Apps
- Backend API: Azure Container Apps
- AI Orchestrator: Azure Container Apps worker
- Queue: Azure Service Bus Basic
- Database: Azure Database for PostgreSQL Flexible Server
- Images: Azure Container Registry Basic
- CI/CD: GitHub Actions

Runtime flow:

```text
Frontend
  -> Backend API
  -> Azure Service Bus queue
  -> AI Orchestrator worker
  -> Gemini
  -> Backend internal result endpoint
  -> PostgreSQL
```

## Resource Names

```text
Resource group: rg-nutriguard-demo
Region: centralindia
Registry: acrnutriguarddemo
Backend: nutriguard-backend
Orchestrator: nutriguard-orchestrator
Static app: nutriguard-web
Postgres: pg-nutriguard-demo
Service Bus namespace: sb-nutriguard-demo
Queue: meal-events
Container Apps environment: cae-nutriguard-demo
Log Analytics workspace: log-nutriguard-demo
```

## Cost Controls

Use these settings for a short demo:

```text
Container Apps min replicas: 0
Container Apps max replicas: 1
CPU: 0.25
Memory: 0.5Gi
Service Bus: Basic
ACR: Basic
Postgres: Burstable B1ms or smallest available
Postgres high availability: off
Log Analytics retention: 30 days
```

Notes:

- Log Analytics may reject 7-day retention. Use 30 days if 7 fails.
- Stop PostgreSQL when not testing.
- Delete the whole resource group after the demo if you no longer need it.

## 1. Login And Verify Subscription

```bash
az login
az account show
```

Verify:

```text
state: Enabled
isDefault: true
```

For this deployment we used subscription:

```text
2feb1844-57df-461f-8845-be07a8ccd703
```

## 2. Create Resource Group

```bash
az group create \
  --name rg-nutriguard-demo \
  --location centralindia
```

Why: every demo resource goes inside one group so cleanup is one command.

## 3. Register Azure Providers

New Azure subscriptions often need providers registered before first use.

```bash
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.ServiceBus
az provider register --namespace Microsoft.DBforPostgreSQL
```

Check status when needed:

```bash
az provider show \
  --namespace Microsoft.ContainerRegistry \
  --query registrationState \
  --output tsv
```

Wait until the result is:

```text
Registered
```

## 4. Create Azure Container Registry

```bash
az acr create \
  --resource-group rg-nutriguard-demo \
  --name acrnutriguarddemo \
  --sku Basic \
  --admin-enabled true
```

Why: Container Apps pulls backend and orchestrator images from ACR.

## 5. Create Log Analytics

```bash
az monitor log-analytics workspace create \
  --resource-group rg-nutriguard-demo \
  --workspace-name log-nutriguard-demo \
  --location centralindia \
  --retention-time 30
```

Why: Container Apps sends logs here. Keep logs minimal to control cost.

## 6. Create Container Apps Environment

```bash
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group rg-nutriguard-demo \
  --workspace-name log-nutriguard-demo \
  --query customerId \
  --output tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group rg-nutriguard-demo \
  --workspace-name log-nutriguard-demo \
  --query primarySharedKey \
  --output tsv)

az containerapp env create \
  --resource-group rg-nutriguard-demo \
  --name cae-nutriguard-demo \
  --location centralindia \
  --logs-workspace-id "$WORKSPACE_ID" \
  --logs-workspace-key "$WORKSPACE_KEY"
```

Why: both container apps run inside this environment.

## 7. Create Service Bus Queue

```bash
az servicebus namespace create \
  --resource-group rg-nutriguard-demo \
  --name sb-nutriguard-demo \
  --location centralindia \
  --sku Basic

az servicebus queue create \
  --resource-group rg-nutriguard-demo \
  --namespace-name sb-nutriguard-demo \
  --name meal-events
```

Why: backend queues meal jobs and the orchestrator worker wakes up from this queue.

## 8. Create PostgreSQL

Use a URL-safe password with letters and numbers only, for example:

```text
NutriGuardDemo2026X
```

Avoid `@`, `/`, `#`, `?`, `%`, and `:` unless you URL-encode the password. These characters can break `DATABASE_URL`.

Create the server:

```bash
az postgres flexible-server create \
  --resource-group rg-nutriguard-demo \
  --name pg-nutriguard-demo \
  --location centralindia \
  --admin-user nutriguard_admin \
  --admin-password "<url-safe-password>" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 16 \
  --public-access 0.0.0.0
```

Create the database:

```bash
az postgres flexible-server db create \
  --resource-group rg-nutriguard-demo \
  --server-name pg-nutriguard-demo \
  --name nutriguard_db
```

Allow Azure services to reach the DB:

```bash
az postgres flexible-server firewall-rule create \
  --resource-group rg-nutriguard-demo \
  --server-name pg-nutriguard-demo \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

Database URL format:

```text
postgresql://nutriguard_admin:<url-safe-password>@pg-nutriguard-demo.postgres.database.azure.com:5432/nutriguard_db?sslmode=require
```

Set it locally for the deployment commands:

```bash
DATABASE_URL='postgresql://nutriguard_admin:<url-safe-password>@pg-nutriguard-demo.postgres.database.azure.com:5432/nutriguard_db?sslmode=require'
```

## 9. Prepare Connection Strings

Fetch Service Bus connection string:

```bash
SERVICE_BUS_CONNECTION_STRING=$(az servicebus namespace authorization-rule keys list \
  --resource-group rg-nutriguard-demo \
  --namespace-name sb-nutriguard-demo \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString \
  --output tsv)
```

Verify without printing the secret:

```bash
echo ${#SERVICE_BUS_CONNECTION_STRING}
```

Create internal API key:

```bash
INTERNAL_API_KEY=$(openssl rand -hex 32)
echo ${#INTERNAL_API_KEY}
```

Expected length:

```text
64
```

Create JWT signing secret for user authentication:

```bash
JWT_SECRET=$(openssl rand -hex 32)
echo ${#JWT_SECRET}
```

Expected length:

```text
64
```

Set Gemini key locally for the orchestrator create command:

```bash
GEMINI_API_KEY="<your-gemini-api-key>"
```

Do not paste this key into chat or commit it. If exposed, rotate it.

Optional: provide multiple Gemini keys as a comma-separated secret. This only increases effective quota when the keys belong to different Google projects or quota pools. Multiple keys from the same Google project usually share the same project quota.

```bash
GEMINI_API_KEYS="<key-1>,<key-2>,<key-3>"

az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --secrets gemini-api-keys="$GEMINI_API_KEYS"

az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --set-env-vars GEMINI_API_KEYS=secretref:gemini-api-keys
```

The orchestrator tries the next key only when Gemini returns a quota/rate-limit style error.

## 10. Build And Push Initial Images

Login to ACR:

```bash
az acr login --name acrnutriguarddemo
```

Build for Azure Container Apps using `linux/amd64`. This matters on Apple Silicon Macs, which otherwise build `linux/arm64` images.

```bash
docker build --platform linux/amd64 \
  -t acrnutriguarddemo.azurecr.io/nutriguard-backend:latest \
  services/backend-api

docker push acrnutriguarddemo.azurecr.io/nutriguard-backend:latest
```

The orchestrator uses a worker-specific Dockerfile:

```bash
docker build --platform linux/amd64 \
  -f services/ai-orchestrator/Dockerfile.worker \
  -t acrnutriguarddemo.azurecr.io/nutriguard-orchestrator:latest \
  services/ai-orchestrator

docker push acrnutriguarddemo.azurecr.io/nutriguard-orchestrator:latest
```

## 11. Create Backend Container App

```bash
az containerapp create \
  --resource-group rg-nutriguard-demo \
  --environment cae-nutriguard-demo \
  --name nutriguard-backend \
  --image acrnutriguarddemo.azurecr.io/nutriguard-backend:latest \
  --registry-server acrnutriguarddemo.azurecr.io \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --secrets \
    database-url="$DATABASE_URL" \
    service-bus-connection-string="$SERVICE_BUS_CONNECTION_STRING" \
    internal-api-key="$INTERNAL_API_KEY" \
    jwt-secret="$JWT_SECRET" \
  --env-vars \
    DATABASE_URL=secretref:database-url \
    SERVICE_BUS_CONNECTION_STRING=secretref:service-bus-connection-string \
    INTERNAL_API_KEY=secretref:internal-api-key \
    JWT_SECRET=secretref:jwt-secret \
    JWT_EXPIRES_MINUTES=1440 \
    APP_TIMEZONE=Asia/Kolkata \
    SERVICE_BUS_QUEUE_NAME=meal-events \
    EVENT_TRANSPORT=service_bus \
    ENABLE_OUTBOX_PUBLISHER=false \
    CORS_ORIGINS="*"
```

Get backend URL:

```bash
BACKEND_API_FQDN=$(az containerapp show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo "https://$BACKEND_API_FQDN"
```

Test health:

```bash
curl "https://$BACKEND_API_FQDN/health"
```

Expected:

```json
{"status":"ok","service":"backend-api","build_marker":"backend-ci-check-2026-07-01"}
```

If the backend already exists and JWT was added later, set the secret and env vars:

```bash
JWT_SECRET=$(openssl rand -hex 32)

az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --secrets jwt-secret="$JWT_SECRET"

az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --set-env-vars \
    JWT_SECRET=secretref:jwt-secret \
    JWT_EXPIRES_MINUTES=1440 \
    APP_TIMEZONE=Asia/Kolkata
```

The backend creates missing tables on startup with SQLAlchemy `create_all`, so new app tables such as `notifications` do not need a manual migration for this demo setup. For production, replace this with Alembic migrations before multiple developers or environments depend on schema history.

If a revision fails:

```bash
az containerapp revision list \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --query "[].{name:name, active:properties.active, healthState:properties.healthState, provisioningState:properties.provisioningState}" \
  --output table

az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --tail 120
```

## 12. Create AI Orchestrator Worker

Do not use `--ingress disabled`. In this Azure CLI version, omit ingress entirely for a worker.

Do not pass `--command python --args -m app.worker`; the CLI can parse `-m` as its own argument. The worker Dockerfile already contains the command.

```bash
az containerapp create \
  --resource-group rg-nutriguard-demo \
  --environment cae-nutriguard-demo \
  --name nutriguard-orchestrator \
  --image acrnutriguarddemo.azurecr.io/nutriguard-orchestrator:latest \
  --registry-server acrnutriguarddemo.azurecr.io \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --scale-rule-name servicebus-meal-events \
  --scale-rule-type azure-servicebus \
  --scale-rule-metadata queueName=meal-events namespace=sb-nutriguard-demo messageCount=1 \
  --scale-rule-auth connection=service-bus-connection-string \
  --secrets \
    service-bus-connection-string="$SERVICE_BUS_CONNECTION_STRING" \
    gemini-api-key="$GEMINI_API_KEY" \
    internal-api-key="$INTERNAL_API_KEY" \
  --env-vars \
    SERVICE_BUS_CONNECTION_STRING=secretref:service-bus-connection-string \
    SERVICE_BUS_QUEUE_NAME=meal-events \
    GEMINI_API_KEY=secretref:gemini-api-key \
    GEMINI_MODEL=gemini-3-flash-preview \
    BACKEND_API_URL="https://$BACKEND_API_FQDN" \
    INTERNAL_API_KEY=secretref:internal-api-key
```

Check revision:

```bash
az containerapp revision list \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --query "[].{name:name, active:properties.active, healthState:properties.healthState, provisioningState:properties.provisioningState}" \
  --output table
```

Because `min-replicas=0`, the worker may scale to zero until a queue message arrives.

View worker logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --tail 120
```

Smoke marker in logs:

```text
NutriGuard orchestrator worker started: orchestrator-ci-check-2026-07-01
```

## 13. Create Static Web App

Recommended path: create the Static Web App from Azure Portal.

Settings:

```text
Resource group: rg-nutriguard-demo
Name: nutriguard-web
Plan: Free
Source: GitHub
App location: frontend
API location: leave blank
Output location: dist
```

Azure creates a workflow like:

```text
.github/workflows/azure-static-web-apps-gentle-dune-0fa65b600.yml
```

That workflow must pass the backend URL to Vite:

```yaml
env:
  VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
```

GitHub secret value:

```text
VITE_API_BASE_URL=https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io
```

Do not rely on `frontend/.env` for Azure builds. Vite environment variables are build-time values, so Static Web Apps must receive `VITE_API_BASE_URL` in GitHub Actions.

## 14. GitHub Actions CI/CD

There are two workflows.

### Frontend Workflow

```text
.github/workflows/azure-static-web-apps-gentle-dune-0fa65b600.yml
```

Purpose:

```text
Automatically deploy frontend to Azure Static Web Apps on push to main.
```

Required secret:

```text
AZURE_STATIC_WEB_APPS_API_TOKEN_GENTLE_DUNE_0FA65B600
VITE_API_BASE_URL
```

The token secret is created by Azure Static Web Apps.

### Backend And Orchestrator Workflow

```text
.github/workflows/deploy.yml
```

Purpose:

```text
Build and deploy backend-api and ai-orchestrator containers.
```

It runs:

```text
manually via workflow_dispatch
automatically only when backend/orchestrator files change
```

Path trigger:

```text
services/backend-api/**
services/ai-orchestrator/**
.github/workflows/deploy.yml
```

Required secrets:

```text
AZURE_CREDENTIALS
AZURE_CONTAINER_REGISTRY=acrnutriguarddemo
AZURE_RESOURCE_GROUP=rg-nutriguard-demo
BACKEND_CONTAINER_APP_NAME=nutriguard-backend
ORCHESTRATOR_CONTAINER_APP_NAME=nutriguard-orchestrator
```

The backend Container App already stores app runtime secrets such as `DATABASE_URL`, `SERVICE_BUS_CONNECTION_STRING`, `INTERNAL_API_KEY`, and `JWT_SECRET`. The `deploy.yml` workflow only updates images, so those runtime secrets are preserved across image deployments.

Create `AZURE_CREDENTIALS`:

```bash
az ad sp create-for-rbac \
  --name sp-nutriguard-github \
  --role contributor \
  --scopes /subscriptions/2feb1844-57df-461f-8845-be07a8ccd703/resourceGroups/rg-nutriguard-demo \
  --sdk-auth
```

Copy the full JSON output into GitHub secret:

```text
AZURE_CREDENTIALS
```

Then run:

```text
GitHub -> Actions -> Deploy NutriGuard -> Run workflow
```

## 15. End-To-End Test

1. Open the Static Web App URL.
2. Confirm the frontend subtitle includes:

```text
AI meal timeline · Azure CI check
```

3. Create an account.
4. Create profile.
5. Log a meal.
6. Confirm the backend queues the message.
7. Confirm orchestrator worker wakes and saves the report.

Backend health:

```bash
curl "https://$BACKEND_API_FQDN/health"
```

Authentication smoke test:

```bash
curl -X POST "https://$BACKEND_API_FQDN/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"<email>","password":"<password>"}'
```

Expected response includes:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Service Bus queue status:

```bash
az servicebus queue show \
  --resource-group rg-nutriguard-demo \
  --namespace-name sb-nutriguard-demo \
  --name meal-events \
  --query "{active:countDetails.activeMessageCount, deadLetter:countDetails.deadLetterMessageCount}" \
  --output table
```

Backend logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --tail 120
```

Orchestrator logs:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --tail 120
```

## Troubleshooting

### `MissingSubscriptionRegistration`

Register the missing provider:

```bash
az provider register --namespace Microsoft.ContainerRegistry
```

Replace the namespace with the one from the error.

### Image OS/Arch Must Be `linux/amd64`

Rebuild with:

```bash
docker build --platform linux/amd64 ...
```

### Backend Logs Show Socket Connection To Postgres Host

Example:

```text
connection to server on socket "@pg-nutriguard-demo.postgres.database.azure.com/.s.PGSQL.5432" failed
```

Cause: malformed `DATABASE_URL`, usually from a password containing special URL characters.

Fix: reset to URL-safe password or URL-encode the password, update the Container App secret, then force a new revision.

```bash
az postgres flexible-server update \
  --resource-group rg-nutriguard-demo \
  --name pg-nutriguard-demo \
  --admin-password "NutriGuardDemo2026X"
```

Update secret:

```bash
DATABASE_URL="postgresql://nutriguard_admin:NutriGuardDemo2026X@pg-nutriguard-demo.postgres.database.azure.com:5432/nutriguard_db?sslmode=require"

az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --secrets database-url="$DATABASE_URL"
```

Force new revision:

```bash
az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --revision-suffix fixdb \
  --set-env-vars DATABASE_URL=secretref:database-url
```

### Browser Shows `ERR_CONNECTION_REFUSED`

This is not CORS. It usually means the frontend bundle is calling `localhost:8000` or an old ngrok backend.

Fix:

- Set GitHub secret `VITE_API_BASE_URL` to the Azure backend URL.
- Ensure Static Web Apps workflow passes `VITE_API_BASE_URL` in `env`.
- Re-run the Static Web Apps workflow.
- Hard refresh the browser.

### `azure/login` Fails In `Deploy NutriGuard`

Cause: `AZURE_CREDENTIALS` is missing or incomplete.

Fix: create the service principal and add the full JSON output as the GitHub secret.

### `--ingress disabled` Is Invalid

For the worker Container App, omit `--ingress` entirely.

### `unrecognized arguments: -m app.worker`

Use `services/ai-orchestrator/Dockerfile.worker`, which contains:

```dockerfile
CMD ["python", "-m", "app.worker"]
```

Do not pass `--command` or `--args` in `az containerapp create`.

## LangSmith Orchestrator Tracing

The AI orchestrator has optional LangSmith tracing around:

- Service Bus meal event handling
- `process_meal`
- Meal Analyzer Agent
- Health Risk Agent
- Report Agent

Tracing is off unless `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` are set. The app redacts `health_report_text` from trace inputs and truncates very long text values.

Enable LangSmith on the orchestrator container app:

```bash
LANGSMITH_API_KEY="<your-langsmith-api-key>"

az containerapp secret set \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --secrets langsmith-api-key="$LANGSMITH_API_KEY"

az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --set-env-vars \
    LANGSMITH_TRACING=true \
    LANGSMITH_API_KEY=secretref:langsmith-api-key \
    LANGSMITH_PROJECT=nutriguard-demo
```

Disable LangSmith when you want less observability traffic:

```bash
az containerapp update \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --set-env-vars LANGSMITH_TRACING=false
```

GitHub Actions image updates do not remove existing Container App env vars, so enabling this once in Azure is enough unless you recreate the container app.

## Useful Cost Commands

## Manual Azure Monitoring Toggle

Use this when you want to keep the bill low. Turning monitoring off stops new Container Apps console logs from being sent to Log Analytics. Old logs remain until workspace retention deletes them.

Check current monitoring destination:

```bash
az containerapp env show \
  --resource-group rg-nutriguard-demo \
  --name cae-nutriguard-demo \
  --query "properties.appLogsConfiguration.destination" \
  --output tsv
```

Turn monitoring off:

```bash
az containerapp env update \
  --resource-group rg-nutriguard-demo \
  --name cae-nutriguard-demo \
  --logs-destination none
```

Turn monitoring on again:

```bash
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group rg-nutriguard-demo \
  --workspace-name log-nutriguard-demo \
  --query customerId \
  --output tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group rg-nutriguard-demo \
  --workspace-name log-nutriguard-demo \
  --query primarySharedKey \
  --output tsv)

az containerapp env update \
  --resource-group rg-nutriguard-demo \
  --name cae-nutriguard-demo \
  --logs-destination log-analytics \
  --logs-workspace-id "$WORKSPACE_ID" \
  --logs-workspace-key "$WORKSPACE_KEY"
```

Keep Log Analytics retention at the minimum allowed value:

```bash
az monitor log-analytics workspace update \
  --resource-group rg-nutriguard-demo \
  --workspace-name log-nutriguard-demo \
  --retention-time 30
```

Quick log checks after turning monitoring on:

```bash
az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-backend \
  --tail 80

az containerapp logs show \
  --resource-group rg-nutriguard-demo \
  --name nutriguard-orchestrator \
  --tail 80
```

Stop PostgreSQL:

```bash
az postgres flexible-server stop \
  --resource-group rg-nutriguard-demo \
  --name pg-nutriguard-demo
```

Start PostgreSQL:

```bash
az postgres flexible-server start \
  --resource-group rg-nutriguard-demo \
  --name pg-nutriguard-demo
```

Delete all demo resources:

```bash
az group delete --name rg-nutriguard-demo
```
