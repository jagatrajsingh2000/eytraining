# Day 17 - Collab 1

Python version of the CrewAI supply-chain disruption pipeline, powered by Groq.

## Required Keys

This script reads secrets from the existing root file:

`eytraining/.env`

Required:

```env
GROQ_API_KEY=your_groq_key
```

Optional:

```env
TAVILY_API_KEY=your_tavily_key
```

`TAVILY_API_KEY` is not required in the current script because it uses a built-in mock search tool. If you later swap in a real Tavily search tool, add that key to the same root `.env`.

## LLM Setup

CrewAI is configured to call Groq through its OpenAI-compatible endpoint, so no `litellm` setup is required for this script.

## What It Builds

- 5 CrewAI agents:
- Disruption Monitor
- Route Optimiser
- Supplier Communications Specialist
- Trade Compliance Officer
- Executive Communications Writer

- Hierarchical crew orchestration with a Groq manager model
- Task dependency chain through `context`
- Executive disruption report written to disk

## Run

From `eytraining`:

```powershell
python .\day17\collab1\main.py
```

This runs in offline mode by default and generates the report without calling Groq.

To attempt the live CrewAI + Groq flow:

```powershell
python .\day17\collab1\main.py --remote
```

## Output

Files are saved in `day17/collab1/output`:

- `globalflow_disruption_report.txt`
- `crew_run.log`
