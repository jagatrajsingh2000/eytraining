# Day 14 - Task 1: Hallucination Detector

This task uses the OpenAI ChatGPT API to evaluate whether an answer is grounded in a trusted source context.

## What It Detects

- Intrinsic hallucination: answer contradicts the source.
- Extrinsic hallucination: answer adds unsupported facts.
- Closed-domain violation: answer goes outside the allowed scope.
- Factuality drift: answer uses outdated or false information.
- Cascading hallucination: answer repeats an earlier wrong assumption.
- FactScore-like precision.
- RAG groundedness.
- SelfCheckGPT-like consistency.

## Setup

Create `day14/task1/.env`:

```env
OPENAI_API_KEY=your_chatgpt_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Install dependencies from the repo root:

```powershell
pip install -r requirements.txt
```

## Run

From `day14/task1`:

```powershell
python hallucination_detector.py
```

The script runs a sample Azure AI Search chunking example and prints a structured JSON hallucination report.
