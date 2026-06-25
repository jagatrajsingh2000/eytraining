# Trace / Spans vs Audit Logs

Traces and audit logs both record system activity, but they answer different questions.

| Aspect | Trace / Spans | Audit Log |
| --- | --- | --- |
| Main question | How did this request move through the system? | What action or decision happened? |
| Primary audience | Engineers, SREs, DevOps | Compliance, security, auditors |
| Retention | Usually short or medium term | Usually long term |
| Sampling | Often sampled | Usually complete for important actions |
| Best for | Debugging, latency, cost, failures | Accountability, compliance, proof |

## Trace / Spans

A trace follows one request across services, agents, tools, and model calls. Each span represents one part of the request.

Use traces when you need to know:

- Where a request failed.
- Which service or agent was slow.
- How many tokens were used.
- Which tool call caused an error.
- What happened inside a multi-agent workflow.

## Audit Logs

An audit log records important business actions and decisions in a durable form.

Use audit logs when you need to prove:

- Who performed an action.
- When a decision was made.
- What was approved, denied, blocked, or changed.
- Whether a compliance requirement was satisfied.
- Whether records remained tamper-evident over time.

## When To Use Both

Use both for critical workflows such as financial transactions, guardrail blocks, access changes, policy decisions, or regulated GenAI workflows.

Simple rule:

- **Trace / Spans** explain how the system behaved.
- **Audit Logs** prove what decision or action happened.
- **Both** are needed when the workflow must be debugged and legally or operationally verified.
