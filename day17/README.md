# Day 17 - Multi-Agent Architecture

Day 17 covers different ways to coordinate multiple AI agents. The main theme is: split work only when the task genuinely benefits from specialist roles, parallel work, or review checkpoints.

## Main Topics

| Folder | Topic | Purpose |
| --- | --- | --- |
| `task1` | YouTube emotion analysis | App-style workflow for multimodal analysis |
| `collab1` | CrewAI + Groq pipeline | Multi-agent task execution with specialist roles |
| `extensiontask1` | Multi-agent architecture | Supervisor-style orchestration and graph output |
| `extensiontask2` | AutoGen vs Flowise scenario | Architecture comparison and selection reasoning |

## Supervisor Pattern

The supervisor pattern uses one coordinating agent to manage specialist agents.

```text
User request
    -> Supervisor
        -> Research Agent
        -> Analysis Agent
        -> Writer Agent
    -> Final response
```

This pattern is useful when the workflow needs clear ownership but still needs a central decision-maker.

## Researcher-Supervisor Pattern

A common research workflow has:

- **Supervisor**: decides the next step.
- **Researcher**: gathers information or evidence.
- **Writer**: turns findings into a final report.

This works well when the final response should be based on collected evidence and a human may need to review the research before the writer produces the final output.

## When Multi-Agent Helps

Choose a multi-agent setup when:

- The task has clearly different domains.
- Some work can run in parallel.
- Different tools or permissions are needed.
- A reviewer or approval gate is required.
- You want clearer traceability for each stage.

For a simple linear task with one shared context, a single well-designed agent is often cleaner and faster.
