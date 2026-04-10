"""
ShopAgent — LangChain-style agent with Claude + Neo4j.

Three memory types powered by the Neo4j knowledge layer:
  1. Long-term memory  — user profile, purchases, preferences (cross-session)
  2. Short-term memory — current conversation context (in-session)
  3. Reasoning memory  — decision traces, reusable decision patterns
"""

import json
import os
from typing import Any

from anthropic import Anthropic
from neo4j import GraphDatabase

from .prompts import WITH_CONTEXT_PROMPT, WITHOUT_CONTEXT_PROMPT

# ---------------------------------------------------------------------------
# Neo4j connection
# ---------------------------------------------------------------------------

_neo4j_driver = None


def _get_driver():
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
    return _neo4j_driver


def execute_cypher(query: str, params: dict[str, Any] | None = None) -> str:
    """Execute a Cypher query against Neo4j and return results as JSON."""
    driver = _get_driver()
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            records = []
            for record in result:
                row = {}
                for key in record.keys():
                    val = record[key]
                    if hasattr(val, "__iter__") and not isinstance(val, (str, dict)):
                        val = list(val)
                    row[key] = val
                records.append(row)
            return json.dumps(records, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)[:300], "hint": "Check Cypher syntax. Use widthOptions CONTAINS 'narrow' instead of width. Use existing property names from schema."})


def get_neo4j_schema() -> str:
    """Return the database schema."""
    driver = _get_driver()
    with driver.session() as session:
        labels = session.run("CALL db.labels()").data()
        rels = session.run("CALL db.relationshipTypes()").data()
        return json.dumps({
            "nodeLabels": [r["label"] for r in labels],
            "relationshipTypes": [r["relationshipType"] for r in rels],
        }, indent=2)


# ---------------------------------------------------------------------------
# Tool definitions — explicitly labeled by memory type
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "recall_long_term_memory",
        "description": (
            "LONG-TERM MEMORY: Load the user's persistent profile from Neo4j — "
            "foot width, size, purchase history, rejections, fit notes, style "
            "preferences, and similar users. This data persists across sessions "
            "and grows over time. Run this FIRST on every request."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID (e.g. 'alex')",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "recall_reasoning_memory",
        "description": (
            "REASONING MEMORY: Search past decision traces and recommendations. "
            "Find successful decision patterns the agent used before — reuse them "
            "to avoid redundant traversals, reduce tool calls, and cut latency. "
            "This is how agents learn over time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "execute_cypher",
        "description": (
            "Execute a Cypher query against the Neo4j graph database. "
            "Use for context graph traversals, review insight lookups, "
            "cross-user similarity queries, and writing data back to memory. "
            "Returns query results as JSON."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The Cypher query to execute",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "update_long_term_memory",
        "description": (
            "LONG-TERM MEMORY WRITE: Update the user's persistent profile — "
            "record a new purchase, rejection, preference change, or fit note. "
            "This data will be available in all future sessions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID",
                },
                "update_type": {
                    "type": "string",
                    "enum": ["purchase", "rejection", "preference", "fit_note"],
                    "description": "Type of update",
                },
                "shoe_id": {
                    "type": "string",
                    "description": "Shoe ID if applicable",
                },
                "data": {
                    "type": "object",
                    "description": "Additional data — rating, notes, reason, etc.",
                },
            },
            "required": ["user_id", "update_type"],
        },
    },
    {
        "name": "write_decision_trace",
        "description": (
            "REASONING MEMORY WRITE: Persist a decision trace to the graph. "
            "Records tool invocation, parameters, reasoning, and results so "
            "future sessions can find and reuse this decision pattern."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cypher_query": {
                    "type": "string",
                    "description": "The Cypher query that was executed",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why this query was run",
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["long-term", "short-term", "reasoning"],
                    "description": "Which memory type this trace belongs to",
                },
                "result_summary": {
                    "type": "string",
                    "description": "Brief summary of what was found",
                },
            },
            "required": ["reasoning", "memory_type"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def _execute_tool(tool_name: str, tool_input: dict) -> tuple[str, dict]:
    """Execute a tool and return (result_string, log_entry)."""

    if tool_name == "recall_long_term_memory":
        uid = tool_input.get("user_id", "alex")
        query = """
        MATCH (u:User {id: $uid})
        OPTIONAL MATCH (u)-[p:PURCHASED]->(bought:Shoe)
        OPTIONAL MATCH (u)-[rej:REJECTED]->(r:Shoe)
        OPTIONAL MATCH (u)-[v:VIEWED]->(viewed:Shoe)
        RETURN u {.id, .name, .footWidth, .primarySize, .fitNotes, .stylePrefs, .priceRange},
               collect(DISTINCT CASE WHEN bought IS NOT NULL THEN
                 {shoe: bought.brand+' '+bought.model, shoeId: bought.id, rating: p.rating, notes: p.notes}
               END) AS purchases,
               collect(DISTINCT CASE WHEN r IS NOT NULL THEN
                 {shoe: r.brand+' '+r.model, reason: rej.reason}
               END) AS rejections,
               collect(DISTINCT CASE WHEN viewed IS NOT NULL THEN
                 {shoe: viewed.brand+' '+viewed.model, views: v.count}
               END) AS viewed
        """
        result = execute_cypher(query, {"uid": uid})
        return result, {"name": "recall_long_term_memory", "query": query, "result": result, "memoryType": "long-term"}

    elif tool_name == "recall_reasoning_memory":
        uid = tool_input.get("user_id", "alex")
        query = """
        MATCH (u:User {id: $uid})-[:HAD_CONVERSATION]->(c:Conversation)
        WHERE c.hasContextGraph = true
        OPTIONAL MATCH (c)-[:PRODUCED]->(rec:Recommendation)-[:RECOMMENDS]->(s:Shoe)
        OPTIONAL MATCH (dt:DecisionTrace)-[:PART_OF]->(c)
        WHERE dt.memoryType IS NOT NULL
        RETURN c.id AS session, c.startTime AS date, c.resolved,
               c.timeToDecisionSeconds AS decisionTime,
               collect(DISTINCT CASE WHEN s IS NOT NULL THEN
                 {shoe: s.brand+' '+s.model, confidence: rec.confidence,
                  accepted: rec.accepted, reasoning: rec.reasoning}
               END) AS pastRecs,
               collect(DISTINCT CASE WHEN dt IS NOT NULL THEN
                 {traceId: dt.id, memoryType: dt.memoryType,
                  reasoning: dt.reasoning, result: dt.result}
               END) AS traces
        ORDER BY c.startTime DESC LIMIT 5
        """
        result = execute_cypher(query, {"uid": uid})
        return result, {"name": "recall_reasoning_memory", "query": query, "result": result, "memoryType": "reasoning"}

    elif tool_name == "execute_cypher":
        query = tool_input.get("query", "")
        result = execute_cypher(query)
        return result, {"name": "execute_cypher", "query": query, "result": result, "memoryType": "context-graph"}

    elif tool_name == "update_long_term_memory":
        uid = tool_input.get("user_id", "alex")
        update_type = tool_input.get("update_type", "")
        shoe_id = tool_input.get("shoe_id", "")
        data = tool_input.get("data", {})

        if update_type == "purchase":
            query = f"""
            MATCH (u:User {{id: $uid}}), (s:Shoe {{id: $shoeId}})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date(), r.rating = $rating, r.notes = $notes
            RETURN 'Purchase recorded' AS status
            """
            result = execute_cypher(query, {
                "uid": uid, "shoeId": shoe_id,
                "rating": data.get("rating", 0),
                "notes": data.get("notes", ""),
            })
        elif update_type == "rejection":
            query = f"""
            MATCH (u:User {{id: $uid}}), (s:Shoe {{id: $shoeId}})
            MERGE (u)-[r:REJECTED]->(s)
            SET r.reason = $reason, r.date = date()
            RETURN 'Rejection recorded' AS status
            """
            result = execute_cypher(query, {
                "uid": uid, "shoeId": shoe_id,
                "reason": data.get("reason", ""),
            })
        elif update_type == "preference":
            updates = []
            if "fitNotes" in data:
                updates.append(f"u.fitNotes = '{data['fitNotes']}'")
            if "stylePrefs" in data:
                updates.append(f"u.stylePrefs = {data['stylePrefs']}")
            if "priceRange" in data:
                updates.append(f"u.priceRange = '{data['priceRange']}'")
            set_clause = ", ".join(updates) if updates else "u.totalSessions = u.totalSessions + 1"
            query = f"MATCH (u:User {{id: $uid}}) SET {set_clause} RETURN 'Profile updated' AS status"
            result = execute_cypher(query, {"uid": uid})
        else:
            result = json.dumps({"status": "Unknown update type"})
            query = ""

        return result, {"name": "update_long_term_memory", "query": query, "result": result, "memoryType": "long-term"}

    elif tool_name == "write_decision_trace":
        cypher_q = tool_input.get("cypher_query", "")
        reasoning = tool_input.get("reasoning", "")
        mem_type = tool_input.get("memory_type", "reasoning")
        result_summary = tool_input.get("result_summary", "")

        query = """
        CREATE (dt:DecisionTrace {
          id: randomUUID(),
          toolName: 'execute_cypher',
          cypherQuery: $cypher,
          reasoning: $reasoning,
          memoryType: $memType,
          result: $resultSummary,
          timestamp: datetime(),
          durationMs: 0
        })
        RETURN 'Decision trace persisted' AS status, dt.id AS traceId
        """
        result = execute_cypher(query, {
            "cypher": cypher_q,
            "reasoning": reasoning,
            "memType": mem_type,
            "resultSummary": result_summary,
        })
        return result, {"name": "write_decision_trace", "query": query, "result": result, "memoryType": "reasoning"}

    elif tool_name == "get_schema":
        result = get_neo4j_schema()
        return result, {"name": "get_schema", "query": "CALL db.schema", "result": result, "memoryType": "schema"}

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"}), {"name": tool_name, "query": "", "result": "error"}


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------

def run_agent(
    message: str,
    use_context_graph: bool,
    conversation_history: list[dict],
) -> dict:
    """
    Run the agent. Returns:
        {
            "reply": str,
            "tool_calls": [{"name": str, "query": str, "result": str, "memoryType": str}, ...],
        }
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system_prompt = WITH_CONTEXT_PROMPT if use_context_graph else WITHOUT_CONTEXT_PROMPT
    tools = TOOLS if use_context_graph else []

    messages = []
    for h in conversation_history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    tool_calls_log = []
    max_iterations = 10

    for _ in range(max_iterations):
        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        response = client.messages.create(**kwargs)

        if response.stop_reason == "tool_use":
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result_str, log_entry = _execute_tool(block.name, block.input)
                    tool_calls_log.append(log_entry)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            reply = ""
            for block in response.content:
                if hasattr(block, "text"):
                    reply += block.text
            return {"reply": reply, "tool_calls": tool_calls_log}

    return {"reply": "I ran into an issue processing your request.", "tool_calls": tool_calls_log}
