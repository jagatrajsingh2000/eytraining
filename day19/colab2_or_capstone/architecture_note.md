# Capstone Architecture Note - Support Agent

## Objective

Extend Lab 2 into a small customer support agent that can resolve a delayed-order refund request end to end.

The agent must combine short-term memory, long-term recall, tool routing, tool chaining, async side effects, human approval, tracing, retries, and prompt-cache/token reporting.

## Architecture

```text
User
  |
  v
Support Agent Loop
  |
  +-- Redis short-term memory
  |
  +-- Vector store policy recall
  |
  +-- SQLite operational tools
  |     +-- lookup_order
  |     +-- create_ticket
  |     +-- request_refund
  |     +-- approve_refund
  |
  +-- Redis Stream async queue
        +-- send_followup_email
        +-- email worker
        +-- check_email_job
```

## Memory

Short-term memory is stored in Redis as a list:

```text
support:history:<session_id>
```

Each user and assistant turn is appended as JSON. The list is trimmed to keep the latest turns bounded.

Long-term recall is implemented as a small vector store over support policy documents. The demo uses bag-of-words cosine similarity so it works without external embedding services.

## Tools

The capstone provides more than three tools:

- `recall_policy`
- `lookup_order`
- `create_ticket`
- `request_refund`
- `approve_refund`
- `send_followup_email`
- `check_email_job`

`send_followup_email` is async queue-backed. It writes to a Redis Stream and returns a `job_id` immediately.

## Routing And Chaining

The expected flow for a delayed refund request is:

```text
recall_policy
  -> lookup_order
  -> create_ticket
  -> request_refund
  -> approve_refund if needed
  -> send_followup_email
  -> check_email_job
```

This demonstrates both routing and prompt/tool chaining.

## Human Approval Gate

Refunds above `$100` return:

```python
{"status": "needs_approval", "approval_id": "..."}
```

The agent must call `approve_refund` before the refund is finalized.

## Tracing And Retries

All tool calls are wrapped by `run_tool`.

For each call, the trace records:

- tool name
- arguments
- duration in milliseconds
- success/failure
- number of attempts

The email tool simulates one transient failure so the retry behavior is visible.

## Prompt Caching

In live Claude mode, the system prompt is marked with ephemeral cache control:

```python
{"cache_control": {"type": "ephemeral"}}
```

The script also reads token usage fields when available:

- input tokens
- output tokens
- cache-read input tokens

Offline mode skips the API call and runs a deterministic mock flow.

## Why This Design

This design separates responsibilities:

- The LLM decides what should happen next.
- Python validates and executes tools.
- Redis preserves short-term state.
- The vector store retrieves durable policy knowledge.
- SQLite stores operational records.
- Redis Streams decouple slow email side effects from the agent turn.
- Human approval prevents high-value refunds from being auto-executed.

The result is a small but realistic support-agent architecture.
