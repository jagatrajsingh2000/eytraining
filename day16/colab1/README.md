# 🧪 Day 16 — Build a Financial RAG System

## Overview

Build an end-to-end Retrieval-Augmented Generation (RAG) pipeline that ingests SEC 10-K filings (Apple fiscal 2023), embeds them with HuggingFace, stores vectors in FAISS, generates answers using Azure OpenAI GPT-4o, and evaluates quality with RAGAS metrics.

## Industry Scenario: FinSight AI

> You are an engineer at a Tier-1 investment bank building **FinSight**, an AI Research Analyst Assistant.
> Analysts need to query annual reports in natural language.
> **Target:** faithfulness ≥ 0.85, latency < 3s, cost < $0.002/query.

---

## What's Inside

```
day16/
└── colab1/
    ├── financial_rag_system.ipynb   # Original Colab notebook
    ├── main.py                      # Standalone Python script (converted from notebook)
    └── README.md                    # This file
```

---

## Pipeline Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  SEC 10-K    │───▶│   Chunking   │───▶│  Embedding   │───▶│    FAISS     │───▶│  Azure GPT-4o│
│  Documents   │    │ (Recursive)  │    │ (MiniLM-L6)  │    │  Vector DB   │    │  Generation  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                                       │
                                                                                       ▼
                                                                               ┌──────────────┐
                                                                               │    RAGAS      │
                                                                               │  Evaluation   │
                                                                               └──────────────┘
```

### Steps

| Step | Description |
|------|-------------|
| **Step 1** | Load credentials from `.env` (Azure OpenAI endpoint, key, deployment) |
| **Step 2** | Load 3 sample Apple 10-K excerpts (Risk, Products, Liquidity) |
| **Step 3** | Chunk documents using `RecursiveCharacterTextSplitter` (512 chars, 64 overlap) |
| **Step 4** | Embed chunks with HuggingFace `all-MiniLM-L6-v2` (384-dim vectors) |
| **Step 5** | Build FAISS vector index with MMR (Maximal Marginal Relevance) retrieval |
| **Step 6** | Build a RAG chain with Azure OpenAI GPT-4o and a FinSight analyst prompt |
| **Step 7** | Run 5 test queries and measure latency per query |
| **Step 8** | Evaluate with RAGAS (faithfulness, answer relevancy, context recall, context precision) |
| **Step 9** | Chunk size experiment — compare 256 vs 512 vs 1024 chunk sizes |

---

## Setup

### 1. Install Dependencies

```bash
pip install langchain langchain-community langchain-openai \
    faiss-cpu sentence-transformers openai \
    ragas datasets pypdf tiktoken \
    python-dotenv tqdm rich pandas
```

### 2. Configure `.env`

Make sure your project-level `.env` file (in `Ey_training_genai/`) contains:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### 3. Run

```bash
# From the project root
python day16/colab1/main.py
```

Or open `financial_rag_system.ipynb` in Google Colab and add your keys via the Secrets sidebar.

---

## Key Concepts

### Chunking Strategy
- **RecursiveCharacterTextSplitter** splits on `\n\n`, `\n`, `. `, then spaces.
- Default: 512-character chunks with 64-character overlap.
- Chunk size is one of the most impactful RAG design decisions — smaller chunks improve precision but can miss context.

### Embedding Model
- **all-MiniLM-L6-v2**: 80M parameters, 384 dimensions, fast and free.
- Good for financial text but may struggle with very domain-specific jargon.

### Retrieval: MMR
- **Maximal Marginal Relevance** balances relevance and diversity.
- `lambda_mult=0.7` means 70% relevance, 30% diversity.
- Fetches 10 candidates, returns top 4.

### RAGAS Metrics

| Metric | What it measures |
|--------|------------------|
| **Faithfulness** | Are answer claims grounded in retrieved context? |
| **Answer Relevancy** | Does the answer address the question? |
| **Context Recall** | Does retrieved context cover what's needed? |
| **Context Precision** | Is the context precise (minimal noise)? |

---

## Extension Task — Hybrid Retrieval + Re-Ranker

**Goal:** Improve retrieval precision by combining dense vectors with BM25 sparse retrieval, then re-rank with a cross-encoder.

1. Install `rank_bm25`
2. Build a `BM25Retriever` from the same chunks
3. Use `EnsembleRetriever` with 60% dense + 40% BM25 weights
4. Add cross-encoder re-ranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`
5. Re-run RAGAS — target faithfulness > 0.88
6. Plot faithfulness vs latency for dense vs hybrid vs hybrid+rerank

---

## Reflection Questions

1. What faithfulness score did you achieve? How does it compare to the FinSight target of ≥ 0.85?
2. Which chunk size gave the best trade-off between faithfulness and latency?
3. What types of queries failed? Why might the RAG pipeline struggle with them?
4. How would you adapt this pipeline for 10,000 PDFs ingested daily?
