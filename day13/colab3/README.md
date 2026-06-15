# 🏦 FinSight AI — LLM Eval Pipeline (Lab 3)

Automated quality gates for Groq-powered credit risk memo generation in a CI/CD environment.

## Architecture

```
.
├── src/
│   ├── eval_harness.py      # Core eval logic (Groq API, hallucination detection, BERTScore)
│   ├── test_cases.py        # 20 FinSight credit memo test cases (easy to adversarial)
│   └── run_ci_eval.py       # CI entrypoint (called by GitHub Actions, outputs csv/json)
├── tests/
│   └── test_eval_gates.py   # pytest unit + integration tests
├── results/                 # Evaluation results output (csv, json, gitignored)
├── .github/workflows/
│   └── llm-eval.yml         # GitHub Actions pipeline workflow
└── requirements.txt         # Package dependencies
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure your Groq API Key is configured in your `.env` file or environment variables:
   ```bash
   export GROQ_API_KEY=gsk_...
   ```
   *(Note: You can also use `XAI_API_KEY` as a fallback environment key).*

3. Run evals locally:
   ```bash
   python src/run_ci_eval.py
   ```

4. Run unit tests:
   ```bash
   pytest tests/ -v
   ```

## CI/CD Quality Gate (FinSight Production Constraints)

A pull request is blocked from merging if no model satisfies all four quality constraints:

| Constraint | Threshold | Description |
|---|---|---|
| **Hallucination rate** | `< 1%` | Fabricated numeric values not in the source text |
| **BERTScore F1** | `≥ 0.88` | High semantic similarity with context metrics |
| **Latency p95** | `< 3s` | High percentile latency threshold |
| **Cost per memo** | `< $0.02` | Financial budget limit per generation |

## CI Behavior

| Event | Trigger | Models | Cases |
|---|---|---|---|
| **Pull Request** | On PR to `main` | `llama-3.3-70b` + `llama-3.1-8b` | 5 easy (smoke) |
| **Push** | On commit to `main` | `llama-3.3-70b` + `llama-3.1-8b` | 5 easy (smoke) |
| **Nightly (02:00 UTC)** | Schedule | All 4 Groq models | All 20 |
| **Manual** | `workflow_dispatch` | Configurable | Configurable |
