# 🧪 Day 16 Colab 2 — LangChain Agent with Short-Term & Long-Term Memory + Tools

## Overview

Build a **ReAct agent** with dual memory systems (Short-Term + Long-Term) and real tools (web search, Python REPL, calculator). The agent reasons step-by-step, uses tools when needed, and remembers facts across conversation turns and even across sessions.

> **Note:** This lab uses **OpenAI GPT-4o** (converted from the original Anthropic Claude version).

---

## Architecture

```
User Prompt
     │
     ▼
┌─────────────────────────────────────────────┐
│               AgentExecutor                  │
│                                             │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │  ReAct LLM  │◄──►│  STM (Buffer/      │  │
│  │  (GPT-4o)   │    │  Summary Memory)   │  │
│  └──────┬──────┘    └────────────────────┘  │
│         │ tool calls                        │
│  ┌──────▼──────────────────────────────┐    │
│  │            Tool Router              │    │
│  │  [Search]  [PythonREPL]  [Calc]     │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────┐
│  LTM: Chroma VectorDB│  ← stores every Q&A pair
│  (persistent across  │    retrieved at query time
│   sessions)         │
└─────────────────────┘
```

**STM** = the rolling conversation window (this session only)
**LTM** = semantic vector store that persists across sessions

---

## What's Inside

```
day16/colab2/
├── main.py              # Standalone Python script (converted from notebook)
├── README.md            # This file
└── chroma_ltm/          # Created at runtime — persistent vector store
```

---

## Pipeline Sections

| Part | Description |
|------|-------------|
| **Part 1** | Short-Term Memory (STM) with `ConversationBufferMemory` — agent recalls facts from earlier in the conversation |
| **Part 2** | Long-Term Memory (LTM) with ChromaDB — agent retrieves semantically similar past Q&A pairs from a persistent vector store |
| **Part 3** | Defining Tools — web search (Tavily), Python REPL, safe calculator |
| **Part 4** | Assembling the Full Agent — ReAct agent with custom prompt that injects both STM and LTM |
| **Part 5** | Testing — 4 tests covering LTM recall, multi-step reasoning, follow-ups, and code execution |
| **Part 6** | STM vs LTM Comparison — side-by-side view of what each memory system holds |

### Extension Tasks

| Extension | Description |
|-----------|-------------|
| **Extension 1** | Swap STM to `ConversationSummaryMemory` — LLM summarises older exchanges to save tokens |
| **Extension 2** | Add a SQLite tool for structured LTM — exact lookups (user IDs, deadlines, preferences) |
| **Extension 3** | Self-Critique Loop (Reflexion) — agent evaluates its own answer, identifies weaknesses, revises |
| **Extension 4** | Streaming output — custom callback handler that prints tokens and tool calls in real-time |

---

## Setup

### 1. Install Dependencies

```bash
pip install langchain langchain-openai langchain-community langchain-experimental \
    langchain-chroma chromadb tavily-python sentence-transformers \
    tiktoken faiss-cpu python-dotenv pydantic
```

### 2. Configure `.env`

Make sure your project-level `.env` file (in `Ey_training_genai/`) contains:

```env
# Required
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Required for web search tool
TAVILY_API_KEY=tvly-your-tavily-key-here
```

**How to get a Tavily API key:**
1. Go to [tavily.com](https://tavily.com)
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Paste it into your `.env` file

### 3. Run

```bash
# From the project root
python day16/colab2/main.py
```

---

## Key Concepts

### Short-Term Memory (STM)
- Lives in the LLM's context window
- Keeps conversation history so the agent can refer to earlier messages
- **Buffer**: keeps all messages verbatim (simple but fills up fast)
- **Summary**: LLM summarises older exchanges to save tokens (production-ready)

### Long-Term Memory (LTM)
- Stored in a **ChromaDB vector database** on disk
- Persists across sessions — restart the script and it still remembers
- Uses **semantic similarity search** (not keyword matching)
- A query about "revenue last quarter" retrieves "Q3 sales figures"

### ReAct Agent Pattern
The agent follows a strict Thought → Action → Observation loop:
1. **Thought**: "I need to search the web for current population data"
2. **Action**: `TavilySearch("current population of India")`
3. **Observation**: "India's population is approximately 1.44 billion..."
4. **Thought**: "Now I need to calculate 0.5% of that"
5. **Action**: `Calculator("1440000000 * 0.005")`
6. **Observation**: "7200000"
7. **Final Answer**: "0.5% of India's population is 7.2 million"

### Reflexion (Self-Critique)
The agent generates an answer, then a separate "critic" LLM scores and critiques it. If the score is below 9/10, the agent revises its answer using the feedback. This can run for multiple rounds.

---

## STM vs LTM Comparison

| Property | STM (Buffer) | LTM (Chroma) |
|----------|-------------|--------------|
| **Scope** | This session only | Across all sessions |
| **Retrieval** | Sequential (all messages) | Semantic similarity search |
| **Persistence** | Lost on session end | Saved to disk |
| **Token cost** | Grows linearly | Fixed-size injection (top-k) |
| **Best for** | Context continuity | User facts, past decisions |

---

## Reflection Questions

1. When would you choose `ConversationSummaryMemory` over `ConversationBufferMemory`?
2. What happens if LTM retrieves irrelevant context? How would you filter it?
3. How does the Reflexion pattern trade off latency vs quality?
4. What safety concerns exist with giving an agent a `PythonREPLTool`?
