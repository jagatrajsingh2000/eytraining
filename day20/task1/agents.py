from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


# Output folder for persisted observability events.
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
# We store every emitted JSON event in JSONL format: one JSON object per line.
TRACE_PATH = OUTPUT_DIR / "trace.jsonl"


def utc_now() -> str:
    # Return a UTC timestamp so events are easy to compare across systems.
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Agent:
    # Minimal simulation of an agent in a multi-agent pipeline.
    # `steps` represents how many units of work this agent performs.
    # `fail_at_step` is optional and is used to test observability on failure.
    name: str
    steps: int
    fail_at_step: int | None = None

    def run(self, listener, trace_id: str) -> None:
        # Each agent execution gets its own span_id.
        # trace_id = whole pipeline run
        # span_id = one agent's execution inside that run
        span_id = str(uuid.uuid4())
        started_at = time.time()

        # Emit lifecycle event: the agent has started.
        listener.agent_started(self.name, trace_id, span_id, self.steps)

        # We do not emit progress on every single step.
        # Instead, we throttle to roughly every 25% to reduce log noise.
        progress_marks = {max(1, round(self.steps * fraction / 4)) for fraction in range(1, 5)}

        for step in range(1, self.steps + 1):
            # Simulate actual work / latency.
            time.sleep(random.uniform(0.05, 0.15))

            # Force a deterministic failure when requested.
            # This helps prove that our telemetry can pinpoint where the run broke.
            if self.fail_at_step and step == self.fail_at_step:
                listener.agent_failed(
                    agent_name=self.name,
                    trace_id=trace_id,
                    span_id=span_id,
                    step=step,
                    total_steps=self.steps,
                    error_message=f"{self.name} failed at step {step}",
                )
                raise RuntimeError(f"{self.name} failed at step {step}")

            # Emit throttled progress events.
            if step in progress_marks or step == self.steps:
                listener.agent_progress(self.name, trace_id, span_id, step, self.steps)

        # Emit completion with total duration for this agent.
        listener.agent_completed(self.name, trace_id, span_id, self.steps, time.time() - started_at)


class ObservabilityListener:
    def __init__(self, agents: list[Agent], trace_path: Path):
        # One trace_id groups all events from one end-to-end run.
        self.trace_id = str(uuid.uuid4())
        self.trace_path = trace_path

        # Pipeline-level stats are computed across all agents together.
        self.total_steps = sum(agent.steps for agent in agents)
        self.completed_steps = 0
        self.completed_agents = 0
        self.run_started_at = time.time()
        self.failed_agent: str | None = None

        # Fresh run = fresh output file.
        self.trace_path.parent.mkdir(exist_ok=True)
        self.trace_path.write_text("", encoding="utf-8")

    def pipeline_percent_complete(self) -> float:
        # Pipeline progress = finished steps / total planned steps.
        return round((self.completed_steps / self.total_steps) * 100, 2)

    def throughput(self) -> float:
        # Throughput tells us how fast the whole run is moving.
        elapsed = max(time.time() - self.run_started_at, 1e-6)
        return round(self.completed_steps / elapsed, 2)

    def emit(self, event: dict) -> None:
        # All events are normalized into one JSON shape.
        # This makes them queryable and easier to ship to real log systems later.
        payload = {
            "timestamp": utc_now(),
            "trace_id": self.trace_id,
            **event,
        }
        line = json.dumps(payload, ensure_ascii=False)
        print(line)

        # Persist every event so we can inspect the run after execution.
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def agent_started(self, agent_name: str, trace_id: str, span_id: str, total_steps: int) -> None:
        # Agent lifecycle event: start.
        self.emit(
            {
                "span_id": span_id,
                "event": "agent_started",
                "agent": agent_name,
                "step": 0,
                "total_steps": total_steps,
                "pipeline_percent_complete": self.pipeline_percent_complete(),
                "throughput_steps_per_sec": self.throughput(),
            }
        )

    def agent_progress(self, agent_name: str, trace_id: str, span_id: str, step: int, total_steps: int) -> None:
        # Every progress event represents one completed unit of work.
        self.completed_steps += 1
        self.emit(
            {
                "span_id": span_id,
                "event": "agent_progress",
                "agent": agent_name,
                "step": step,
                "total_steps": total_steps,
                "pipeline_percent_complete": self.pipeline_percent_complete(),
                "throughput_steps_per_sec": self.throughput(),
            }
        )

    def agent_completed(
        self,
        agent_name: str,
        trace_id: str,
        span_id: str,
        total_steps: int,
        duration_seconds: float,
    ) -> None:
        # Track how many agents finished successfully.
        self.completed_agents += 1
        self.emit(
            {
                "span_id": span_id,
                "event": "agent_completed",
                "agent": agent_name,
                "step": total_steps,
                "total_steps": total_steps,
                "duration_seconds": round(duration_seconds, 3),
                "pipeline_percent_complete": self.pipeline_percent_complete(),
                "throughput_steps_per_sec": self.throughput(),
            }
        )

    def agent_failed(
        self,
        agent_name: str,
        trace_id: str,
        span_id: str,
        step: int,
        total_steps: int,
        error_message: str,
    ) -> None:
        # Failure event localizes exactly which agent and which step failed.
        self.failed_agent = agent_name
        self.emit(
            {
                "span_id": span_id,
                "event": "agent_failed",
                "agent": agent_name,
                "step": step,
                "total_steps": total_steps,
                "error_message": error_message,
                "pipeline_percent_complete": self.pipeline_percent_complete(),
                "throughput_steps_per_sec": self.throughput(),
            }
        )

    def run_summary(self, status: str) -> None:
        # Final orchestration-level event summarizing the whole run.
        self.emit(
            {
                "span_id": "run",
                "event": "run_summary",
                "agent": "orchestrator",
                "final_status": status,
                "completed_agents": self.completed_agents,
                "failed_agent": self.failed_agent,
                "total_duration_seconds": round(time.time() - self.run_started_at, 3),
                "pipeline_percent_complete": self.pipeline_percent_complete(),
                "throughput_steps_per_sec": self.throughput(),
            }
        )


class Orchestrator:
    def __init__(self, agents: list[Agent], listener: ObservabilityListener):
        # The orchestrator is responsible for calling agents in sequence.
        self.agents = agents
        self.listener = listener

    def run(self) -> None:
        try:
            # Run the pipeline agent by agent.
            for agent in self.agents:
                agent.run(self.listener, self.listener.trace_id)
        except RuntimeError:
            # If any agent fails, stop cleanly and emit a failed run summary.
            self.listener.run_summary(status="failed")
            return
        # If all agents finish, emit a success summary.
        self.listener.run_summary(status="success")


def print_timeline(trace_path: Path) -> None:
    # Small helper for reading the persisted trace and summarizing it per agent.
    print("\nPer-agent timeline")
    timelines: dict[str, list[str]] = {}
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        agent = event["agent"]
        timelines.setdefault(agent, []).append(event["event"])
    for agent, events in timelines.items():
        print(f"- {agent}: {' -> '.join(events)}")


def main() -> None:
    # Fixed seed keeps the demo timing stable across runs.
    random.seed(7)

    # This pipeline mirrors a simple multi-agent handoff chain.
    # Writer is intentionally configured to fail so we can see the failure event.
    agents = [
        Agent("Planner", 3),
        Agent("Researcher", 6),
        Agent("Writer", 4, fail_at_step=3),
        Agent("Reviewer", 2),
    ]

    # Listener collects and emits all observability data.
    listener = ObservabilityListener(agents, TRACE_PATH)

    # Run the orchestration, then read the saved trace back as a tiny summary.
    Orchestrator(agents, listener).run()
    print_timeline(TRACE_PATH)
    print(f"\nTrace saved to: {TRACE_PATH}")


if __name__ == "__main__":
    main()
