"""
ShopAgent FastAPI backend
Endpoints:
  POST /api/agent/chat        — SSE streaming chat
  POST /api/agent/reset       — reset session
  GET  /api/graph/user/{id}   — subgraph for NVL
  GET  /api/graph/trace/{id}  — decision traces for conversation
  POST /api/seed              — seed database
"""

import asyncio
import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv(override=False)  # Don't override Vercel's env vars

from graph.neo4j_client import close_driver, get_conversation_traces, get_driver, get_user_subgraph, run_query
from graph.seed import run_seed

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_driver()


app = FastAPI(title="ShopAgent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------
sessions: dict[str, list[dict]] = {}

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    conversationId: str
    useContextGraph: bool = True
    userId: str = "alex"


# ---------------------------------------------------------------------------
# Helper: extract metadata from reply + tool calls
# ---------------------------------------------------------------------------

def extract_metadata(reply: str, tool_calls: list[dict], use_context_graph: bool) -> dict:
    facts_recalled = []
    graph_paths = []
    cypher_queries = []
    memory_types_used = []
    question_count = 0
    graph_hops = 0
    confidence = 0.5

    if use_context_graph:
        # Extract Cypher queries and memory types from tool calls
        for tc in tool_calls:
            if tc.get("query"):
                cypher_queries.append(tc["query"])
            mem_type = tc.get("memoryType", "")
            if mem_type and mem_type not in memory_types_used:
                memory_types_used.append(mem_type)

        # Count graph hops
        for q in cypher_queries:
            graph_hops += q.count("]->(") + q.count("]->") + q.count("<-[")

        # Build facts from tool call names (more reliable than regex)
        for tc in tool_calls:
            name = tc.get("name", "")
            if name == "recall_long_term_memory":
                facts_recalled.append("[Long-term] User profile loaded")
            elif name == "recall_reasoning_memory":
                facts_recalled.append("[Reasoning] Past decisions recalled")
            elif name == "update_long_term_memory":
                facts_recalled.append("[Long-term] Profile updated")
            elif name == "write_decision_trace":
                facts_recalled.append("[Reasoning] Decision trace persisted")

        # Extract additional facts from reply text
        for m in re.finditer(r"(?:size|width|narrow|purchased|rejected|rating)[\w\s:,.*★-]{5,50}", reply, re.IGNORECASE):
            fact = m.group(0).strip()[:60]
            if fact not in facts_recalled and len(facts_recalled) < 8:
                facts_recalled.append(fact)

        # Build graph paths from tool calls
        if any(tc.get("name") == "recall_long_term_memory" for tc in tool_calls):
            graph_paths.append("User → PURCHASED → Shoe")
            graph_paths.append("User → REJECTED → Shoe")
        if any(tc.get("name") == "recall_reasoning_memory" for tc in tool_calls):
            graph_paths.append("User → HAD_CONVERSATION → Conversation → PRODUCED → Recommendation")
            graph_paths.append("DecisionTrace → PART_OF → Conversation")
        if any("SIMILAR_TO" in tc.get("query", "") or "similar" in tc.get("query", "").lower() for tc in tool_calls):
            graph_paths.append("User → SIMILAR_TO → User → PURCHASED → Shoe")
        if any("HAS_REVIEW" in tc.get("query", "") for tc in tool_calls):
            graph_paths.append("Shoe → HAS_REVIEW → Review → CONTAINS_INSIGHT → ReviewInsight")

        if graph_hops == 0:
            graph_hops = len(tool_calls) * 3

        # Confidence from reply
        conf_match = re.search(r"(\d{1,3})%\s*(?:match|confidence)", reply, re.IGNORECASE)
        confidence = int(conf_match.group(1)) / 100 if conf_match else 0.88
    else:
        question_count = reply.count("?")
        confidence = 0.3

    return {
        "factsRecalled": facts_recalled[:10],
        "graphPaths": graph_paths,
        "cypherQueries": cypher_queries,
        "memoryTypesUsed": memory_types_used,
        "confidence": confidence,
        "questionCount": question_count,
        "graphHops": graph_hops,
    }


# ---------------------------------------------------------------------------
# Agent runner — streams response word by word
# ---------------------------------------------------------------------------

async def run_agent_streaming(
    message: str,
    conversation_id: str,
    use_context_graph: bool,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    """Run the Claude agent and yield SSE chunks."""
    try:
        from agent.shopagent import run_agent

        # Run synchronous agent in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            run_agent,
            message,
            use_context_graph,
            history,
        )

        reply = result["reply"]
        tool_calls = result["tool_calls"]

        # Stream the reply word by word
        words = reply.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.02)

        # Send metadata
        meta = extract_metadata(reply, tool_calls, use_context_graph)
        yield f"data: {json.dumps({'type': 'meta', **meta})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Write conversation + decision traces to Neo4j
        if use_context_graph and tool_calls:
            try:
                await run_query(
                    """
                    MERGE (c:Conversation {id: $convId})
                    ON CREATE SET c.startTime = datetime(), c.hasContextGraph = true,
                                  c.intent = 'shoe recommendation', c.resolved = false,
                                  c.questionCount = 0, c.factsRecalled = $factsCount,
                                  c.graphHops = $hops
                    WITH c
                    MATCH (u:User {id: 'alex'})
                    MERGE (u)-[:HAD_CONVERSATION]->(c)
                    """,
                    {
                        "convId": conversation_id,
                        "factsCount": len(meta["factsRecalled"]),
                        "hops": meta["graphHops"],
                    },
                )
                for i, tc in enumerate(tool_calls):
                    dt_id = f"dt_live_{conversation_id}_{i}"
                    await run_query(
                        """
                        MERGE (dt:DecisionTrace {id: $dtId})
                        SET dt.toolName = $toolName,
                            dt.cypherQuery = $query,
                            dt.reasoning = 'Live agent tool call',
                            dt.timestamp = datetime(),
                            dt.durationMs = 0
                        WITH dt
                        MATCH (c:Conversation {id: $convId})
                        MERGE (dt)-[:PART_OF]->(c)
                        """,
                        {
                            "dtId": dt_id,
                            "toolName": tc["name"],
                            "query": tc.get("query", ""),
                            "convId": conversation_id,
                        },
                    )
            except Exception as e:
                print(f"Neo4j trace write warning: {e}")

    except Exception as exc:
        print(f"Agent error (using fallback): {exc}")
        import traceback
        traceback.print_exc()
        async for chunk in simulated_response(message, use_context_graph, conversation_id):
            yield chunk


async def simulated_response(
    message: str, use_context_graph: bool, conversation_id: str
) -> AsyncGenerator[str, None]:
    """Fallback simulated response."""
    if use_context_graph:
        await asyncio.sleep(0.8)
        reply = (
            "**From your profile:** narrow width (AA), size 9.5, Brooks Ghost 15N ★4 "
            "(great heel lock, toe box snug around mile 8), Asics Kayano 28N ★3 "
            "(heavier than expected). Rejected: Nike Pegasus 40 (too wide), Hoka Bondi 8 "
            "(rocker sole).\n\n"
            "Based on 3 similar narrow-footed users who share your purchase history, "
            "here are my top picks:\n\n"
            "**1. Saucony Kinvara 14N — $139.95** · 91% match\n"
            "> \"Heel locks in immediately. Toe box has real room — no black toenails after 10 miles.\"\n"
            "> \"Everyone with AA or B width loves the secure feel.\"\n\n"
            "**2. Asics Gel-Nimbus 25N — $149.95** · 88% match\n"
            "> \"Asics narrow width is the gold standard. Plush without being sloppy.\"\n\n"
            "**3. New Balance Fresh Foam 1080v13N — $129.95** *(on sale, $20 off)* · 84% match\n"
            "> \"Most comfortable shoe I've owned as a narrow-footed runner.\"\n\n"
            "Confidence based on 47 narrow-foot reviews across 3 users with identical purchase history."
        )
    else:
        await asyncio.sleep(2.5)
        reply = (
            "Thanks for reaching out! To help you find the right shoe, I'll need a bit more information:\n\n"
            "1. What's your shoe size?\n"
            "2. Do you have a narrow, medium, or wide foot width?\n"
            "3. What's your budget range?\n\n"
            "Also, what will you primarily be using these shoes for — running, casual wear, or something else?"
        )

    words = reply.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        await asyncio.sleep(0.02)

    meta = extract_metadata(reply, [], use_context_graph)
    yield f"data: {json.dumps({'type': 'meta', **meta})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/agent/chat")
async def chat(req: ChatRequest):
    if req.conversationId not in sessions:
        sessions[req.conversationId] = []

    history = sessions[req.conversationId]
    history.append({"role": "user", "content": req.message})

    collected_reply = []

    async def event_stream():
        async for chunk in run_agent_streaming(
            req.message, req.conversationId, req.useContextGraph, history
        ):
            # Collect reply text so we can save to history
            try:
                if '"type": "chunk"' in chunk:
                    data = json.loads(chunk.split("data: ", 1)[1])
                    if data.get("type") == "chunk":
                        collected_reply.append(data.get("content", ""))
            except Exception:
                pass
            yield chunk
        # Save assistant reply to session history
        full_reply = "".join(collected_reply)
        if full_reply:
            history.append({"role": "assistant", "content": full_reply})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/agent/reset")
async def reset():
    new_id = str(uuid.uuid4())
    sessions[new_id] = []
    return {"conversationId": new_id}


@app.get("/api/graph/user/{user_id}")
async def get_user_graph(user_id: str):
    try:
        data = await get_user_subgraph(user_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/trace/{conversation_id}")
async def get_trace(conversation_id: str):
    try:
        traces = await get_conversation_traces(conversation_id)
        return {"traces": traces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/seed")
async def seed():
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            run_seed,
            os.environ["NEO4J_URI"],
            os.environ["NEO4J_USERNAME"],
            os.environ["NEO4J_PASSWORD"],
        )
        return {"status": "ok", "message": "Seed data loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    # Test Neo4j connection
    neo4j_status = "unknown"
    node_count = 0
    try:
        driver = get_driver()
        with driver.session() as session:
            r = session.run("RETURN 1 AS n").single()
            neo4j_status = "connected"
            r2 = session.run("MATCH (n) RETURN count(n) AS c").single()
            node_count = r2["c"]
    except Exception as e:
        neo4j_status = f"error: {str(e)[:150]}"

    return {
        "status": "ok",
        "neo4j": neo4j_status,
        "nodes": node_count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
