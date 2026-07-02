# NutriGuard Local RAG

NutriGuard currently uses a lightweight local RAG system:

- Knowledge lives in `app/rag/knowledge/*.json`.
- Retrieval uses keyword/tag scoring in `app/rag/retriever.py`.
- Retrieved context is passed into the Health Risk Agent and Report Agent.
- Ayurveda entries must use `evidence_level: "traditional_ayurveda"` so agents phrase them as traditional context, not clinical claims.

## Add Knowledge

Add JSON items with this shape:

```json
{
  "id": "protein_vegetarian_001",
  "topic": "protein_recommendation",
  "goals": ["muscle_gain"],
  "diet_types": ["vegetarian"],
  "conditions": [],
  "tags": ["protein", "paneer", "tofu"],
  "content": "Recommendation text.",
  "source": "Source label",
  "evidence_level": "nutrition_guideline",
  "safety": "Safety note."
}
```

## Evaluate Retrieval

Run the lightweight retrieval check:

```bash
cd services/ai-orchestrator
python3 app/rag/eval/run_ragas_eval.py
```

Optional RAGAS check:

```bash
pip install -r requirements-ragas.txt
python3 app/rag/eval/run_ragas_eval.py --ragas
```

RAGAS may require evaluator LLM credentials depending on the metrics/configuration you use.

