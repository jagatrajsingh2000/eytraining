"""Day 19 Colab 1 - Claude Agent + FastAPI Backend + Redis Memory.

This is the Python script version of the Colab notebook.

It demonstrates:
1. A tiny FastAPI backend exposing an `/orders/{id}` endpoint.
2. A Redis-like memory layer using fakeredis.
3. A Claude tool-use loop driven by `stop_reason`.

Run:
    python3 claude_agent_fastapi_redis_memory.py

If `ANTHROPIC_API_KEY` is not set, the script runs in offline mock mode.
"""

from __future__ import annotations

import getpass
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


MODEL = "claude-sonnet-4-6"
SUMMARY_MODEL = "claude-3-5-haiku-latest"
PROJECT_ENV = Path(__file__).resolve().parents[2] / ".env"


def install_dependencies() -> None:
    """Install dependencies used by the lab."""
    # In Colab this is similar to running:
    # !pip install anthropic fastapi 'httpx<0.28' fakeredis
    # In a local script we first check what is missing, then install only that.
    required = {
        "anthropic": "anthropic",
        "fastapi": "fastapi",
        "fakeredis": "fakeredis",
        "httpx": "httpx<0.28",
    }
    missing = [package for module, package in required.items() if importlib.util.find_spec(module) is None]
    if not missing:
        print("deps already installed")
        return

    command = [sys.executable, "-m", "pip", "install", "-q", *missing]
    try:
        subprocess.run(command, check=True)
        print("deps installed")
    except subprocess.CalledProcessError as exc:
        install_hint = " ".join(command)
        raise RuntimeError(
            "Missing dependencies could not be installed automatically. "
            "If you are on macOS system Python, activate a virtual environment first, then run:\n"
            f"{install_hint}"
        ) from exc


def load_env_file(path: Path = PROJECT_ENV) -> None:
    """Load simple KEY=value lines from the project .env file."""
    # This avoids requiring python-dotenv for a small demo script.
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def configure_api_key() -> bool:
    """Return True for live Claude mode, False for offline mock mode."""
    load_env_file()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        entered = getpass.getpass("ANTHROPIC_API_KEY (blank = offline mock): ")
        if entered:
            os.environ["ANTHROPIC_API_KEY"] = entered

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    # The training .env may contain ANTHROPIC_API_KEY=demo.
    # Treat that as offline mode so the script can run without paid API calls.
    live = bool(api_key and api_key.lower() != "demo")
    print("LIVE mode" if live else "OFFLINE mock mode (no key) - agent loop will be simulated")
    return live


def create_fastapi_backend():
    """Create the tiny external API and return its TestClient."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient

    app = FastAPI()

    # This dictionary acts like a tiny order database for the lab.
    orders = {
        "A1001": {
            "id": "A1001",
            "customer_id": "C001",
            "item": "Mechanical keyboard",
            "qty": 1,
            "status": "shipped",
            "total": 129.0,
        },
        "A1002": {
            "id": "A1002",
            "customer_id": "C002",
            "item": "USB-C hub",
            "qty": 2,
            "status": "processing",
            "total": 58.0,
        },
        "A1003": {
            "id": "A1003",
            "customer_id": "C001",
            "item": "4K monitor",
            "qty": 1,
            "status": "delivered",
            "total": 410.0,
        },
    }
    customers = {
        "C001": {"id": "C001", "name": "Asha Rao", "tier": "gold", "city": "Bengaluru"},
        "C002": {"id": "C002", "name": "Ravi Mehta", "tier": "silver", "city": "Mumbai"},
    }

    @app.get("/orders/{order_id}")
    def get_order(order_id: str):
        order = orders.get(order_id.upper())
        if not order:
            raise HTTPException(status_code=404, detail="order not found")
        return order

    @app.get("/customers/{customer_id}")
    def get_customer(customer_id: str):
        customer = customers.get(customer_id.upper())
        if not customer:
            raise HTTPException(status_code=404, detail="customer not found")
        return customer

    @app.get("/order-summary/{order_id}")
    def get_order_summary(order_id: str):
        order = orders.get(order_id.upper())
        if not order:
            raise HTTPException(status_code=404, detail="order not found")
        customer = customers.get(order["customer_id"])
        return {"order": order, "customer": customer}

    # TestClient lets our agent call the FastAPI app in-process.
    # No uvicorn server or external API hosting is needed.
    return TestClient(app)


class RedisMemory:
    """Short-term conversation history plus long-term facts."""

    def __init__(self, redis_client, session_id: str, history_limit: int = 40):
        self.r = redis_client
        self.sid = session_id
        self.history_limit = history_limit
        self.h_key = f"hist:{session_id}"
        self.f_key = f"facts:{session_id}"
        self.ttl_prefix = f"{self.f_key}:ttl:"

    def append_turn(self, role: str, content) -> None:
        # Store each chat turn as JSON in a Redis list.
        self.r.rpush(self.h_key, json.dumps({"role": role, "content": content}))
        # Keep only the latest history_limit turns to prevent unbounded growth.
        self.r.ltrim(self.h_key, -self.history_limit, -1)

    def load_history(self) -> list[dict]:
        return [json.loads(x) for x in self.r.lrange(self.h_key, 0, -1)]

    def compact_history(self, summarize_fn, max_turns: int = 8, keep_recent: int = 6) -> bool:
        """Summarize older turns when history grows beyond max_turns."""
        history = self.load_history()
        if len(history) <= max_turns:
            return False

        # Old turns are compressed into one synthetic assistant summary.
        # Recent turns stay unchanged because they usually contain important local context.
        old_turns = history[: len(history) - keep_recent]
        recent_turns = history[-keep_recent:]
        summary = summarize_fn(old_turns)
        compacted_history = [
            {
                "role": "assistant",
                "content": f"Conversation summary so far: {summary}",
            },
            *recent_turns,
        ]

        self.r.delete(self.h_key)
        for turn in compacted_history:
            self.r.rpush(self.h_key, json.dumps(turn))
        return True

    def set_fact(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        if ttl_seconds:
            # Redis hash fields do not expire independently, so TTL facts are stored
            # as separate keys. That way one expiring fact does not delete all facts.
            self.r.hdel(self.f_key, key)
            self.r.set(f"{self.ttl_prefix}{key}", value, ex=ttl_seconds)
            return

        self.r.delete(f"{self.ttl_prefix}{key}")
        self.r.hset(self.f_key, key, value)

    def forget_fact(self, key: str) -> bool:
        hash_deleted = self.r.hdel(self.f_key, key)
        ttl_deleted = self.r.delete(f"{self.ttl_prefix}{key}")
        return bool(hash_deleted or ttl_deleted)

    def get_fact(self, key: str):
        ttl_value = self.r.get(f"{self.ttl_prefix}{key}")
        if ttl_value is not None:
            return ttl_value.decode() if isinstance(ttl_value, bytes) else ttl_value

        value = self.r.hget(self.f_key, key)
        return value.decode() if isinstance(value, bytes) else value

    def all_facts(self) -> dict[str, str]:
        facts = {k.decode(): v.decode() for k, v in self.r.hgetall(self.f_key).items()}
        for raw_key in self.r.scan_iter(f"{self.ttl_prefix}*"):
            redis_key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
            fact_key = redis_key.removeprefix(self.ttl_prefix)
            value = self.r.get(raw_key)
            if value is not None:
                facts[fact_key] = value.decode() if isinstance(value, bytes) else value
        return facts


TOOLS = [
    # These schemas are what Claude sees. The model chooses a tool by reading
    # the name, description, and input_schema.
    {
        "name": "get_order",
        "description": "Look up a customer order by its ID and return item, quantity, status and total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID like 'A1001'.",
                    "pattern": "^[Aa][0-9]{4}$",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_customer",
        "description": "Look up a customer by customer ID and return name, loyalty tier, and city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID like 'C001'.",
                    "pattern": "^[Cc][0-9]{3}$",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_order_summary",
        "description": "Look up an order and its customer together by order ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID like 'A1001'.",
                    "pattern": "^[Aa][0-9]{4}$",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "remember_fact",
        "description": "Persist a durable fact about the user for future turns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": 'Short fact key, e.g. "shipping_pref".'},
                "value": {"type": "string", "description": "The fact value to store."},
                "ttl_seconds": {
                    "type": "integer",
                    "description": "Optional time to live in seconds. Omit for no expiry.",
                    "minimum": 1,
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall_fact",
        "description": "Retrieve a previously stored fact about the user by key.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string", "description": "The fact key to look up."}},
            "required": ["key"],
        },
    },
    {
        "name": "forget_fact",
        "description": "Delete a previously stored fact about the user by key.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string", "description": "The fact key to forget."}},
            "required": ["key"],
        },
    },
]

SYSTEM = (
    # The system prompt sets the agent's operating policy.
    "You are an order-support assistant. Use get_order for any order question. "
    "Use get_customer for customer details. If a question asks for multiple independent "
    "records, request the tools together in one turn when possible. "
    "Use remember_fact / recall_fact to keep durable user preferences across turns. "
    "If remember_fact returns an error, explain the safety issue and continue helpfully. "
    "Be concise."
)


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
CARD_RE = re.compile(r"(?:\d[ -]*?){13,19}")


def looks_like_pii(value: str) -> str | None:
    """Return the detected PII type, or None when the value is safe enough for this demo."""
    if EMAIL_RE.search(value):
        return "email address"

    card_match = CARD_RE.search(value)
    if card_match:
        digits = re.sub(r"\D", "", card_match.group())
        if 13 <= len(digits) <= 19:
            return "payment card number"

    return None


def build_tools(client, mem: RedisMemory):
    """Create tool functions and dispatch map."""

    def tool_get_order(order_id: str):
        # Tool 1: read from the FastAPI backend.
        response = client.get(f"/orders/{order_id}")
        if response.status_code == 404:
            return {"error": f"No order {order_id} found."}
        response.raise_for_status()
        return response.json()

    def tool_get_customer(customer_id: str):
        response = client.get(f"/customers/{customer_id}")
        if response.status_code == 404:
            return {"error": f"No customer {customer_id} found."}
        response.raise_for_status()
        return response.json()

    def tool_get_order_summary(order_id: str):
        response = client.get(f"/order-summary/{order_id}")
        if response.status_code == 404:
            return {"error": f"No order {order_id} found."}
        response.raise_for_status()
        return response.json()

    def tool_remember_fact(key: str, value: str, ttl_seconds: int | None = None):
        # Tool 2: write long-term memory.
        pii_type = looks_like_pii(value)
        if pii_type:
            return {
                "error": (
                    f"Refused to store {pii_type}. Store a non-sensitive preference "
                    "or a redacted value instead."
                )
            }
        mem.set_fact(key, value, ttl_seconds=ttl_seconds)
        return {"ok": True, "stored": {key: value}, "ttl_seconds": ttl_seconds}

    def tool_recall_fact(key: str):
        # Tool 3: read long-term memory.
        value = mem.get_fact(key)
        return {"key": key, "value": value} if value is not None else {"key": key, "value": None}

    def tool_forget_fact(key: str):
        # Tool 4: delete long-term memory.
        deleted = mem.forget_fact(key)
        return {"ok": True, "forgot": key, "existed": deleted}

    dispatch = {
        "get_order": tool_get_order,
        "get_customer": tool_get_customer,
        "get_order_summary": tool_get_order_summary,
        "remember_fact": tool_remember_fact,
        "recall_fact": tool_recall_fact,
        "forget_fact": tool_forget_fact,
    }

    def run_tool(name: str, args: dict):
        # This is the trusted boundary: the model requests a tool by name,
        # but our Python code decides what actually runs.
        fn = dispatch.get(name)
        if fn is None:
            return {"error": f"unknown tool {name}"}, True
        try:
            output = fn(**args)
            is_error = isinstance(output, dict) and "error" in output
            return output, is_error
        except Exception as exc:
            return {"error": repr(exc)}, True

    return run_tool


def make_summarizer(live: bool):
    """Use a cheap model in live mode; otherwise use a deterministic local summary."""

    def summarize(old_turns: list[dict]) -> str:
        compact_text = "\n".join(
            f"{turn['role']}: {str(turn['content'])[:500]}" for turn in old_turns
        )

        if not live:
            # Offline mode still demonstrates the compaction pattern without an API key.
            return f"{len(old_turns)} older turns compacted. Key prior context: {compact_text[:700]}"

        try:
            from anthropic import Anthropic

            client = Anthropic()
            response = client.messages.create(
                model=os.getenv("SUMMARY_MODEL", SUMMARY_MODEL),
                max_tokens=200,
                system="Summarize this conversation history for future agent context. Keep facts, preferences, and open tasks.",
                messages=[{"role": "user", "content": compact_text}],
            )
            return "".join(block.text for block in response.content if block.type == "text")
        except Exception as exc:
            return f"Summary fallback after {type(exc).__name__}: {compact_text[:700]}"

    return summarize


def make_agent_turn(live: bool, mem: RedisMemory, run_tool, summarize_fn):
    """Create the Claude or offline-mock agent turn function."""

    def agent_turn(user_text: str, max_steps: int = 6, verbose: bool = True) -> str:
        token_totals = {"input": 0, "output": 0}

        # 1. Save the user turn into memory.
        mem.append_turn("user", user_text)
        # 2. Compact history before sending context to the model.
        if mem.compact_history(summarize_fn):
            print("history compacted")
        messages = mem.load_history()

        if not live:
            # Mock path: useful for class demos and tests when no real Claude key exists.
            lowered = user_text.lower()
            if "a1001" in lowered and "a1003" in lowered:
                if verbose:
                    print("... (mock) model emits two tool_use blocks: get_order A1001 and get_order A1003")
                output_1, _ = run_tool("get_order", {"order_id": "A1001"})
                output_2, _ = run_tool("get_order", {"order_id": "A1003"})
                reply = (
                    "(mock) Parallel lookup complete: "
                    f"A1001 is {output_1.get('status')} for {output_1.get('item')}; "
                    f"A1003 is {output_2.get('status')} for {output_2.get('item')}."
                )
                mem.append_turn("assistant", reply)
                mem.compact_history(summarize_fn)
                if verbose:
                    print("tokens this turn: input=0 output=0 (offline mock)")
                return reply

            if "email" in lowered or "card" in lowered or "@" in user_text:
                if verbose:
                    print("... (mock) model requests remember_fact with sensitive data")
                output, is_error = run_tool("remember_fact", {"key": "sensitive_note", "value": user_text})
                reply = (
                    "(mock) I could not store that because it appears sensitive. "
                    "Please share a non-sensitive preference instead."
                    if is_error
                    else f"(mock) Stored: {output}"
                )
                mem.append_turn("assistant", reply)
                mem.compact_history(summarize_fn)
                if verbose:
                    print("tokens this turn: input=0 output=0 (offline mock)")
                return reply

            if verbose:
                print("... (mock) model requests get_order A1001")
            output, _ = run_tool("get_order", {"order_id": "A1001"})
            reply = f'(mock) Order A1001 is {output.get("status", "?")}.'
            mem.append_turn("assistant", reply)
            mem.compact_history(summarize_fn)
            if verbose:
                print("tokens this turn: input=0 output=0 (offline mock)")
            return reply

        from anthropic import Anthropic

        anthropic_client = Anthropic()
        for _ in range(max_steps):
            # 3. Ask Claude for either a final answer or one/more tool calls.
            response = anthropic_client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                tools=TOOLS,
                messages=messages,
            )
            usage = getattr(response, "usage", None)
            if usage:
                token_totals["input"] += getattr(usage, "input_tokens", 0)
                token_totals["output"] += getattr(usage, "output_tokens", 0)

            if response.stop_reason == "tool_use":
                # 4. Claude requested tools. Run each one and send tool_result blocks back.
                messages.append(
                    {"role": "assistant", "content": [block.model_dump() for block in response.content]}
                )
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if verbose:
                            print(f"  -> tool: {block.name}({block.input})")
                        output, is_error = run_tool(block.name, block.input)
                        results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(output),
                                "is_error": is_error,
                            }
                        )
                messages.append({"role": "user", "content": results})
                continue

            text = "".join(block.text for block in response.content if block.type == "text")
            # 5. Claude ended the turn. Save answer and return it.
            mem.append_turn("assistant", text)
            mem.compact_history(summarize_fn)
            if verbose:
                print(
                    "tokens this turn: "
                    f"input={token_totals['input']} output={token_totals['output']}"
                )
            return text

        return "(stopped: max steps reached)"

    return agent_turn


def run_demo() -> None:
    install_dependencies()
    live = configure_api_key()

    client = create_fastapi_backend()
    print(client.get("/orders/A1001").json())

    import fakeredis

    redis_client = fakeredis.FakeStrictRedis()
    mem = RedisMemory(redis_client, session_id="demo-user")
    mem.set_fact("name", "Asha")
    mem.append_turn("user", "hello")
    print("facts:", mem.all_facts())
    print("history:", mem.load_history())
    print(len(TOOLS), "tools declared")

    run_tool = build_tools(client, mem)
    print(run_tool("get_order", {"order_id": "A1002"}))
    print(run_tool("get_order", {"order_id": "A9999"}))
    print(run_tool("get_customer", {"customer_id": "C001"}))
    print(run_tool("get_order_summary", {"order_id": "A1001"}))

    print("\nTTL + forget tool demo")
    print(run_tool("remember_fact", {"key": "coupon", "value": "SAVE10", "ttl_seconds": 1}))
    print("coupon before expiry:", mem.get_fact("coupon"))
    time.sleep(1.2)
    print("coupon after expiry:", mem.get_fact("coupon"))
    print(run_tool("remember_fact", {"key": "color_pref", "value": "blue"}))
    print(run_tool("forget_fact", {"key": "color_pref"}))
    print("color_pref after forget:", mem.get_fact("color_pref"))

    summarize_fn = make_summarizer(live)
    agent_turn = make_agent_turn(live, mem, run_tool, summarize_fn)

    print(agent_turn("What is the status of order A1002?"))

    print("\nParallel lookup demo")
    print(
        agent_turn(
            "Compare orders A1001 and A1003. Call get_order separately for both order ids in the same turn if possible."
        )
    )

    print("\nGuarded PII write demo")
    print(agent_turn("Please remember that my email is asha@example.com."))

    print(agent_turn("Please remember that my shipping preference is express."))
    print("---")
    print(agent_turn("What did I say my shipping preference was?"))
    print("---")
    print("Raw facts in Redis:", mem.all_facts())
    print("History length:", len(mem.load_history()), "turns")

    for message in [
        "Hi, I am Asha.",
        "How much was order A1003?",
        "Remember that my budget cap is 500 dollars.",
        "Given my budget cap, was that order within it?",
    ]:
        print("USER:", message)
        print("AGENT:", agent_turn(message, verbose=False))
        print()

    print("History length after compaction:", len(mem.load_history()), "turns")
    print("First history entry:", mem.load_history()[0])


if __name__ == "__main__":
    run_demo()
