# Day 12 - Collab 1: Indexing & Multi-DB Retrieval Showdown

This lab compares retrieval across FAISS, Pinecone, and Azure AI Search using the same local corpus and embeddings.

## What This Does

1. Loads hardcoded Wikipedia-style article summaries.
2. Splits articles into chunks.
3. Creates local embeddings with `HashingVectorizer`.
4. Builds a local FAISS index.
5. Optionally uploads/query vectors in Pinecone.
6. Optionally indexes/searches documents in Azure AI Search.
7. Optionally runs Cohere rerank setup.
8. Prints p50/p95 latency and Hit@5 summary.

## Why Hardcoded Articles?

The original lab expected live Wikipedia access, but this environment blocks outbound Wikipedia requests. The corpus is hardcoded so the lab runs consistently without network access for data loading.

## Required Setup

Install dependencies from the repo root:

```powershell
pip install -r requirements.txt
```

Create or update `day12/collab_1/.env`:

```env
PINECONE_API_KEY=your_pinecone_key
GROQ_API_KEY=your_groq_key
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your_azure_search_admin_key
AZURE_SEARCH_INDEX_NAME=rag-showdown
COHERE_API_KEY=your_cohere_key
```

Only Pinecone and Azure are needed for their respective cloud comparisons. FAISS runs locally.

## Run Commands


Run full comparison:

```powershell
python main.py
```


## Outputs

- Console latency summary with p50, p95, mean latency, and Hit@5.
- `latency_benchmark.png` when plotting is enabled.

## Notes

- `.env` is ignored by git and should not be committed.
- The Groq key is loaded but not used for embeddings because this lab needs vector embeddings; the script uses local deterministic embeddings.
- Azure endpoint and Azure key must belong to the same Azure AI Search service.
