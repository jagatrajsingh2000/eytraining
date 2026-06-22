# Day 18 - AutoGen

This folder contains two files:

- `run_autogen_studio.py` starts AutoGen Studio in the browser through ngrok.
- `groq_architecture_agent.py` creates a simple AutoGen agent in Python.

## 1. Start AutoGen Studio

From the project root:

```bash
python3 Ey_training_genai/day18/autogen/run_autogen_studio.py
```

The script will:

1. Install `autogenstudio`, `pyautogen`, and `pyngrok`.
2. Verify AutoGen Studio.
3. Read or ask for the Groq API key.
4. Ask for the ngrok auth token.
5. Start AutoGen Studio on port `8081`.
6. Print the public browser URL.

## 2. Run The Python Agent

From this folder:

```bash
python3 groq_architecture_agent.py
```

Or from the project root:

```bash
python3 Ey_training_genai/day18/autogen/groq_architecture_agent.py
```

The agent is named `architecture_choice_agent`.

It is designed to help with GenAI architecture-choice questions, such as:

- single-agent vs multi-agent
- AutoGen vs CrewAI
- LangGraph for production orchestration
- human-in-the-loop and tool-routing decisions

## Environment

The agent reads keys from:

```text
Ey_training_genai/.env
```

Preferred variable:

```env
GROQ_API_KEY=your_groq_key
```

You can also set:

```env
GROQ_MODEL=llama-3.3-70b-versatile
```
