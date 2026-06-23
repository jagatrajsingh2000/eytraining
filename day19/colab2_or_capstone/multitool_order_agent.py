"""Day 19 Colab 2 / Capstone - Multi-tool Agent + Redis Event Queue.

This is the Python script version of the Colab notebook.

It demonstrates:
1. SQLite inventory and orders tables.
2. A Redis Stream email queue using fakeredis.
3. A worker that consumes queued email jobs.
4. A Claude tool-use loop that chains:
   check_inventory -> create_order -> send_confirmation -> check_job

Run:
    python3 multitool_order_agent.py

If ANTHROPIC_API_KEY is missing or set to "demo", the script runs in offline mock mode.
"""

from __future__ import annotations

import getpass
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path


MODEL = "claude-sonnet-4-6"
PROJECT_ENV = Path(__file__).resolve().parents[2] / ".env"
STREAM = "emails"
GROUP = "mailers"


def install_dependencies() -> None:
    """Install dependencies used by the capstone if they are missing."""
    required = {
        "anthropic": "anthropic",
        "fakeredis": "fakeredis",
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
        raise RuntimeError(
            "Missing dependencies could not be installed automatically. "
            "Activate a virtual environment first, then run:\n"
            f"{' '.join(command)}"
        ) from exc


def load_env_file(path: Path = PROJECT_ENV) -> None:
    """Load simple KEY=value pairs from Ey_training_genai/.env."""
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
    live = bool(api_key and api_key.lower() != "demo")
    print("LIVE mode" if live else "OFFLINE mock mode")
    return live


def create_database() -> sqlite3.Connection:
    """Create an in-memory SQLite database for inventory and orders."""
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.execute("CREATE TABLE inventory (sku TEXT PRIMARY KEY, name TEXT, qty INTEGER, price REAL)")
    db.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, qty INTEGER, total REAL, status TEXT)"
    )
    db.executemany(
        "INSERT INTO inventory VALUES (?,?,?,?)",
        [
            ("KB-01", "Mechanical keyboard", 12, 129.0),
            ("HUB-2", "USB-C hub", 0, 58.0),
            ("MON-4", "4K monitor", 5, 410.0),
        ],
    )
    db.commit()
    print("inventory seeded")
    return db


def create_queue():
    """Create a fakeredis stream and consumer group for email jobs."""
    import fakeredis

    redis_client = fakeredis.FakeStrictRedis()
    try:
        redis_client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except Exception as exc:
        print("group exists:", exc)
    return redis_client


def enqueue_email(redis_client, to: str, subject: str, body: str) -> str:
    """Async boundary: enqueue email work and return immediately."""
    job_id = uuid.uuid4().hex[:8]
    redis_client.xadd(STREAM, {"job_id": job_id, "to": to, "subject": subject, "body": body})
    redis_client.set(f"jobresult:{job_id}", "queued")
    return job_id


def run_worker(redis_client, max_msgs: int = 10) -> int:
    """Drain queued email jobs through a Redis consumer group."""
    processed = 0
    response = redis_client.xreadgroup(GROUP, "worker-1", {STREAM: ">"}, count=max_msgs)
    for _stream, messages in response or []:
        for msg_id, fields in messages:
            decoded = {key.decode(): value.decode() for key, value in fields.items()}
            # In production, this is where a real email provider would be called.
            redis_client.set(f"jobresult:{decoded['job_id']}", "sent")
            redis_client.xack(STREAM, GROUP, msg_id)
            processed += 1
    return processed


def build_tools(db: sqlite3.Connection, redis_client):
    """Create sync SQLite tools and async Redis Stream tools."""

    def check_inventory(sku: str):
        row = db.execute(
            "SELECT sku,name,qty,price FROM inventory WHERE sku=? LIMIT 1", (sku,)
        ).fetchone()
        if not row:
            return {"error": f"unknown sku {sku}"}
        return {"sku": row[0], "name": row[1], "qty": row[2], "price": row[3]}

    def create_order(sku: str, qty: int):
        current = db.execute("SELECT qty,price FROM inventory WHERE sku=? LIMIT 1", (sku,)).fetchone()
        if not current:
            return {"error": f"unknown sku {sku}"}

        have, price = current
        if qty <= 0:
            return {"error": "qty must be positive"}
        if have < qty:
            return {"error": f"insufficient stock: have {have}, need {qty}"}

        db.execute("UPDATE inventory SET qty=qty-? WHERE sku=?", (qty, sku))
        cursor = db.execute(
            "INSERT INTO orders (sku,qty,total,status) VALUES (?,?,?,?)",
            (sku, qty, round(price * qty, 2), "created"),
        )
        db.commit()
        return {"order_id": cursor.lastrowid, "sku": sku, "qty": qty, "total": round(price * qty, 2)}

    def send_confirmation(to: str, order_id: int):
        job_id = enqueue_email(
            redis_client,
            to,
            f"Order {order_id} confirmed",
            f"Your order {order_id} is on its way.",
        )
        return {"job_id": job_id, "status": "queued"}

    def check_job(job_id: str):
        value = redis_client.get(f"jobresult:{job_id}")
        return {"job_id": job_id, "status": value.decode() if value else "unknown"}

    dispatch = {
        "check_inventory": check_inventory,
        "create_order": create_order,
        "send_confirmation": send_confirmation,
        "check_job": check_job,
    }

    def run_tool(name: str, args: dict):
        fn = dispatch.get(name)
        if fn is None:
            return {"error": f"unknown tool {name}"}, True
        try:
            output = fn(**args)
            return output, isinstance(output, dict) and "error" in output
        except Exception as exc:
            return {"error": repr(exc)}, True

    return run_tool


TOOLS = [
    {
        "name": "check_inventory",
        "description": "Check stock and price for a product SKU before ordering.",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string", "description": "Product SKU, e.g. KB-01."}},
            "required": ["sku"],
        },
    },
    {
        "name": "create_order",
        "description": "Create an order for a SKU and quantity. Fails if stock is insufficient.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string"},
                "qty": {"type": "integer", "description": "Units to order (>0)."},
            },
            "required": ["sku", "qty"],
        },
    },
    {
        "name": "send_confirmation",
        "description": "Queue a confirmation email for a created order. Returns a job_id immediately.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Customer email."},
                "order_id": {"type": "integer"},
            },
            "required": ["to", "order_id"],
        },
    },
    {
        "name": "check_job",
        "description": "Check the status of a queued email job by job_id.",
        "input_schema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
]

SYSTEM = (
    "You are an ordering agent. To place an order: first check_inventory, then create_order, "
    "then send_confirmation with the returned order_id. Report the order total and the email job status. "
    "If stock is insufficient, say so and do not create the order."
)


def make_agent(live: bool, run_tool, redis_client):
    """Create the live Claude loop or offline mock orchestration."""

    def agent(user_text: str, max_steps: int = 8, verbose: bool = True) -> str:
        if not live:
            if verbose:
                print("... (mock) chaining check_inventory -> create_order -> send_confirmation")
            inventory, is_error = run_tool("check_inventory", {"sku": "MON-4"})
            if is_error:
                return f"(mock) Inventory check failed: {inventory['error']}"

            order, is_error = run_tool("create_order", {"sku": "MON-4", "qty": 1})
            if is_error:
                return f"(mock) Order failed: {order['error']}"

            job, _ = run_tool("send_confirmation", {"to": "asha@x.com", "order_id": order["order_id"]})
            run_worker(redis_client)
            status, _ = run_tool("check_job", {"job_id": job["job_id"]})
            return f"(mock) Order {order['order_id']} total ${order['total']}; email {status['status']}."

        from anthropic import Anthropic

        anthropic_client = Anthropic()
        messages = [{"role": "user", "content": user_text}]
        for _ in range(max_steps):
            response = anthropic_client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                messages.append(
                    {"role": "assistant", "content": [block.model_dump() for block in response.content]}
                )
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if verbose:
                            print(f"  -> {block.name}({block.input})")
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
                run_worker(redis_client)
                continue

            return "".join(block.text for block in response.content if block.type == "text")

        return "(max steps reached)"

    return agent


def print_state(db: sqlite3.Connection, run_tool) -> None:
    """Print database state and an out-of-stock failure example."""
    print("Orders table:")
    for row in db.execute("SELECT id,sku,qty,total,status FROM orders").fetchall():
        print(" ", row)

    print("Remaining stock:")
    for row in db.execute("SELECT sku,qty FROM inventory").fetchall():
        print(" ", row)

    print("Out-of-stock attempt:", run_tool("create_order", {"sku": "HUB-2", "qty": 1}))


def run_demo() -> None:
    install_dependencies()
    live = configure_api_key()
    db = create_database()
    redis_client = create_queue()

    sample_job_id = enqueue_email(redis_client, "a@x.com", "hi", "test")
    print("queue ready; sample job id ->", sample_job_id)
    print("worker processed", run_worker(redis_client), "job(s)")

    run_tool = build_tools(db, redis_client)

    inventory, _ = run_tool("check_inventory", {"sku": "KB-01"})
    print(inventory)
    order, _ = run_tool("create_order", {"sku": "KB-01", "qty": 2})
    print(order)
    job, _ = run_tool("send_confirmation", {"to": "asha@x.com", "order_id": order["order_id"]})
    print(job)
    run_worker(redis_client)
    print(run_tool("check_job", {"job_id": job["job_id"]})[0])
    print("tools ready")

    agent = make_agent(live, run_tool, redis_client)
    print(agent("Order one 4K monitor (SKU MON-4) and email asha@x.com the confirmation."))
    print_state(db, run_tool)


if __name__ == "__main__":
    run_demo()
