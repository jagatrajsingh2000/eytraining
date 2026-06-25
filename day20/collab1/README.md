# Day 20 - Observability and Guardrails

This folder contains a lightweight observability and governance demo for LLM-style calls.

## What It Demonstrates

The script wraps model-like interactions with:

- Structured logging
- Telemetry collection
- Latency tracking
- Token and cost estimation
- Guardrail checks
- Retry handling
- Rate limiting
- Budget protection
- Persistent audit logging

## Architecture

```text
User request
    -> input guardrails
    -> rate limiter
    -> retry handler
    -> instrumented LLM call
        -> telemetry
        -> cost tracking
        -> structured logs
        -> audit log
```

## Output Files

| File | Purpose |
| --- | --- |
| `output/logs.jsonl` | Structured operational logs |
| `output/llm_calls.jsonl` | Per-call model telemetry |
| `output/audit_log.jsonl` | Durable audit events |
| `output/results.json` | Run output summary |
| `output/judge_eval.json` | Evaluation or judging result |

## Key Lesson

Observability explains how the system behaved. Guardrails control what the system is allowed to do. Audit logs preserve the important decisions and actions for later review.
