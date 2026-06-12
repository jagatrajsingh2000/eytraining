# Day 12 - Collab 2: Azure AI Search RAG with Anthropic

This collab builds a small RAG pipeline using local embeddings, Azure AI Search for retrieval, and Anthropic Claude for answer generation. It does not use GPT/OpenAI models.

## What This Does

1. Loads a hardcoded mini knowledge base.
2. Creates local embeddings with `HashingVectorizer`.
3. Creates or updates an Azure AI Search vector index.
4. Uploads documents and local vectors into Azure AI Search.
5. Retrieves the top matching chunks from Azure AI Search.
6. Sends the retrieved context to Anthropic Claude for the final answer.

## `.env` Keys

Create or update `day12/collab_2/.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=claude-3-5-haiku-latest
LOCAL_EMBEDDING_DIM=1536
TOP_K=4
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=eysearch
AZURE_API_KEY=your_azure_search_admin_key
AZURE_SEARCH_API_KEY=your_azure_search_admin_key
```

Key meanings:

- `ANTHROPIC_API_KEY`: Required if you want Anthropic Claude to generate the final answer.
- `ANTHROPIC_MODEL`: Anthropic model used instead of GPT.
- `LOCAL_EMBEDDING_DIM`: Local vector size for `HashingVectorizer`.
- `TOP_K`: Number of chunks retrieved before answer generation.
- `AZURE_SEARCH_ENDPOINT`: Required Azure AI Search service URL.
- `AZURE_API_KEY`: Azure admin key for the same Azure AI Search service.
- `AZURE_SEARCH_API_KEY`: Same Azure admin key, supported by the script for clarity.
- `AZURE_SEARCH_INDEX_NAME`: Azure index name created/updated by the script.

## Required API Keys

Required:

- `AZURE_SEARCH_API_KEY` for retrieval.
- `ANTHROPIC_API_KEY` for final answer generation.

Also required:

- `AZURE_SEARCH_ENDPOINT`, which must belong to the same Azure AI Search service as the key.

No separate embedding key is needed because embeddings are generated locally. Pinecone, Cohere, OpenAI, and Gemini keys are not required for this collab.

## Install

From the repo root:

```powershell
pip install -r requirements.txt
```

Required packages already covered by the repo requirements:

- `anthropic`
- `azure-search-documents`
- `numpy`
- `python-dotenv`
- `scikit-learn`

## Run

Run Azure retrieval only, without calling Anthropic:

```powershell
python main.py --skip-anthropic
```

Run full Azure RAG with Anthropic:

```powershell
python main.py --query "How does RAG work?"
```

Ask another question:

```powershell
python main.py --query "Why are local embeddings useful?"
```

## Notes

- `.env` is ignored by git and should not be committed.
- The script uses Anthropic Claude for generation, not GPT.
- Embeddings are deterministic and local, just like `collab_1`.
- Azure AI Search is the retrieval layer.
- The Azure endpoint and key must come from the same Azure AI Search service.
