"""
ShopAgent — Google ADK + Gemini + Neo4j Agent Memory

Built on the official `neo4j-agent-memory` library (Neo4j Labs).
This is the launch-aligned integration pattern showcased in the
Neo4j Agent Memory v0.0.4 release.

INSTALL:
    pip install neo4j-agent-memory[google-adk]

ENVIRONMENT VARIABLES:
    GOOGLE_API_KEY    — Gemini API key (with billing enabled)
    NEO4J_URI         — neo4j+s://xxxx.databases.neo4j.io
    NEO4J_USERNAME    — neo4j
    NEO4J_PASSWORD    — your password

WHAT THIS DEMONSTRATES:
    The neo4j-agent-memory library gives you a complete agent memory
    API on top of Neo4j — short-term, long-term, and reasoning memory
    — with a few lines of code. The agent uses these memory primitives
    via ADK FunctionTools, and every reasoning step is automatically
    persisted as a queryable graph for full audit trail and decision
    provenance.

THE THREE MEMORY TYPES:
    1. SHORT-TERM  — current session messages, conversation chains
       client.short_term.add_message(), get_conversation()
    2. LONG-TERM   — entities, facts, preferences across sessions
       client.long_term.add_entity(), add_preference(), search_entities()
    3. REASONING   — decision traces, tool calls, reusable patterns
       client.reasoning.start_trace(), add_step(), get_similar_traces()

The agent can also call client.get_context(query) to pull relevant
context from ALL three memory types in a single call.
"""

import logging
import os
import warnings
from contextlib import asynccontextmanager
from typing import Any

# Quiet noisy library warnings during the demo
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
logging.getLogger("neo4j_agent_memory.extraction").setLevel(logging.ERROR)
logging.getLogger("neo4j").setLevel(logging.WARNING)

# Google ADK
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.function_tool import FunctionTool
from google.genai import types as genai_types

# Neo4j Agent Memory (the launch package)
from neo4j_agent_memory import (
    MemoryClient,
    MemorySettings,
    Neo4jConfig,
    EmbeddingConfig,
    EmbeddingProvider,
)

from .prompts import WITH_CONTEXT_PROMPT, WITHOUT_CONTEXT_PROMPT

# ---------------------------------------------------------------------------
# Initialize the Neo4j Agent Memory client
# ---------------------------------------------------------------------------

def build_memory_settings() -> MemorySettings:
    """Configure the neo4j-agent-memory client for Neo4j Aura + Vertex AI."""
    return MemorySettings(
        neo4j=Neo4jConfig(
            uri=os.environ["NEO4J_URI"],
            username=os.environ["NEO4J_USERNAME"],
            password=os.environ["NEO4J_PASSWORD"],
        ),
        # The library supports VertexAIEmbedder for production. For the
        # demo we use sentence-transformers (local, no API key) so we
        # don't need GCP project setup or an OpenAI key just for embeddings.
        embedding=EmbeddingConfig(
            provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
            model="all-MiniLM-L6-v2",
            dimensions=384,
        ),
    )


# A module-level client we connect lazily so tools can share it.
_memory_client: MemoryClient | None = None


async def get_memory_client() -> MemoryClient:
    """Get a connected MemoryClient (lazy singleton)."""
    global _memory_client
    if _memory_client is None or not _memory_client.is_connected:
        _memory_client = MemoryClient(settings=build_memory_settings())
        await _memory_client.connect()
    return _memory_client


# ---------------------------------------------------------------------------
# ADK Tools — wrappers around neo4j-agent-memory primitives
#
# Each tool is a thin wrapper that ADK turns into a FunctionTool. The
# real work is done by the neo4j-agent-memory library — short-term,
# long-term, and reasoning memory operations against the graph.
# ---------------------------------------------------------------------------

async def recall_user_context(user_id: str, query: str = "") -> dict:
    """
    LONG-TERM MEMORY — Pull the user's persistent profile, preferences,
    and entity facts from Neo4j. Uses neo4j-agent-memory's long-term
    memory module which handles entity resolution and deduplication
    automatically.

    Args:
        user_id: The user's identifier (becomes the session prefix)
        query: Optional natural-language query to filter context

    Returns:
        A dict with entities, preferences, and facts about the user
    """
    client = await get_memory_client()

    # Search for entities related to the user
    entities = await client.long_term.search_entities(
        query=user_id if not query else query,
        limit=10,
    )

    # Get all preferences (foot width, style, budget, etc.)
    preferences = await client.long_term.search_preferences(
        query=query or "shopping preferences",
        limit=10,
    )

    # Get facts about the user (e.g. "Alex purchased Brooks Ghost 15")
    facts = await client.long_term.search_facts(
        query=query or f"facts about {user_id}",
        limit=10,
    )

    return {
        "entities": [{"name": e.name, "type": str(e.entity_type), "attrs": e.attributes} for e in entities],
        "preferences": [{"category": p.category, "preference": p.preference, "confidence": p.confidence} for p in preferences],
        "facts": [{"subject": f.subject, "predicate": f.predicate, "object": f.object} for f in facts],
    }


async def recall_reasoning_patterns(task: str, limit: int = 3) -> dict:
    """
    REASONING MEMORY — Find similar past decision traces. The agent
    uses this to reuse successful reasoning patterns instead of
    re-running expensive multi-step traversals from scratch.

    This is the core of "agents that learn over time" — driven by
    neo4j-agent-memory's similarity search over reasoning traces.

    Args:
        task: Natural-language description of the current task
        limit: Maximum number of similar traces to return

    Returns:
        Past reasoning traces with their outcomes
    """
    client = await get_memory_client()

    similar = await client.reasoning.get_similar_traces(
        task=task,
        limit=limit,
        success_only=True,
        threshold=0.6,
    )

    return {
        "similar_traces": [
            {
                "trace_id": str(t.id),
                "task": t.task,
                "outcome": t.outcome,
                "session": t.session_id,
                "completed_at": str(t.completed_at) if t.completed_at else None,
            }
            for t in similar
        ],
    }


async def get_session_history(session_id: str, limit: int = 20) -> dict:
    """
    SHORT-TERM MEMORY — Retrieve the current session's message chain.
    The agent uses this to maintain conversation context without
    re-asking what the user just told it.

    Args:
        session_id: The current session identifier
        limit: Maximum messages to return

    Returns:
        Conversation messages in chronological order
    """
    client = await get_memory_client()
    conversation = await client.short_term.get_conversation(
        session_id=session_id,
        limit=limit,
    )
    return {
        "messages": [
            {"role": str(m.role), "content": m.content, "timestamp": str(m.created_at)}
            for m in conversation.messages
        ],
    }


async def get_unified_context(query: str, session_id: str = "default") -> dict:
    """
    UNIFIED CONTEXT — Pull relevant context from ALL THREE memory types
    in a single call. This is the easiest way for an agent to get
    grounded — neo4j-agent-memory handles the orchestration.

    Args:
        query: What the agent is trying to figure out
        session_id: Current session identifier

    Returns:
        Combined context string ready to inject into the prompt
    """
    client = await get_memory_client()
    context = await client.get_context(
        query=query,
        session_id=session_id,
        include_short_term=True,
        include_long_term=True,
        include_reasoning=True,
        max_items=10,
    )
    return {"context": context}


async def remember_preference(
    user_id: str,
    category: str,
    preference: str,
    confidence: float = 1.0,
) -> dict:
    """
    LONG-TERM MEMORY WRITE — Persist a new preference about the user
    (e.g. "prefers narrow width", "rejected rocker soles"). This is
    automatically embedded for semantic search and stored as a
    Preference node in the graph.

    Args:
        user_id: The user's identifier
        category: Preference category (e.g. "fit", "brand", "budget")
        preference: The preference itself
        confidence: 0.0–1.0 confidence score

    Returns:
        The created preference
    """
    client = await get_memory_client()
    pref = await client.long_term.add_preference(
        category=category,
        preference=preference,
        context=user_id,
        confidence=confidence,
    )
    return {
        "id": str(pref.id),
        "category": pref.category,
        "preference": pref.preference,
        "status": "stored in long-term memory",
    }


async def remember_fact(subject: str, predicate: str, obj: str) -> dict:
    """
    LONG-TERM MEMORY WRITE — Record a fact about the user
    (e.g. "Alex purchased Brooks Ghost 15", "Alex returned Nike Pegasus 40").
    Stored as a Fact node with automatic embedding for semantic recall.

    Args:
        subject: The subject of the fact (usually the user)
        predicate: The relationship (e.g. "purchased", "rejected")
        obj: The object of the fact

    Returns:
        The created fact
    """
    client = await get_memory_client()
    fact = await client.long_term.add_fact(
        subject=subject,
        predicate=predicate,
        obj=obj,
    )
    return {
        "id": str(fact.id),
        "subject": fact.subject,
        "predicate": fact.predicate,
        "object": fact.object_value,
        "status": "stored in long-term memory",
    }


# ---------------------------------------------------------------------------
# Build the ADK agent
# ---------------------------------------------------------------------------

def create_adk_agent(use_context_graph: bool) -> Agent:
    """
    Create a Google ADK Agent powered by Gemini.

    With use_context_graph=True, the agent has 6 memory tools wired
    to neo4j-agent-memory:

      Long-term memory:
        - recall_user_context        — load profile, prefs, facts
        - remember_preference        — write a new preference
        - remember_fact              — record a new fact

      Short-term memory:
        - get_session_history        — current conversation context

      Reasoning memory:
        - recall_reasoning_patterns  — find reusable past decisions

      Unified:
        - get_unified_context        — pull from all three memory types

    With use_context_graph=False, the agent has no tools — pure
    Gemini with no memory.
    """
    if use_context_graph:
        return Agent(
            model="gemini-2.5-flash",
            name="ShopAgent",
            instruction=WITH_CONTEXT_PROMPT,
            tools=[
                FunctionTool(func=recall_user_context),
                FunctionTool(func=recall_reasoning_patterns),
                FunctionTool(func=get_session_history),
                FunctionTool(func=get_unified_context),
                FunctionTool(func=remember_preference),
                FunctionTool(func=remember_fact),
            ],
        )
    else:
        return Agent(
            model="gemini-2.5-flash",
            name="StandardAgent",
            instruction=WITHOUT_CONTEXT_PROMPT,
            tools=[],
        )


# ---------------------------------------------------------------------------
# Run the agent
# ---------------------------------------------------------------------------

async def run_adk_agent(
    message: str,
    use_context_graph: bool,
    conversation_id: str = "demo-session",
    user_id: str = "alex",
) -> dict:
    """
    Run the Gemini agent against a user message.

    Under the hood, neo4j-agent-memory automatically:
      1. Records the inbound message to short-term memory
      2. Tracks every tool call as a ReasoningStep
      3. Embeds new facts/preferences for future semantic recall
      4. Persists the full decision trace as a queryable graph

    Returns the reply text plus the captured tool call audit trail.
    """
    agent = create_adk_agent(use_context_graph)

    # ADK session — separate from neo4j-agent-memory's session concept,
    # but we use the same ID so they line up in the graph.
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="ShopAgent",
        user_id=user_id,
        session_id=conversation_id,
    )

    runner = Runner(
        agent=agent,
        app_name="ShopAgent",
        session_service=session_service,
    )

    # Persist the user message to short-term memory before running.
    if use_context_graph:
        client = await get_memory_client()
        await client.short_term.add_message(
            session_id=conversation_id,
            role="user",
            content=message,
        )

        # Start a reasoning trace for this turn.
        trace = await client.reasoning.start_trace(
            session_id=conversation_id,
            task=message,
        )

    full_reply = ""
    tool_calls: list[dict] = []

    async for event in runner.run_async(
        user_id=user_id,
        session_id=conversation_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)],
        ),
    ):
        # Capture function calls Gemini makes
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append({
                        "name": fc.name,
                        "args": dict(fc.args or {}),
                    })

        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    full_reply += part.text

    # Persist the assistant reply + complete the reasoning trace.
    if use_context_graph and full_reply:
        client = await get_memory_client()
        await client.short_term.add_message(
            session_id=conversation_id,
            role="assistant",
            content=full_reply,
        )
        await client.reasoning.complete_trace(
            trace_id=trace.id,
            outcome=full_reply[:300],
            success=True,
        )

    return {
        "reply": full_reply,
        "tool_calls": tool_calls,
    }


# ---------------------------------------------------------------------------
# Quick smoke test (run this file directly with a real Gemini key)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    async def main():
        result = await run_adk_agent(
            "I need new running shoes",
            use_context_graph=True,
        )
        print("=== TOOL CALLS ===")
        for tc in result["tool_calls"]:
            print(f"  {tc['name']}({list(tc['args'].keys())})")
        print()
        print("=== REPLY ===")
        print(result["reply"])

    asyncio.run(main())
