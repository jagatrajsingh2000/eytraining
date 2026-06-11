from __future__ import annotations

import argparse
import hashlib
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.embeddings import Embeddings
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAIError


BASE_DIR = Path(__file__).resolve().parent

GEMINI_API_KEY = ""
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
CHAT_MODEL = "gemini-3.5-flash"
EMBEDDING_MODEL = "gemini-embedding-2-preview"


class LocalHashEmbeddings(Embeddings):
    """Tiny deterministic embedding model for offline FAISS testing."""

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in text.lower().split():
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            vector[index] += 1.0
        total = sum(value * value for value in vector) ** 0.5
        return [value / total for value in vector] if total else vector


class LocalPolicyQAChain:
    """Offline chain that retrieves FAISS chunks and returns the matched context."""

    def __init__(self, retriever) -> None:
        self.retriever = retriever

    def invoke(self, payload: dict[str, str]) -> dict[str, str]:
        question = payload["input"]
        docs = self.retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        return {
            "answer": (
                "Mock answer from retrieved policy context:\n"
                f"{context}\n\n"
                "Run without --mock to ask Gemini to write the final natural-language answer."
            )
        }


def create_policy_qa_chain(pdf_path: str | Path, mock: bool = False):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not mock and GEMINI_API_KEY == "PASTE_YOUR_GEMINI_API_KEY_HERE":
        raise ValueError("Replace GEMINI_API_KEY with your Gemini API key before running.")

    # Step 1: Load the 2-page PDF policy document.
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()

    # Step 2: Split the document into manageable chunks.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    # Step 3: Create embeddings and store chunks in a FAISS vectorstore.
    # Gemini works with the GPT/OpenAI SDK because Google documents an
    # OpenAI-compatible Gemini endpoint. The OpenAI/LangChain client keeps the
    # usual OpenAI request format, while base_url routes chat and embedding
    # requests to Gemini and api_key uses the Gemini API key.
    if mock:
        embeddings = LocalHashEmbeddings()
    else:
        embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_BASE_URL,
            tiktoken_enabled=False,
            check_embedding_ctx_length=False,
        )
    vectorstore = FAISS.from_documents(splits, embeddings)

    # Step 4: Expose the vectorstore as a retriever.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    if mock:
        return LocalPolicyQAChain(retriever)

    # Step 5: Define the system prompt for answering questions.
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use only the retrieved policy context to answer the question. "
        "If the answer is not in the context, say that you don't know.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # Step 6: Create the modern retrieval chain.
    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL,
    )
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FAISS retrieval QA bot for a policy PDF.")
    parser.add_argument(
        "--pdf",
        default=str(BASE_DIR / "policy_document.pdf"),
        help="Path to the policy PDF.",
    )
    parser.add_argument(
        "--question",
        default="What is the policy regarding remote work reimbursement?",
        help="Question to ask over the policy PDF.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Test PDF loading, splitting, FAISS indexing, and retrieval without Gemini API calls.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    qa_chain = create_policy_qa_chain(args.pdf, mock=args.mock)
    response = qa_chain.invoke({"input": args.question})

    print(f"Question: {args.question}\n")
    print(f"Answer: {response['answer']}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, OpenAIError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
