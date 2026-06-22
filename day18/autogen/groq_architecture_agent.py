"""Create and run a simple AutoGen agent backed by Groq.

This file belongs in the Day 18 AutoGen folder as the actual agent example.
It reads keys from environment variables or from the project `.env` file.

Run:
    python3 groq_architecture_agent.py
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ENV = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def load_env_file(path: Path = PROJECT_ENV) -> None:
    """Load simple KEY=value pairs without printing secrets."""
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_groq_api_key() -> str:
    """Use GROQ_API_KEY first, with XAI_API_KEY as a class-notes fallback."""
    load_env_file()
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GROQ_API_KEY in Ey_training_genai/.env or in your shell before running."
        )
    return api_key


def create_architecture_agent():
    """Create an AutoGen assistant agent for architecture-choice practice."""
    try:
        from autogen import AssistantAgent
    except ImportError as exc:
        raise RuntimeError(
            "AutoGen is not installed. Run run_autogen_studio.py first, or install it with "
            "`python3 -m pip install autogenstudio pyautogen`."
        ) from exc

    config_list = [
        {
            "model": os.getenv("GROQ_MODEL", DEFAULT_MODEL),
            "api_key": get_groq_api_key(),
            "base_url": GROQ_BASE_URL,
            "api_type": "openai",
            "price": [0.0, 0.0],
        }
    ]

    return AssistantAgent(
        name="architecture_choice_agent",
        llm_config={
            "config_list": config_list,
            "temperature": 0.2,
        },
        system_message=(
            "You are an AutoGen architecture-choice coach for GenAI training. "
            "Help learners decide between single-agent, multi-agent, AutoGen, CrewAI, "
            "LangGraph, and no-code workflow tools. Always explain the decision cues, "
            "trade-offs, and a simple implementation shape. "
            "When your response is complete, end with the exact word TERMINATE on its own line."
        ),
    )


def run_demo_chat() -> None:
    """Run a short terminal chat with the agent."""
    try:
        from autogen import UserProxyAgent
    except ImportError as exc:
        raise RuntimeError(
            "AutoGen is not installed. Run run_autogen_studio.py first, or install it with "
            "`python3 -m pip install autogenstudio pyautogen`."
        ) from exc

    assistant = create_architecture_agent()
    user_proxy = UserProxyAgent(
        name="learner",
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=3,
        is_termination_msg=lambda message: str(message.get("content", ""))
        .rstrip()
        .endswith("TERMINATE"),
    )

    task = (
        "A hospital wants one system to read scan reports, check medication risk, "
        "schedule follow-up, and draft patient communication. Should this be single-agent "
        "or multi-agent, and why?"
    )
    user_proxy.initiate_chat(assistant, message=task)


if __name__ == "__main__":
    run_demo_chat()
