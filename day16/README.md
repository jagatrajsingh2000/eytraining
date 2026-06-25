# Day 16 - RAG Systems and Agent Memory

Day 16 focuses on two production-style GenAI building blocks:

- A financial RAG pipeline for grounded question answering over annual-report content.
- A tool-using agent that combines short-term memory, long-term memory, and external tools.

## 1. Financial RAG System

Folder: `colab1`

This lab builds a Retrieval-Augmented Generation pipeline for financial document analysis. The flow is:

```text
Financial documents
    -> chunking
    -> embeddings
    -> FAISS vector store
    -> MMR retriever
    -> Azure OpenAI answer generation
    -> RAGAS evaluation
```

Key ideas:

- Split long filings into useful chunks.
- Convert chunks into embeddings with a Hugging Face model.
- Store vectors in FAISS for fast semantic retrieval.
- Use MMR retrieval to reduce duplicate context.
- Generate answers grounded in retrieved evidence.
- Evaluate quality using faithfulness, answer relevancy, context recall, and context precision.

## 2. Agent With Memory and Tools

Folder: `colab2`

This lab builds a ReAct-style agent that can reason, call tools, and remember previous interactions.

The memory setup has two layers:

- **Short-term memory** keeps the current conversation context.
- **Long-term memory** stores previous Q&A pairs in ChromaDB so they can be retrieved in later sessions.

The agent can use tools such as search, calculator logic, and Python execution. This makes it useful for multi-step questions where the model should not rely only on its own internal knowledge.

## What To Compare

| Area | RAG System | Memory Agent |
| --- | --- | --- |
| Main goal | Ground answers in documents | Reason with tools and remembered context |
| Storage | FAISS vector index | Chroma long-term memory |
| Best use case | Asking questions over financial filings | Interactive assistant with continuity |
| Evaluation | RAGAS metrics | Tool success, recall quality, answer quality |

## Practical Takeaway

Use RAG when the assistant must answer from a trusted document set. Use agent memory when the assistant needs continuity across turns or sessions. In real applications, both patterns can be combined.
