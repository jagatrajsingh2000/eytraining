# Day 18 - Orchestration Patterns

This topic compares common AutoGen-style orchestration patterns for coordinating multiple agents.

## Patterns Covered

| Pattern | How It Works | Best Fit |
| --- | --- | --- |
| Round Robin | Agents speak in a fixed order | Simple predictable workflows |
| Selector | A router chooses the next agent | Flexible tasks where the next step depends on context |
| GraphFlow | Agents follow a graph of dependencies | Structured workflows with branches, joins, and checkpoints |

## Example Agent Roles

```text
Planner -> Researcher -> Writer -> Final Answer
```

The basic workflow can be extended with a fact checker or reviewer when output quality matters.

## Round Robin

Round robin is the simplest pattern. Each agent gets a turn in sequence.

```text
Planner
  -> Researcher
  -> Writer
```

It is easy to debug because the order is predictable, but it can be inefficient if an agent is not needed for a specific request.

## Selector

Selector-based routing uses a routing decision to choose which agent should act next.

```text
User request
  -> Selector
  -> Best available agent
  -> Selector
  -> Next best agent
```

This is useful when the task is open-ended or the next step cannot be known in advance.

## GraphFlow

GraphFlow treats the workflow as a graph. Nodes are agents, and edges define the allowed execution path.

```text
Planner
  -> Researcher
  -> Fact Checker
  -> Writer
```

GraphFlow is a strong choice for enterprise workflows because the process is explicit, testable, and easier to audit.

## Design Note

If a framework version does not support nested teams inside graph nodes, flatten the design into individual agents. This keeps the architecture compatible while preserving the logical workflow.
