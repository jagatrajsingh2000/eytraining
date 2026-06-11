# Day 11 Task 3: LangChain Prompt Studio Core Tasks

This task implements core tasks `1`, `3`, and `4`.

## Core Tasks Covered

1. Build a zero-shot + few-shot summarisation chain using LangChain `PromptTemplate` for 3 earnings call snippets.
3. Build a 5-class ticket classifier: `Billing`, `Tech`, `Refund`, `General`, `Escalate`.
4. Log all prompts to a PromptLayer-style log file and capture ROUGE-L scores for summarisation.

## Why Gemini Works With The GPT/OpenAI SDK

The code uses the OpenAI Python SDK, but points it to Gemini:

```python
OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
```

This works because Gemini provides an OpenAI-compatible endpoint. The SDK sends the normal `chat.completions` request format, while the `base_url` routes the request to Gemini and the Gemini API key authenticates it.

## Run With Gemini

From the repository root:

```bash
.venv/bin/python Ey_training_genai/day11/task3/main.py
```

## Run Offline For Testing

Use mock mode when you want to generate the output files without making an API call:

```bash
.venv/bin/python Ey_training_genai/day11/task3/main.py --mock
```

## Handling 503 High Demand Errors

If Gemini returns:

```text
503 UNAVAILABLE: This model is currently experiencing high demand
```

the script retries temporary API failures for:

```text
gemini-3.5-flash
```

Use `--mock` if you only need to verify the assignment files while the live model is overloaded.

## Outputs

All outputs are written to:

```text
Ey_training_genai/day11/task3/output/
```

Generated files:

- `summarisation_results.csv`: zero-shot and few-shot summaries with ROUGE-L scores.
- `ticket_classifier_results.csv`: ticket predictions vs ground-truth labels.
- `promptlayer_log.jsonl`: every prompt and response logged in PromptLayer-style JSONL format.
- `task3_report.json`: summary of completed tasks, average ROUGE-L, and classifier accuracy.

## Prompt Templates

The script uses LangChain:

```python
from langchain_core.prompts import PromptTemplate
```

Prompt templates included:

- `create_zero_shot_summary_prompt`
- `create_few_shot_summary_prompt`
- `create_ticket_classifier_prompt`

## ROUGE-L

ROUGE-L is calculated locally using longest common subsequence between the model summary and the reference summary. This avoids adding another dependency.
