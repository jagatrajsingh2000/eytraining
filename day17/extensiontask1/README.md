# Day 17 - Extension Task 1

This task builds a small LangGraph multi-agent architecture and exports its graph diagram.

## What It Uses

- `LangGraph` for the multi-agent workflow
- `ChatOpenAI` for supervisor, researcher, and writer behavior
- `IPython.display.Image` when available for diagram rendering support
- Root `eytraining/.env` for secrets

## Secret Source

The script reads the existing key from:

`eytraining/.env`

Expected variables:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
```

No new `.env` file is required inside this folder.

## Flow

- `supervisor` decides the next node
- `researcher` gathers notes
- `writer` drafts the response
- the graph pauses before `writer` to model human review

## Run

From `eytraining/day17/extensiontask1`:

```powershell
pip install -r ..\..\requirements.txt
python main.py
```

## Outputs

Saved in `day17/extensiontask1/output`:

- `multiagent_graph.mmd`
- `multiagent_graph.png` when Mermaid PNG rendering works
- `diagram_error.txt` if PNG rendering is unavailable
