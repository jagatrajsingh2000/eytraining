# Day 13 Task 2: RAG Metrics by Query

This task reuses the Day 12 Collab 1 idea of local retrieval over a small hardcoded corpus, then evaluates each query with:

- Token count
- Latency
- Answer relevance
- Faithfulness
- Context precision

The script runs fully offline and does not need API keys.

## Run

From the repository root:

```bash
.venv/bin/python Ey_training_genai/day13/task2/main.py
```

## Metrics

| Metric | What it means |
| --- | --- |
| Token count | Total input/context tokens plus output answer tokens |
| Latency | Embedding latency, retrieval latency, generation latency, and total latency |
| Answer relevance | Similarity between the user query and generated answer |
| Faithfulness | How much of the answer is supported by retrieved context |
| Context precision | How many retrieved chunks are actually relevant to the query/reference answer |

## Outputs

All outputs are saved to:

```text
Ey_training_genai/day13/task2/output/
```

Files generated:

- `rag_metrics_by_query.csv`
- `rag_metrics_by_query.json`
- `rag_metrics_report.md`
- `plots/all_queries_summary.png`
- `plots/q1_metrics.png`
- `plots/q2_metrics.png`
- `plots/q3_metrics.png`
- `plots/q4_metrics.png`
- `plots/q5_metrics.png`
- `plots/q6_metrics.png`

Each query gets its own graph showing:

- total tokens
- total latency
- answer relevance
- faithfulness
- context precision
