"""Day 19 Take-home Capstone - Support Agent.

This script extends Lab 2 into a small support agent with:

1. Redis short-term memory.
2. A simple vector store for long-term policy recall.
3. More than three tools, including one async queue-backed email tool.
4. Routing and tool chaining with a human-approval gate.
5. Tracing, retries, and prompt-cache/token reporting hooks.

Run:
    python3 support_agent_capstone.py

If ANTHROPIC_API_KEY is missing or set to "demo", the script runs in offline mock mode.
"""

from __future__ import annotations

import getpass
import importlib.util
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any


MODEL = "claude-sonnet-4-6"
PROJECT_ENV = Path(__file__).resolve().parents[2] / ".env"

# Redis Stream names. A stream is acting like a lightweight job queue here.
EMAIL_STREAM = "support:emails"
EMAIL_GROUP = "support-mailers"

# Business safety rule: refunds above this amount need human approval.
APPROVAL_THRESHOLD = 100.0


def install_dependencies() -> None:
    """Install small runtime dependencies when missing."""
    # The script can run from a plain Python file, so we check dependencies
    # instead of relying on notebook-only `!pip install` cells.
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
    """Load simple KEY=value lines from the project .env file."""
    # This intentionally avoids printing values because .env files contain secrets.
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
    # In this training repo, ANTHROPIC_API_KEY=demo means "do not call Claude".
    live = bool(api_key and api_key.lower() != "demo")
    print("LIVE mode" if live else "OFFLINE mock mode")
    return live


def create_redis():
    """Create fakeredis and the async email stream consumer group."""
    import fakeredis

    redis_client = fakeredis.FakeStrictRedis()
    try:
        # Consumer groups let workers claim messages and ack them after processing.
        redis_client.xgroup_create(EMAIL_STREAM, EMAIL_GROUP, id="0", mkstream=True)
    except Exception:
        pass
    return redis_client


class ShortTermMemory:
    """Redis-backed conversation memory."""

    def __init__(self, redis_client, session_id: str, limit: int = 20):
        self.redis = redis_client
        self.key = f"support:history:{session_id}"
        self.limit = limit

    def append(self, role: str, content: str) -> None:
        # Store each turn as JSON so it can be passed back to the agent later.
        self.redis.rpush(self.key, json.dumps({"role": role, "content": content}))
        # Keep memory bounded. Real systems often compact or summarize older turns.
        self.redis.ltrim(self.key, -self.limit, -1)

    def load(self) -> list[dict[str, str]]:
        return [json.loads(item) for item in self.redis.lrange(self.key, 0, -1)]


def tokenize(text: str) -> list[str]:
    # Small tokenizer for the demo vector store.
    return re.findall(r"[a-z0-9]+", text.lower())


class SimpleVectorStore:
    """Tiny bag-of-words vector store for long-term policy recall."""

    def __init__(self, docs: list[dict[str, str]]):
        self.docs = docs
        # Each policy document becomes a simple word-count vector.
        # In production this would usually be an embedding model + vector DB.
        self.vectors = [Counter(tokenize(doc["text"])) for doc in docs]

    @staticmethod
    def cosine(left: Counter, right: Counter) -> float:
        common = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in common)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)

    def search(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        # Convert the query to the same vector format, score every document,
        # and return the closest policy matches.
        query_vector = Counter(tokenize(query))
        scored = [
            {"id": doc["id"], "title": doc["title"], "text": doc["text"], "score": self.cosine(query_vector, vector)}
            for doc, vector in zip(self.docs, self.vectors)
        ]
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def create_vector_store() -> SimpleVectorStore:
    """Seed long-term support policies."""
    # These documents are the "long-term memory" the support agent can retrieve.
    docs = [
        {
            "id": "refund-delay",
            "title": "Delay refund policy",
            "text": "If a shipped order is delayed more than 5 days, support may offer refund or replacement. Refunds over 100 dollars require human approval.",
        },
        {
            "id": "damaged-item",
            "title": "Damaged item policy",
            "text": "For damaged items, create a support ticket, request photo evidence, and offer replacement before refund unless the customer insists.",
        },
        {
            "id": "email-followup",
            "title": "Customer follow-up policy",
            "text": "All refund or replacement decisions must be followed by an email confirmation. Email sending is asynchronous through the support queue.",
        },
    ]
    return SimpleVectorStore(docs)


def create_database() -> sqlite3.Connection:
    """Create support data: orders, tickets, refunds, approvals."""
    # SQLite stands in for operational systems: order DB, ticketing DB,
    # refund ledger, and human-approval records.
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.execute(
        "CREATE TABLE orders (id TEXT PRIMARY KEY, customer_email TEXT, item TEXT, status TEXT, days_delayed INTEGER, total REAL)"
    )
    db.execute(
        "CREATE TABLE tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, category TEXT, summary TEXT, priority TEXT, status TEXT)"
    )
    db.execute(
        "CREATE TABLE refunds (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, amount REAL, status TEXT, reason TEXT)"
    )
    db.execute(
        "CREATE TABLE approvals (id TEXT PRIMARY KEY, order_id TEXT, amount REAL, reason TEXT, status TEXT)"
    )
    db.executemany(
        "INSERT INTO orders VALUES (?,?,?,?,?,?)",
        [
            ("A1001", "asha@example.com", "Mechanical keyboard", "shipped", 2, 129.0),
            ("A1002", "ravi@example.com", "USB-C hub", "processing", 0, 58.0),
            ("A1003", "asha@example.com", "4K monitor", "shipped", 7, 410.0),
        ],
    )
    db.commit()
    return db


class TraceRecorder:
    """Collect per-tool spans for observability."""

    def __init__(self):
        self.spans: list[dict[str, Any]] = []

    def record(self, tool: str, args: dict, ms: float, ok: bool, attempts: int) -> None:
        # One span per tool call. This makes agent behavior auditable.
        self.spans.append({"tool": tool, "args": args, "ms": round(ms, 2), "ok": ok, "attempts": attempts})

    def print_table(self) -> None:
        print("\nTrace spans:")
        for span in self.spans:
            print(
                f"  {span['tool']:<22} ok={span['ok']!s:<5} "
                f"attempts={span['attempts']} ms={span['ms']:<7} args={span['args']}"
            )


def enqueue_email(redis_client, to: str, subject: str, body: str) -> str:
    """Async queue-backed tool implementation."""
    job_id = uuid.uuid4().hex[:8]
    # XADD puts the email request on the stream. The agent gets a job_id now;
    # a worker can process the slow email side effect separately.
    redis_client.xadd(EMAIL_STREAM, {"job_id": job_id, "to": to, "subject": subject, "body": body})
    redis_client.set(f"support:job:{job_id}", "queued")
    return job_id


def run_email_worker(redis_client, max_msgs: int = 10) -> int:
    """Process queued email jobs."""
    processed = 0
    response = redis_client.xreadgroup(EMAIL_GROUP, "worker-1", {EMAIL_STREAM: ">"}, count=max_msgs)
    for _stream, messages in response or []:
        for msg_id, fields in messages:
            data = {key.decode(): value.decode() for key, value in fields.items()}
            # A real worker would call SendGrid, SES, etc. This demo marks the job sent.
            redis_client.set(f"support:job:{data['job_id']}", "sent")
            # XACK confirms the worker finished the message.
            redis_client.xack(EMAIL_STREAM, EMAIL_GROUP, msg_id)
            processed += 1
    return processed


def build_tools(db: sqlite3.Connection, redis_client, vector_store: SimpleVectorStore, trace: TraceRecorder):
    """Create support tools with retries and tracing."""
    # Used to show retry behavior. The first email attempt fails, then retry succeeds.
    flaky_email_once = {"should_fail": True}

    def recall_policy(query: str):
        # Tool: retrieve policy guidance before making support decisions.
        return {"matches": vector_store.search(query)}

    def lookup_order(order_id: str):
        # Tool: read operational order state from SQLite.
        row = db.execute(
            "SELECT id,customer_email,item,status,days_delayed,total FROM orders WHERE id=? LIMIT 1",
            (order_id.upper(),),
        ).fetchone()
        if not row:
            return {"error": f"unknown order {order_id}"}
        return {
            "order_id": row[0],
            "customer_email": row[1],
            "item": row[2],
            "status": row[3],
            "days_delayed": row[4],
            "total": row[5],
        }

    def create_ticket(order_id: str, category: str, summary: str, priority: str = "medium"):
        # Tool: create an audit trail for the support case.
        cursor = db.execute(
            "INSERT INTO tickets (order_id,category,summary,priority,status) VALUES (?,?,?,?,?)",
            (order_id.upper(), category, summary, priority, "open"),
        )
        db.commit()
        return {"ticket_id": cursor.lastrowid, "status": "open", "priority": priority}

    def request_refund(order_id: str, amount: float, reason: str):
        # Tool: either approve small refunds immediately or request human approval.
        if amount > APPROVAL_THRESHOLD:
            approval_id = uuid.uuid4().hex[:8]
            db.execute(
                "INSERT INTO approvals VALUES (?,?,?,?,?)",
                (approval_id, order_id.upper(), amount, reason, "pending"),
            )
            db.commit()
            return {
                "status": "needs_approval",
                "approval_id": approval_id,
                "message": f"Refund ${amount} requires human approval.",
            }

        cursor = db.execute(
            "INSERT INTO refunds (order_id,amount,status,reason) VALUES (?,?,?,?)",
            (order_id.upper(), amount, "approved", reason),
        )
        db.commit()
        return {"refund_id": cursor.lastrowid, "status": "approved", "amount": amount}

    def approve_refund(approval_id: str, approved: bool = True):
        # Tool: models a human-in-the-loop approval decision.
        row = db.execute("SELECT order_id,amount,reason,status FROM approvals WHERE id=?", (approval_id,)).fetchone()
        if not row:
            return {"error": f"unknown approval {approval_id}"}
        if row[3] != "pending":
            return {"error": f"approval {approval_id} is already {row[3]}"}

        status = "approved" if approved else "rejected"
        db.execute("UPDATE approvals SET status=? WHERE id=?", (status, approval_id))
        if approved:
            db.execute(
                "INSERT INTO refunds (order_id,amount,status,reason) VALUES (?,?,?,?)",
                (row[0], row[1], "approved", row[2]),
            )
        db.commit()
        return {"approval_id": approval_id, "status": status, "amount": row[1]}

    def send_followup_email(to: str, subject: str, body: str):
        # Simulate one transient provider error so retry behavior is visible.
        if flaky_email_once["should_fail"]:
            flaky_email_once["should_fail"] = False
            raise RuntimeError("temporary email provider timeout")
        job_id = enqueue_email(redis_client, to, subject, body)
        return {"job_id": job_id, "status": "queued"}

    def check_email_job(job_id: str):
        # Tool: read the async job status after the worker has had a chance to run.
        value = redis_client.get(f"support:job:{job_id}")
        return {"job_id": job_id, "status": value.decode() if value else "unknown"}

    dispatch = {
        "recall_policy": recall_policy,
        "lookup_order": lookup_order,
        "create_ticket": create_ticket,
        "request_refund": request_refund,
        "approve_refund": approve_refund,
        "send_followup_email": send_followup_email,
        "check_email_job": check_email_job,
    }

    def run_tool(name: str, args: dict, retries: int = 2):
        # Central execution boundary. The LLM asks for a tool, but only this
        # trusted Python function actually executes it.
        fn = dispatch.get(name)
        if fn is None:
            return {"error": f"unknown tool {name}"}, True

        started = time.perf_counter()
        attempts = 0
        last_error = None
        for attempt in range(1, retries + 2):
            attempts = attempt
            try:
                output = fn(**args)
                is_error = isinstance(output, dict) and "error" in output
                # Record both successful and business-error tool calls.
                trace.record(name, args, (time.perf_counter() - started) * 1000, not is_error, attempts)
                return output, is_error
            except Exception as exc:
                last_error = exc
                if attempt <= retries:
                    # Short backoff before retrying transient failures.
                    time.sleep(0.05 * attempt)
                    continue

        trace.record(name, args, (time.perf_counter() - started) * 1000, False, attempts)
        return {"error": repr(last_error)}, True

    return run_tool


TOOLS = [
    # These JSON schemas are sent to Claude. Claude reads the descriptions
    # and decides which tool to request, but it does not execute them directly.
    {
        "name": "recall_policy",
        "description": "Search long-term support policy memory for relevant refund, replacement, or follow-up rules.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Look up order details including email, item, status, delay days, and total.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID like A1003."}},
            "required": ["order_id"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Create a support ticket for a customer issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "category": {"type": "string"},
                "summary": {"type": "string"},
                "priority": {"type": "string"},
            },
            "required": ["order_id", "category", "summary"],
        },
    },
    {
        "name": "request_refund",
        "description": "Request a refund. Refunds above the approval threshold return needs_approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["order_id", "amount", "reason"],
        },
    },
    {
        "name": "approve_refund",
        "description": "Human approval gate for a pending refund approval_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "approval_id": {"type": "string"},
                "approved": {"type": "boolean"},
            },
            "required": ["approval_id"],
        },
    },
    {
        "name": "send_followup_email",
        "description": "Queue a follow-up email asynchronously. Returns a job_id immediately.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "check_email_job",
        "description": "Check the async email job status by job_id.",
        "input_schema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
]

SYSTEM = (
    # This is the high-level operating policy for the live Claude agent.
    "You are a support agent. Use policy recall before deciding on refunds or replacements. "
    "For delayed orders, look up the order, create a ticket, request the refund if appropriate, "
    "use the human approval gate when a tool returns needs_approval, then queue a follow-up email. "
    "Report ticket, refund/approval, email job status, and any policy used."
)


def make_agent(live: bool, memory: ShortTermMemory, run_tool, redis_client):
    """Create live Claude agent or deterministic offline capstone flow."""

    def agent(user_text: str, max_steps: int = 10, verbose: bool = True) -> str:
        # Save the user's latest request into short-term Redis memory.
        memory.append("user", user_text)

        if not live:
            # Offline mode follows the exact intended orchestration path without
            # making a paid model call. This is useful for demos and testing.
            if verbose:
                print("... (mock) routing -> policy recall -> order lookup -> ticket -> approval -> email queue")

            # 1. Retrieve policy guidance from long-term vector memory.
            policy, _ = run_tool("recall_policy", {"query": "delayed shipped order refund over 100"})

            # 2. Look up the operational order record.
            order, _ = run_tool("lookup_order", {"order_id": "A1003"})

            # 3. Create a support ticket for auditability.
            ticket, _ = run_tool(
                "create_ticket",
                {
                    "order_id": "A1003",
                    "category": "delay_refund",
                    "summary": "Customer requests support for delayed 4K monitor.",
                    "priority": "high",
                },
            )

            # 4. Request a refund. Since the amount is > $100, this returns
            #    needs_approval instead of finalizing immediately.
            refund, _ = run_tool(
                "request_refund",
                {"order_id": "A1003", "amount": order["total"], "reason": "shipped order delayed 7 days"},
            )
            if refund.get("status") == "needs_approval":
                # 5. Human-in-the-loop gate. The demo auto-approves so the
                #    full flow can finish in one run.
                approval, _ = run_tool("approve_refund", {"approval_id": refund["approval_id"], "approved": True})
            else:
                approval = refund

            # 6. Queue customer communication asynchronously.
            email, _ = run_tool(
                "send_followup_email",
                {
                    "to": order["customer_email"],
                    "subject": "Support update for order A1003",
                    "body": "Your delayed order refund has been approved. We are sorry for the delay.",
                },
            )

            # 7. Worker processes the queue; the agent then checks job status.
            run_email_worker(redis_client)
            email_status, _ = run_tool("check_email_job", {"job_id": email["job_id"]})
            reply = (
                f"(mock) Ticket {ticket['ticket_id']} opened. Refund approval {approval['status']} "
                f"for ${approval['amount']}. Email job {email_status['status']}. "
                f"Policy used: {policy['matches'][0]['title']}."
            )
            memory.append("assistant", reply)
            return reply

        from anthropic import Anthropic

        client = Anthropic()
        # Live mode starts with all remembered turns, including the latest user turn.
        messages = memory.load()
        cache_hits = {"input": 0, "output": 0, "cache_read": 0}
        for _ in range(max_steps):
            # Ask Claude to either answer or request tools.
            # The system prompt is cache-marked so repeated runs can save tokens.
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                tools=TOOLS,
                messages=messages,
            )
            usage = getattr(response, "usage", None)
            if usage:
                # Token accounting: useful for cost and prompt-cache analysis.
                cache_hits["input"] += getattr(usage, "input_tokens", 0)
                cache_hits["output"] += getattr(usage, "output_tokens", 0)
                cache_hits["cache_read"] += getattr(usage, "cache_read_input_tokens", 0)

            if response.stop_reason == "tool_use":
                # Claude may request one or more tools. We echo its tool_use
                # blocks back into the transcript, then append matching results.
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
                # Drain async email jobs between model steps so check_email_job
                # can observe the updated status.
                run_email_worker(redis_client)
                continue

            text = "".join(block.text for block in response.content if block.type == "text")
            # Final model answer: persist it to short-term memory.
            memory.append("assistant", text)
            if verbose:
                print(
                    "tokens: "
                    f"input={cache_hits['input']} output={cache_hits['output']} "
                    f"cache_read={cache_hits['cache_read']}"
                )
            return text

        return "(max steps reached)"

    return agent


def print_state(db: sqlite3.Connection, trace: TraceRecorder, memory: ShortTermMemory) -> None:
    """Print final state so learners can inspect side effects."""
    print("\nTickets:")
    for row in db.execute("SELECT id,order_id,category,priority,status FROM tickets").fetchall():
        print(" ", row)

    print("Refunds:")
    for row in db.execute("SELECT id,order_id,amount,status,reason FROM refunds").fetchall():
        print(" ", row)

    print("Approvals:")
    for row in db.execute("SELECT id,order_id,amount,status FROM approvals").fetchall():
        print(" ", row)

    print("\nShort-term memory:")
    for turn in memory.load():
        print(" ", turn)

    trace.print_table()


def run_demo() -> None:
    """Wire all components together and run one support-agent scenario."""
    install_dependencies()
    live = configure_api_key()

    # Infrastructure / state stores.
    redis_client = create_redis()
    db = create_database()
    vector_store = create_vector_store()
    memory = ShortTermMemory(redis_client, session_id="capstone-demo")

    # Observability and executable tools.
    trace = TraceRecorder()
    run_tool = build_tools(db, redis_client, vector_store, trace)
    agent = make_agent(live, memory, run_tool, redis_client)

    # Scenario: high-value delayed order, so approval gate should be triggered.
    prompt = "Customer says order A1003 is very delayed and wants a refund plus an email update."
    print(agent(prompt))
    print_state(db, trace, memory)


if __name__ == "__main__":
    run_demo()
