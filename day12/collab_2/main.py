"""
Day 12 - Collab 2: Azure AI Search RAG with Anthropic

This script uses local HashingVectorizer embeddings, Azure AI Search for retrieval,
and Anthropic Claude for answer generation. It does not use OpenAI GPT or remote embedding APIs.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

import numpy as np
from anthropic import Anthropic
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize


SCRIPT_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
LOCAL_EMBEDDING_DIM = int(os.getenv("LOCAL_EMBEDDING_DIM", "1536"))
TOP_K = int(os.getenv("TOP_K", "4"))
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", os.getenv("AZURE_API_KEY", ""))
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "collab-2-rag")

ARTICLES = [
    {
        "title": "Retrieval-Augmented Generation",
        "content": "Retrieval-Augmented Generation combines a retriever with a language model. Documents are split into chunks, embedded into vectors, and stored in a vector index. At question time, the query is embedded, relevant chunks are retrieved, and the language model answers using that context.",
    },
    {
        "title": "Vector Search",
        "content": "Vector search represents text as numeric embeddings and finds similar content using nearest-neighbour search. Similarity can be measured with cosine similarity, inner product, or Euclidean distance. FAISS is a popular local library for vector indexing and search.",
    },
    {
        "title": "Anthropic Claude",
        "content": "Anthropic Claude is a family of language models designed for helpful, safe, and context-aware responses. In this collab, Anthropic is used for answer generation instead of OpenAI GPT. Embeddings are created locally, so the Anthropic key is only needed for the final response generation layer.",
    },
    {
        "title": "Local Embeddings",
        "content": "Local embeddings avoid remote embedding API calls. This script uses scikit-learn HashingVectorizer to create deterministic fixed-size vectors. These vectors are useful for lab demonstrations, lightweight retrieval, and environments where external embedding APIs are not available.",
    },
    {
        "title": "FAISS",
        "content": "FAISS is an open-source similarity search library from Meta. IndexFlatL2 performs exact nearest-neighbour search over vectors. It runs locally and is useful for prototypes, demos, and small corpora that fit in memory.",
    },
]


@dataclass
class RetrievedChunk:
    title: str
    content: str
    score: float


class LocalHashingEmbedder:
    def __init__(self, dimensions: int) -> None:
        self.vectorizer = HashingVectorizer(
            n_features=dimensions,
            alternate_sign=False,
            norm=None,
            stop_words="english",
        )

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        matrix = self.vectorizer.transform(texts)
        normalized = normalize(matrix, norm="l2", copy=False)
        return normalized.astype(np.float32).toarray()

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_documents([query])


def require_azure_config() -> None:
    if not AZURE_SEARCH_ENDPOINT:
        raise RuntimeError("Set AZURE_SEARCH_ENDPOINT in day12/collab_2/.env.")
    if not AZURE_SEARCH_API_KEY:
        raise RuntimeError("Set AZURE_SEARCH_API_KEY in day12/collab_2/.env.")


def make_search_clients() -> tuple[SearchIndexClient, SearchClient]:
    require_azure_config()
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=credential)
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=credential,
    )
    return index_client, search_client


def create_or_update_index(index_client: SearchIndexClient) -> None:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=LOCAL_EMBEDDING_DIM,
            vector_search_profile_name="hnsw-profile",
        ),
    ]

    index = SearchIndex(
        name=AZURE_SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")],
        ),
    )
    index_client.create_or_update_index(index)


def upload_documents(search_client: SearchClient, embedder: LocalHashingEmbedder) -> None:
    texts = [article["content"] for article in ARTICLES]
    vectors = embedder.embed_documents(texts)

    payload = []
    for article_index, (article, vector) in enumerate(zip(ARTICLES, vectors)):
        payload.append(
            {
                "id": f"article-{article_index}",
                "title": article["title"],
                "content": article["content"],
                "embedding": vector.tolist(),
            }
        )

    search_client.upload_documents(documents=payload)


def prepare_azure_search(embedder: LocalHashingEmbedder) -> SearchClient:
    index_client, search_client = make_search_clients()
    create_or_update_index(index_client)
    upload_documents(search_client, embedder)
    return search_client


def retrieve(query: str, embedder: LocalHashingEmbedder, search_client: SearchClient, top_k: int) -> list[RetrievedChunk]:
    query_vector = embedder.embed_query(query)[0].tolist()
    results = search_client.search(
        search_text=query,
        vector_queries=[
            VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="embedding",
            )
        ],
        select=["title", "content"],
        top=top_k,
    )

    chunks = [
        RetrievedChunk(
            title=result["title"],
            content=result["content"],
            score=float(result.get("@search.score", 0.0)),
        )
        for result in results
    ]
    return chunks


def answer_with_anthropic(query: str, chunks: list[RetrievedChunk]) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("Set ANTHROPIC_API_KEY in day12/collab_2/.env before asking Anthropic for an answer.")

    context = "\n\n".join(
        f"Title: {chunk.title}\nContent: {chunk.content}" for chunk in chunks
    )
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=500,
        temperature=0.2,
        system="Answer using only the provided context. If the context is insufficient, say what is missing.",
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Collab 2 Azure AI Search RAG with Anthropic.")
    parser.add_argument("--query", default="How does RAG work?", help="Question to answer.")
    parser.add_argument("--skip-anthropic", action="store_true", help="Only show retrieved chunks, do not call Anthropic.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    embedder = LocalHashingEmbedder(dimensions=LOCAL_EMBEDDING_DIM)
    search_client = prepare_azure_search(embedder)
    chunks = retrieve(args.query, embedder, search_client, TOP_K)

    print(f"Query: {args.query}")
    print("\nRetrieved chunks:")
    for rank, chunk in enumerate(chunks, start=1):
        print(f"{rank}. {chunk.title} | score={chunk.score:.4f}")

    if args.skip_anthropic:
        return

    print("\nAnthropic answer:")
    print(answer_with_anthropic(args.query, chunks))


if __name__ == "__main__":
    main()
