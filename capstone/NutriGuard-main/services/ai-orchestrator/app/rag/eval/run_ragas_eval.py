import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


DATASET_PATH = Path(__file__).resolve().parent / "ragas_dataset.jsonl"
ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[3]
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from app.rag.retriever import retrieve_nutrition_context


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def simple_answer(question: str, contexts: list[dict[str, Any]]) -> str:
    context_text = " ".join(item.get("content", "") for item in contexts[:3])
    return f"{question} {context_text}".strip()


def retrieval_summary(cases: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    rows = []
    for case in cases:
        contexts = retrieve_nutrition_context(case["input_state"], limit=limit)
        retrieved_ids = [item["id"] for item in contexts]
        expected_ids = case.get("expected_context_ids", [])
        hits = [item_id for item_id in expected_ids if item_id in retrieved_ids]
        hit_count = len(hits)
        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "retrieved_ids": retrieved_ids,
                "expected_context_ids": expected_ids,
                "hit_rate": round(hit_count / len(expected_ids), 2) if expected_ids else 0,
                "context_precision": round(hit_count / len(retrieved_ids), 2) if retrieved_ids else 0,
                "hits": hits,
                "contexts": contexts,
            }
        )
    return rows


def build_judge_llm(provider: str, model: str | None):
    if provider == "openai":
        return None

    if provider == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("Claude RAGAS evaluation requires ANTHROPIC_API_KEY.")
        try:
            from langchain_anthropic import ChatAnthropic
            from ragas.llms import LangchainLLMWrapper
        except ImportError as exc:
            raise RuntimeError(
                "Claude RAGAS evaluation requires langchain-anthropic. "
                "Run: pip install langchain-anthropic"
            ) from exc
        return LangchainLLMWrapper(
            ChatAnthropic(
                model=model or "claude-3-5-sonnet-latest",
                temperature=0,
            )
        )

    raise RuntimeError(f"Unsupported judge provider: {provider}")


def run_ragas(rows: list[dict[str, Any]], cases: list[dict[str, Any]], judge_provider: str, judge_model: str | None):
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import context_precision, context_recall, faithfulness
    except ImportError as exc:
        raise RuntimeError(
            "RAGAS dependencies are not installed. Run: "
            "pip install -r services/ai-orchestrator/requirements-ragas.txt"
        ) from exc

    case_by_id = {case["id"]: case for case in cases}
    dataset = Dataset.from_list(
        [
            {
                "question": row["question"],
                "answer": simple_answer(row["question"], row["contexts"]),
                "contexts": [item.get("content", "") for item in row["contexts"]],
                "ground_truth": case_by_id[row["id"]]["reference"],
            }
            for row in rows
        ]
    )
    judge_llm = build_judge_llm(judge_provider, judge_model)

    return evaluate(
        dataset,
        metrics=[
            faithfulness,
            context_precision,
            context_recall,
        ],
        llm=judge_llm,
    )


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0


def extract_ragas_metrics(ragas_result: Any) -> dict[str, float]:
    if ragas_result is None:
        return {}

    try:
        frame = ragas_result.to_pandas()
        return {
            key: round(float(value), 2)
            for key, value in frame.mean(numeric_only=True).to_dict().items()
            if value == value
        }
    except Exception:
        pass

    scores = getattr(ragas_result, "scores", None)
    if isinstance(scores, list):
        keys = sorted({key for score in scores if isinstance(score, dict) for key in score})
        return {
            key: average([float(score[key]) for score in scores if isinstance(score, dict) and isinstance(score.get(key), (int, float))])
            for key in keys
        }

    if isinstance(ragas_result, dict):
        return {
            key: round(float(value), 2)
            for key, value in ragas_result.items()
            if isinstance(value, (int, float))
        }

    return {}


def build_result_payload(
    rows: list[dict[str, Any]],
    average_hit_rate: float,
    ragas_result: Any = None,
    judge_provider: str | None = None,
    judge_model: str | None = None,
) -> dict[str, Any]:
    retrieval_metrics = {
        "context_recall": round(average_hit_rate, 2),
        "context_precision": average([row["context_precision"] for row in rows]),
        "average_contexts_retrieved": average([len(row["retrieved_ids"]) for row in rows]),
    }
    payload = {
        "source": "local_ragas",
        "average_hit_rate": round(average_hit_rate, 2),
        "total_cases": len(rows),
        "passed_cases": sum(1 for row in rows if row["hit_rate"] >= 1),
        "retrieval_metrics": retrieval_metrics,
        "ragas_metrics": extract_ragas_metrics(ragas_result),
        "judge": {
            "provider": judge_provider,
            "model": judge_model,
        },
        "cases": rows,
    }
    if ragas_result is not None:
        payload["ragas"] = str(ragas_result)
    return payload


def publish_result(payload: dict[str, Any], backend_url: str, internal_api_key: str):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError(
            "Publishing RAG eval results requires requests. Install orchestrator dependencies first."
        ) from exc

    response = requests.post(
        f"{backend_url.rstrip('/')}/internal/rag-eval-results",
        json=payload,
        headers={"x-internal-api-key": internal_api_key},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Evaluate NutriGuard local RAG retrieval quality.")
    parser.add_argument("--dataset", default=str(DATASET_PATH), help="Path to JSONL eval cases.")
    parser.add_argument("--limit", type=int, default=6, help="Number of contexts to retrieve per case.")
    parser.add_argument("--ragas", action="store_true", help="Run RAGAS metrics in addition to retrieval hit-rate.")
    parser.add_argument("--judge-provider", choices=["openai", "claude"], default=os.getenv("RAGAS_JUDGE_PROVIDER", "openai"))
    parser.add_argument("--judge-model", default=os.getenv("RAGAS_JUDGE_MODEL"))
    parser.add_argument("--publish", action="store_true", help="Publish latest result to backend admin dashboard.")
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_API_URL", "http://localhost:8000"))
    parser.add_argument("--internal-api-key", default=os.getenv("INTERNAL_API_KEY", "dev-internal-key"))
    args = parser.parse_args()

    cases = load_cases(Path(args.dataset))
    rows = retrieval_summary(cases, args.limit)
    average_hit_rate = sum(row["hit_rate"] for row in rows) / len(rows) if rows else 0
    ragas_result = None

    if args.ragas:
        ragas_result = run_ragas(rows, cases, args.judge_provider, args.judge_model)

    payload = build_result_payload(rows, average_hit_rate, ragas_result, args.judge_provider, args.judge_model)
    print(json.dumps(payload, indent=2))

    if args.publish:
        print(json.dumps({"published": publish_result(payload, args.backend_url, args.internal_api_key)}, indent=2))


if __name__ == "__main__":
    main()
