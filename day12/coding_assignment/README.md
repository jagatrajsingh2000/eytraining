# Smart FAQ Bot

Minimal RAG-powered FAQ bot for the Day 12 coding assignment.

## What It Does

- Uses a plain Python list of 10 FAQ strings.
- Creates local embeddings with `HashingVectorizer`.
- Stores vectors in FAISS in memory.
- Retrieves the top 2 most similar FAQs by cosine-style similarity.
- Uses Groq for a concise grounded answer when `GROQ_API_KEY` is available.
- Falls back to an offline answer from retrieved FAQs if Groq is unavailable.

## `.env`

Create `day12/coding_assignment/.env`:

```env
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant
```

No embedding API key is required because embeddings are local.

## Run

From this folder:

```powershell
python main.py
```

Type a question, for example:

```text
How can I return my order?
```

Type `exit` to quit.

## Required Packages

Covered by the repo `requirements.txt`
