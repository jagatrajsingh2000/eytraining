# Day 20 - Task 1

Offline observability exercise for a multi-agent pipeline, based on the PDF assignment in `task_multipart.pdf`.

## Files

- `eytraining/day20/task1/agents.py` - standard-library-only solution
- `eytraining/day20/task1/output/trace.jsonl` - persisted JSON event stream after a run

## What it does

- Simulates an orchestrated agent pipeline: Planner -> Researcher -> Writer -> Reviewer
- Emits structured JSON events instead of plain progress prints
- Adds run-level `trace_id` and per-agent `span_id`
- Reports:
  - pipeline percent complete
  - throughput in steps/second
  - per-agent duration
- Emits lifecycle events:
  - `agent_started`
  - `agent_progress`
  - `agent_completed`
  - `agent_failed`
  - `run_summary`
- Persists events to `trace.jsonl`
- Prints a tiny per-agent timeline at the end

## Run

```powershell
python .\eytraining\day20\task1\agents.py
```

## Notes

- The current script intentionally fails `Writer` at step 3 to exercise failure localization.
- To test the success path, remove `fail_at_step=3` from `Writer` in `eytraining/day20/task1/agents.py:183`.

## Extra signal I'd add next

I would add retry count and tool-call success rate per agent, because they usually explain why an agent is slow or looping even when step counts look healthy. In a client environment, I would send these events to a centralized log pipeline or tracing backend such as OpenTelemetry-compatible storage.
