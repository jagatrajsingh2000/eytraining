# RAGAS Evaluation With OpenAI

NutriGuard can run local RAG retrieval checks and optional RAGAS judge metrics using OpenAI as the evaluator.

## Required Environment

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export RAGAS_JUDGE_PROVIDER=openai
export RAGAS_JUDGE_MODEL=gpt-4o-mini
```

Install evaluation dependencies:

```bash
cd services/ai-orchestrator
../../.venv/bin/python -m pip install -r requirements-ragas.txt
```

## Run Retrieval-Only Evaluation

This does not call OpenAI. It checks whether the local retriever returns the expected knowledge snippets.

```bash
cd services/ai-orchestrator
../../.venv/bin/python app/rag/eval/run_ragas_eval.py --limit 3
```

## Run RAGAS With OpenAI

This calls OpenAI through RAGAS to calculate judge-based metrics such as faithfulness, context precision, and context recall.

```bash
cd services/ai-orchestrator
../../.venv/bin/python app/rag/eval/run_ragas_eval.py \
  --ragas \
  --judge-provider openai \
  --judge-model gpt-4o-mini
```

## Publish To Admin Dashboard

```bash
cd services/ai-orchestrator
../../.venv/bin/python app/rag/eval/run_ragas_eval.py \
  --ragas \
  --judge-provider openai \
  --judge-model gpt-4o-mini \
  --publish \
  --backend-url "https://nutriguard-backend.livelypebble-65a075a7.centralindia.azurecontainerapps.io" \
  --internal-api-key "$INTERNAL_API_KEY"
```

The admin dashboard reads the latest published run from the backend `rag_eval_runs` table.
