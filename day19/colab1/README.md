# Day 19 Colab 1 - Claude Agent + FastAPI + Redis Memory

This lab builds a small tool-using agent in Python.

The goal is to understand how an LLM agent can:

1. Receive a user question.
2. Decide when it needs a tool.
3. Call backend tools safely through Python code.
4. Store conversation history and user facts in memory.
5. Compact old history so context stays bounded.

## Files

- `claude_agent_fastapi_redis_memory.py` - runnable Python script.
- `claude_agent_fastapi_redis_memory.ipynb` - original Colab notebook version.

## What The Script Builds

### 1. FastAPI Backend

The script creates a tiny FastAPI app with these endpoints:

```text
GET /orders/{order_id}
GET /customers/{customer_id}
GET /order-summary/{order_id}
```

Example:

```text
/orders/A1001
/customers/C001
/order-summary/A1001
```

This simulates external order and customer systems that the agent can query.

### 2. Redis Memory

The script uses `fakeredis`, so Redis runs in memory and no Redis server is required.

Memory has two parts:

- Short-term memory: conversation turns stored in a Redis list.
- Long-term memory: user facts stored in Redis.

Example facts:

```text
name = Asha
shipping_preference = express
budget_cap = 500 dollars
```

### 3. Claude Tool Use

The script defines tools with JSON schemas:

- `get_order`
- `get_customer`
- `get_order_summary`
- `remember_fact`
- `recall_fact`
- `forget_fact`

Claude sees the tool names, descriptions, and schemas. If it needs a tool, it returns `stop_reason == "tool_use"`.

Then Python runs the tool and sends the result back to Claude.

### 4. Rolling Summary / Compaction

When the conversation history becomes too long, the script summarizes older turns and keeps only:

- one synthetic assistant summary message
- the most recent turns

This keeps the agent context bounded.

In live mode, the summary uses a cheaper Claude model:

```python
SUMMARY_MODEL = "claude-3-5-haiku-latest"
```

In offline mode, it uses a simple local summary.

### 5. TTL And Forget Tool

Facts can expire automatically:

```python
remember_fact(key="coupon", value="SAVE10", ttl_seconds=1)
```

After the TTL expires:

```python
recall_fact("coupon")  # None
```

The agent can also delete facts manually:

```python
forget_fact("color_pref")
```

### 6. Parallel Lookups

Claude can request more than one tool in the same turn.

The demo asks about two order IDs:

```text
Compare orders A1001 and A1003.
```

In live mode, Claude can emit two `tool_use` blocks in one response. The Python loop handles every `tool_use` block, returns one `tool_result` per ID, and then lets Claude answer with both results.

In offline mock mode, the script simulates the same pattern.

### 7. Guarded Writes / PII Safety

The `remember_fact` tool refuses to store values that look like:

- email addresses
- payment card numbers

Example:

```text
Please remember that my email is asha@example.com.
```

The tool returns an error result instead of storing the value. The agent can then explain the safety issue and ask for a non-sensitive preference.

### 8. Token Accounting

In live mode, each Claude response includes usage metadata.

The script reads:

```python
response.usage.input_tokens
response.usage.output_tokens
```

It prints cumulative tokens for each agent turn:

```text
tokens this turn: input=... output=...
```

In offline mock mode, token usage prints as zero because no model call is made.

## Run

From this folder:

```bash
python3 claude_agent_fastapi_redis_memory.py
```

Or from the project root:

```bash
python3 Ey_training_genai/day19/colab1/claude_agent_fastapi_redis_memory.py
```

## API Key Behavior

The script reads:

```text
Ey_training_genai/.env
```

If `ANTHROPIC_API_KEY=demo`, the script runs in offline mock mode.

For live Claude calls, replace it with a real Anthropic key:

```env
ANTHROPIC_API_KEY=your_real_key
```

## Expected Output

The script demonstrates:

- order lookup
- customer lookup
- parallel order lookups
- missing order error handling
- fact storage
- guarded PII write rejection
- TTL expiry returning `None`
- forgetting a fact
- token accounting
- rolling history compaction
- multi-turn agent interaction

## Key Learning

The LLM does not directly call APIs or write memory.

Instead:

1. Claude asks for a tool.
2. Python validates and runs the tool.
3. Python returns the tool result.
4. Claude uses that result to answer.

That separation is what makes tool-using agents safer and easier to debug.
