# Day 19 Colab 2 / Capstone

This folder contains two related demos:

- `multitool_order_agent.py` - Python version of the Lab 2 ordering notebook.
- `support_agent_capstone.py` - take-home support-agent capstone.
- `support_agent_capstone.ipynb` - notebook wrapper that runs the capstone script.
- `architecture_note.md` - short architecture note.

The main file for the take-home task is:

```text
support_agent_capstone.py
```

## What The Capstone Builds

The capstone is a small customer support agent.

Scenario:

```text
Customer says order A1003 is very delayed and wants a refund plus an email update.
```

The support agent must:

1. Remember the conversation.
2. Recall support policy.
3. Look up the order.
4. Create a support ticket.
5. Request a refund.
6. Ask for human approval if the refund is high value.
7. Queue a follow-up email asynchronously.
8. Check the email job status.
9. Print trace spans for every tool call.

## High-level Flow

```text
User request
  |
  v
Support agent
  |
  +-- Redis short-term memory
  |
  +-- Vector-store policy recall
  |
  +-- SQLite tools
  |     +-- lookup_order
  |     +-- create_ticket
  |     +-- request_refund
  |     +-- approve_refund
  |
  +-- Redis Stream async queue
        +-- send_followup_email
        +-- run_email_worker
        +-- check_email_job
```

## Components Explained

### 1. Redis Short-term Memory

Class:

```python
ShortTermMemory
```

Purpose:

- stores recent user and assistant turns
- uses Redis list commands
- keeps only the latest turns with `ltrim`

Key used:

```text
support:history:<session_id>
```

In this demo, `fakeredis` is used, so no Redis server is required.

### 2. Vector Store For Long-term Recall

Class:

```python
SimpleVectorStore
```

Purpose:

- stores support policy documents
- retrieves the most relevant policy for the current user issue

The demo uses a small bag-of-words cosine similarity implementation.

In production, this would usually become:

```text
embedding model + vector database
```

### 3. SQLite Operational Database

Function:

```python
create_database()
```

Tables:

- `orders`
- `tickets`
- `refunds`
- `approvals`

SQLite stands in for real systems such as:

- order database
- ticketing platform
- refund ledger
- approval workflow

### 4. Tools

The agent has more than three tools:

```text
recall_policy
lookup_order
create_ticket
request_refund
approve_refund
send_followup_email
check_email_job
```

Each tool is a normal Python function.

The LLM does not execute tools directly. It asks for a tool, and Python runs it through:

```python
run_tool(...)
```

### 5. Human Approval Gate

Constant:

```python
APPROVAL_THRESHOLD = 100.0
```

If a refund is more than `$100`, `request_refund` returns:

```python
{"status": "needs_approval", "approval_id": "..."}
```

Then the agent must call:

```python
approve_refund(...)
```

This prevents high-value refunds from being silently approved.

### 6. Async Queue-backed Tool

Tool:

```python
send_followup_email
```

This tool does not send email directly.

Instead, it writes an email job to a Redis Stream:

```text
support:emails
```

Then a worker processes it:

```python
run_email_worker(...)
```

This models the common production pattern:

```text
agent queues slow side effect -> worker performs it later
```

### 7. Tracing And Retries

Class:

```python
TraceRecorder
```

Every tool call records:

- tool name
- arguments
- execution time
- success/failure
- number of attempts

The email tool intentionally fails once:

```python
raise RuntimeError("temporary email provider timeout")
```

Then `run_tool` retries it.

This shows how transient failures can recover without breaking the whole agent flow.

### 8. Prompt Caching And Token Hooks

In live Claude mode, the system prompt is marked cacheable:

```python
"cache_control": {"type": "ephemeral"}
```

The script reads token usage when available:

```python
input_tokens
output_tokens
cache_read_input_tokens
```

In offline mode, this part is skipped because no model call is made.

## Expected Tool Chain

For the demo prompt, the intended sequence is:

```text
recall_policy
  -> lookup_order
  -> create_ticket
  -> request_refund
  -> approve_refund
  -> send_followup_email
  -> run_email_worker
  -> check_email_job
```

## Run

From this folder:

```bash
python3 support_agent_capstone.py
```

Or from the project root:

```bash
python3 Ey_training_genai/day19/colab2_or_capstone/support_agent_capstone.py
```

## API Key Behavior

The script reads:

```text
Ey_training_genai/.env
```

If this is set:

```env
ANTHROPIC_API_KEY=demo
```

the script runs in offline mock mode.

Offline mode still demonstrates the full architecture without making a Claude API call.

## Output To Look For

When the script runs successfully, look for:

- the final agent reply
- created ticket
- approved refund
- approval record
- short-term memory turns
- trace span table
- email job status `sent`

Example final reply shape:

```text
Ticket 1 opened. Refund approval approved for $410.0. Email job sent.
```

## Why This Architecture Matters

The LLM is used for reasoning and routing.

Python owns execution:

```text
LLM decides -> Python validates -> Python executes -> result goes back to LLM
```

This keeps the system:

- safer
- easier to debug
- easier to trace
- easier to extend with real services later

The capstone is intentionally small, but the shape matches a real support-agent architecture.
