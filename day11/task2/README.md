# Day 11 Task 2: Gemini With OpenAI SDK And FAISS Retrieval Bot

This folder contains two examples:

- `main.py`: Gemini chat call using the OpenAI SDK and a prompt layer.
- `retrival_bot_fss.py`: Retrieval QA over a policy PDF using LangChain, FAISS, and Gemini through OpenAI-compatible clients.

## Install

Install the packages needed for the retrieval bot:

```bash
.venv/bin/pip install langchain langchain-community langchain-openai faiss-cpu pypdf
```

These packages are also listed in `Ey_training_genai/requirements.txt`.

## Why Gemini Works With The GPT/OpenAI SDK

Gemini provides an OpenAI-compatible endpoint:

```text
https://generativelanguage.googleapis.com/v1beta/openai/
```

That means OpenAI-compatible clients can keep the usual request format, while `base_url` routes requests to Gemini and `api_key` uses a Gemini API key.

## Run Prompt Layer Example

From the repository root:

```bash
.venv/bin/python Ey_training_genai/day11/task2/main.py
```

## Run Retrieval Bot

Place a PDF policy document at:

```text
Ey_training_genai/day11/task2/policy_document.pdf
```

Then run:

```bash
.venv/bin/python Ey_training_genai/day11/task2/retrival_bot_fss.py \
  --pdf Ey_training_genai/day11/task2/policy_document.pdf \
  --question "What is the policy regarding remote work reimbursement?"
```

For local testing without using Gemini quota:

```bash
.venv/bin/python Ey_training_genai/day11/task2/retrival_bot_fss.py --mock
```

`--mock` still loads the PDF, splits it, builds a FAISS index, and retrieves relevant chunks. It skips Gemini embeddings and chat completion.

## Retrieval Bot Flow

`retrival_bot_fss.py` does the following:

1. Loads the PDF using `PyPDFLoader`.
2. Splits pages into chunks using `RecursiveCharacterTextSplitter`.
3. Creates embeddings with `OpenAIEmbeddings` pointed at Gemini.
4. Stores chunks in a FAISS vectorstore.
5. Retrieves the top 3 relevant chunks.
6. Answers the question using `ChatOpenAI` pointed at Gemini.

## API Key

Before running, replace this value in the Python files:

```python
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"
```

Avoid committing a real API key to GitHub.
