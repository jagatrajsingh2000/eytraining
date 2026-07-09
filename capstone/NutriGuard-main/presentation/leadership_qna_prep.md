# NutriGuard AI - Leadership Q&A Prep

Use these as simple answers with enough technical detail. Start with the short answer, then add the technical detail only if they ask deeper.

## 30-Second Project Summary

NutriGuard AI is a personalized nutrition guidance app. A user creates a health profile, logs meals, and receives a day-level nutrition report that checks meals against goals, deficiencies, supplements, and timing.

Technically, it is a React frontend, FastAPI backend, PostgreSQL database, async meal-processing pipeline, LangGraph multi-agent orchestrator, local RAG knowledge retrieval, Gemini/OpenAI fallback, and an admin observability dashboard.

The key point: this is not just one prompt behind a UI. It is a small production-style AI system with async processing, safety guardrails, fallbacks, testing, RAG evaluation, and monitoring.

## Simple Architecture

User logs a meal in React.

The FastAPI backend saves the meal in PostgreSQL and creates a processing event.

In local development, the event is picked up from the outbox table. In Azure production, the event can go through Azure Service Bus.

The AI orchestrator receives the meal plus the user's full-day meal timeline and health profile.

LangGraph runs three agents:

1. Meal Analyzer Agent: extracts foods, drinks, protein sources, carbs, and issues.
2. Health Risk Agent: checks the meal against health context, supplements, deficiencies, timing, and RAG knowledge.
3. Report Agent: creates a simple user-facing report with suggestions and safety notes.

The result is saved back into PostgreSQL as risk flags, daily reports, metrics, and token/cost events.

## Questions Leadership May Ask

### 1. What problem are we solving?

Most nutrition apps only track food. They do not understand the user's medical context, supplements, deficiencies, or meal timing.

NutriGuard adds context-aware reasoning. For example, if a user has iron deficiency and logs tea near an iron supplement, the system can flag that timing may matter.

Technical detail: the system sends the user's profile, uploaded health report text, previous meal context, and full-day meal timeline to the AI workflow.

### 2. Why does this need AI?

The input is messy natural language. Users may write "poha, tea, iron tablet" instead of structured nutrition fields.

AI helps extract structured meal data and explain recommendations in simple language.

But we do not depend blindly on AI. We also use deterministic fallback rules for known cases like low protein, tea near iron, and calcium near iron.

### 3. Why LangGraph instead of one big prompt?

One big prompt is harder to debug and harder to monitor.

LangGraph lets us split the workflow into steps:

- analyze meal
- detect risks
- write report

Each step has a clear responsibility, latency metric, fallback behavior, and output. If something goes wrong, we can see which agent failed.

### 4. Why React instead of Streamlit?

Streamlit is great for prototypes, but NutriGuard needs a real user experience: login, profile setup, meal logging, history, reports, notifications, responsive layout, and admin dashboards.

React gives us production-style frontend structure and better control over routing, state, forms, mobile layout, and deployment to Azure Static Web Apps.

### 5. Why Gemini and OpenAI both?

Gemini is used as the primary provider for cost-effective generation.

OpenAI is used as a fallback and as the judge for optional RAGAS evaluation.

If Gemini fails, the provider chain tries OpenAI. If both fail or output cannot be parsed, the app falls back to rule-based logic so the user still gets useful guidance.

Technical detail: the provider chain records events like `gemini_fallback`, `openai_answer`, `openai_fallback`, `rule_fallback`, and token usage.

### 6. What is RAG in this project?

RAG means the AI does not answer only from the model's memory. It retrieves relevant nutrition guidance first, then uses that context while generating the answer.

In this project, the knowledge base is stored as curated JSON files. Each knowledge entry has tags, topic, content, source, evidence level, and safety note.

Those entries act as our chunks.

The retriever builds query tokens from the meal, goals, diet type, health conditions, deficiencies, supplements, meal analysis, and day timeline. It scores knowledge entries by tag and keyword overlap, then passes the top chunks to the health-risk and report agents.

### 7. How did we handle chunking?

We are not using fixed 500-character or 1,000-character chunks yet.

Our current chunking is semantic and curated: one focused JSON knowledge item equals one chunk.

Example of a good chunk: vegetarian protein options for breakfast.

Example of a bad chunk: all nutrition advice in one large document.

Why this matters:

- large chunks preserve context but add noise and cost
- tiny chunks are focused but may lose meaning
- focused semantic chunks are easier to evaluate and debug

Next improvement: split broad entries, improve tags, tune top K, and compare with vector embeddings.

### 8. How do we evaluate RAG quality?

We evaluate retrieval separately from generation.

Local metrics:

- Recall@K: did the expected evidence appear in the top K retrieved chunks?
- Precision@K: how many retrieved chunks were actually relevant?
- Average contexts retrieved: how much context we send to the model.

Optional RAGAS metrics:

- faithfulness: is the answer grounded in the retrieved context?
- context precision: was the retrieved context useful?
- context recall: did retrieved context cover the expected answer?

OpenAI can act as the RAGAS judge with `gpt-4o-mini`.

The result can be published to the admin dashboard through `/internal/rag-eval-results`.

### 9. What is observability here?

Observability means we can see what the system is doing after deployment.

NutriGuard tracks:

- API request latency
- p95 latency and max latency
- agent latency by stage
- failed reports
- report completion count
- Gemini/OpenAI/rule fallback count
- token usage and estimated cost
- latest load-test result
- latest RAG/RAGAS quality result
- feedback and notification metrics

Technical detail: the backend stores metric events in PostgreSQL, and the admin page reads them from `/admin/metrics`.

### 10. Why is observability important for this project?

AI systems can fail silently.

A normal API may return 200, but the background AI worker may be slow, the provider may be failing, or reports may not complete.

Because NutriGuard is health-related, invisible failures are risky. We need to know whether the API, queue, LLM provider, agent pipeline, or report-writing step is the bottleneck.

### 11. How do we trace one meal request?

Each meal gets a `trace_id`.

That trace connects the request from:

- frontend meal submission
- backend meal record
- outbox or Service Bus event
- AI orchestrator
- LangGraph agents
- saved report and metrics

This makes debugging much easier because we can follow one meal through the full distributed workflow.

### 12. Why async processing?

AI calls can take several seconds. We do not want the user request to block until all agents finish.

So the backend quickly saves the meal and queues processing. The frontend can poll or refresh for the final report.

This gives a better user experience and makes the system more resilient under load.

### 13. Why Azure Service Bus?

Service Bus decouples the backend from the AI worker.

The backend can accept meal logs quickly, while the worker processes them separately.

If AI processing is slow, the queue absorbs the work instead of making the frontend wait.

Local development uses a database outbox table. Production can use Azure Service Bus for a more cloud-native queue.

### 14. Why Azure hosting?

Azure gives managed services that fit this architecture:

- Static Web Apps for React
- Container Apps for backend and worker
- PostgreSQL Flexible Server for database
- Service Bus for async queue
- Container Registry for Docker images
- Log Analytics for cloud logs
- GitHub Actions for CI/CD

It lets us deploy without managing virtual machines.

### 15. What does serverless mean here?

Serverless does not mean there is no server. It means we do not manage the server directly.

Azure Container Apps can scale containerized services and keep infrastructure work low.

For a demo or early product, this is useful because we can run small, control cost, and scale later.

### 16. How do we protect user data?

The app uses JWT authentication. Users can only access their own data through `require_user_id`.

Passwords are hashed with PBKDF2 SHA-256 and a salt.

Internal endpoints require an internal API key.

Important honest note: this is demo-stage security, not clinical-grade compliance. For a real healthcare product, we would add stronger secrets management, audit logs, encryption review, role-based access control, and compliance work.

### 17. Is this giving medical advice?

No. The system is designed to stay nutrition-focused and conservative.

Prompts explicitly say:

- do not diagnose
- do not prescribe
- do not change supplement dosage
- include safety notes
- advise following clinician guidance

It can flag nutrition timing concerns, but it is not a doctor.

### 18. What tests do we have?

Backend unit tests cover:

- admin metrics aggregation
- API latency calculations
- LLM fallback metrics
- RAG/RAGAS dashboard serialization
- admin access guard
- notification timezone logic
- password hashing and verification
- health profile normalization

Latest documented result: 13 tests passed in 0.51 seconds.

There are also stress/load test scripts that exercise signup, login, profile creation, meal logging, report polling, and daily report endpoints.

### 19. What are the biggest current limitations?

The current RAG retriever is keyword/tag based, not embedding-based vector search.

The knowledge base is small and curated.

The system needs more evaluation cases before being trusted broadly.

The local outbox publisher is enough for development, but production should use Service Bus and stronger retry/dead-letter handling.

Security and compliance are demo-stage, not healthcare-production ready.

The admin dashboard is DB-backed and useful for demos, but large-scale production would also need centralized logs, alerting, and dashboards in Azure Monitor or another observability platform.

### 20. What would we build next?

Near-term improvements:

- add more RAG evaluation cases
- improve chunk tags and split broad chunks
- test vector-based retrieval
- add dead-letter queue handling
- add stronger retry policies
- add alerts for failed reports, high latency, and provider fallback spikes
- move secrets to Azure Key Vault
- add more frontend E2E tests
- add better clinical disclaimer and safety review

## One Strong Closing Answer

NutriGuard proves that a personalized nutrition app can be built as a real AI system, not only a chatbot. The value is the combination of user-friendly meal logging, health-context reasoning, RAG grounding, multi-agent orchestration, async cloud architecture, provider fallback, and observability.

The current version is demo-stage, but the architecture points in the right direction for production: decoupled services, measurable AI quality, monitored latency and cost, and conservative safety guardrails.

