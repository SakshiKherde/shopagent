# Getting Started: Google ADK + Neo4j Agent Memory

A 10-minute walkthrough showing how to give a Google ADK + Gemini agent
a complete memory system using the official **`neo4j-agent-memory`**
library from Neo4j Labs.

## What You'll Build

A shopping assistant where Gemini has all three types of agent memory:

- **Long-term memory** — entities, facts, and preferences that persist
  across sessions, with automatic embedding and entity resolution
- **Short-term memory** — current session messages, conversation chains,
  and contextual recall
- **Reasoning memory** — decision traces the agent can search and reuse
  to avoid re-running expensive multi-step reasoning from scratch

All powered by Neo4j as the knowledge layer.

## Prerequisites

- Python 3.10–3.12
- Neo4j Aura instance (free tier works) — https://console.neo4j.io
- Gemini API key with billing enabled — https://aistudio.google.com/apikey

## Step 1 — Install

```bash
pip install neo4j-agent-memory[google-adk]
```

This installs the agent memory library plus the `google-adk` extras
(ADK, google-genai, and the Vertex AI embedder).

## Step 2 — Set environment variables

```
GOOGLE_API_KEY=AIza...
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

## Step 3 — Connect the memory client

```python
from neo4j_agent_memory import MemoryClient, MemorySettings, Neo4jConfig

settings = MemorySettings(
    neo4j=Neo4jConfig(
        uri=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
    )
)

async with MemoryClient(settings=settings) as client:
    # client.long_term  — entities, facts, preferences
    # client.short_term — messages, conversations
    # client.reasoning  — decision traces and tool calls
    ...
```

That's the entire connection setup. The library handles embeddings,
entity resolution, deduplication, and graph schema for you.

## Step 4 — Wire the memory tools to a Gemini agent

```python
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool

async def recall_user_context(user_id: str, query: str = "") -> dict:
    """Pull persistent user context — entities, prefs, facts."""
    entities = await client.long_term.search_entities(query=user_id, limit=10)
    preferences = await client.long_term.search_preferences(query=query or "", limit=10)
    facts = await client.long_term.search_facts(query=f"facts about {user_id}", limit=10)
    return {"entities": entities, "preferences": preferences, "facts": facts}

async def recall_reasoning_patterns(task: str, limit: int = 3) -> dict:
    """Find similar past reasoning traces — reuse instead of recompute."""
    similar = await client.reasoning.get_similar_traces(
        task=task, limit=limit, success_only=True,
    )
    return {"similar_traces": similar}

async def get_unified_context(query: str, session_id: str) -> dict:
    """One call → context from all three memory types."""
    return {"context": await client.get_context(query, session_id=session_id)}

agent = Agent(
    model="gemini-2.0-flash",
    name="ShopAgent",
    instruction="You are a shopping assistant with persistent memory...",
    tools=[
        FunctionTool(func=recall_user_context),
        FunctionTool(func=recall_reasoning_patterns),
        FunctionTool(func=get_unified_context),
    ],
)
```

## Step 5 — Seed your customer profile (optional, demo only)

The library starts with an empty memory. For a demo, populate it with
a sample customer first:

```python
from neo4j_agent_memory import EntityType

async with MemoryClient(settings=settings) as client:
    # Create the customer entity
    alex, _ = await client.long_term.add_entity(
        name="Alex Chen",
        entity_type=EntityType.PERSON,
        attributes={"foot_width": "narrow", "primary_size": 9.5},
    )

    # Add preferences
    await client.long_term.add_preference(
        category="fit",
        preference="narrow width with snug heel and roomy toe box",
    )

    # Add facts (purchases, rejections, notes)
    await client.long_term.add_fact(
        subject="Alex Chen",
        predicate="purchased",
        obj="Brooks Ghost 15 (rated 4 stars)",
    )

    # Record a past reasoning trace so the agent can find/reuse it
    trace = await client.reasoning.start_trace(
        session_id="session-001",
        task="recommend running shoes for narrow-footed runner",
    )
    await client.reasoning.complete_trace(
        trace_id=trace.id,
        outcome="Recommended Saucony Kinvara 14N (91% match) - accepted",
        success=True,
    )
```

See `agent/seed_agent_memory.py` in this repo for a complete example.

## Step 6 — Run the agent and persist the trace

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

session_service = InMemorySessionService()
await session_service.create_session(
    app_name="ShopAgent", user_id="alex", session_id="session-001"
)

runner = Runner(agent=agent, app_name="ShopAgent", session_service=session_service)

# 1. Persist the user message to short-term memory
await client.short_term.add_message(
    session_id="session-001", role="user", content="I need new running shoes"
)

# 2. Start a reasoning trace
trace = await client.reasoning.start_trace(
    session_id="session-001", task="recommend running shoes"
)

# 3. Run the agent
async for event in runner.run_async(
    user_id="alex",
    session_id="session-001",
    new_message=genai_types.Content(
        role="user",
        parts=[genai_types.Part(text="I need new running shoes")],
    ),
):
    if event.is_final_response():
        print(event.content.parts[0].text)

# 4. Complete the reasoning trace
await client.reasoning.complete_trace(
    trace_id=trace.id, outcome="recommended Kinvara 14N", success=True
)
```

## What Happens Under the Hood

1. **Message arrives** → `client.short_term.add_message()` records it,
   auto-embeds it, and chains it to the previous message in the session.
2. **Reasoning trace starts** → `client.reasoning.start_trace()` creates
   a `ReasoningTrace` node linked to the session and the triggering message.
3. **Gemini calls memory tools** → ADK invokes the Python functions you
   wrote, which use `client.long_term.search_*()` to pull relevant context.
4. **Each tool call is recorded** → ADK fires events that you (or the
   library) can persist as `ReasoningStep` and `ToolCall` nodes for full
   audit trail.
5. **Gemini reasons and responds** → It composes a final answer using
   the retrieved memory and its own knowledge.
6. **Reply persisted + trace completed** → `add_message()` stores the
   assistant reply, `complete_trace()` finalizes the reasoning trace
   with an outcome and success flag.

## The Three Memory Types in Action

| Memory Type | Library Path | What It Stores |
|---|---|---|
| **Short-term** | `client.short_term` | Messages, conversations, sessions |
| **Long-term** | `client.long_term` | Entities, facts, preferences (with embeddings) |
| **Reasoning** | `client.reasoning` | Traces, steps, tool calls — reusable patterns |

You can also call `client.get_context(query)` once and the library
pulls relevant items from all three for you.

## Why This Beats Vector Search Alone

- **Entity resolution built in** — `add_entity()` deduplicates and
  resolves entities across mentions automatically
- **Schema-aware retrieval** — search by entity type, fact predicate,
  preference category — not just embeddings
- **Reasoning patterns are first-class** — agents can find similar past
  decisions and reuse them, cutting tokens and latency
- **Full provenance** — every memory entry links to the message that
  created it and the trace it belongs to

## Next Steps

- **Real example**: see `agent/shopagent_adk.py` in this repo for the
  full ShopAgent integration with all six memory tools
- **Use Vertex AI embeddings**: pass `EmbeddingConfig(provider="vertex_ai")`
  to `MemorySettings` for production-grade semantic search
- **Multi-agent orchestration**: combine `Neo4jMemoryService` with
  ADK's `Runner` to share memory across multiple agents
- **Deploy to Vertex AI**: same code runs on Gemini Enterprise without
  modification

## Library Reference

- Library: https://github.com/neo4j-labs/neo4j-agent-memory
- Docs: https://neo4j.com/labs/agent-memory/
- PyPI: https://pypi.org/project/neo4j-agent-memory/
