# ShopAgent — Neo4j Knowledge Layer for Agentic AI

A side-by-side demo showing what happens when an AI shopping agent has
**no memory** versus one backed by a **Neo4j context graph** with a
complete agent memory system.

> Same model. Same question. Completely different experience.

Built for the Neo4j AI Launch.

![Three memory types: short-term, long-term, reasoning](https://img.shields.io/badge/memory-short--term%20%7C%20long--term%20%7C%20reasoning-00BCD4)
![Frameworks](https://img.shields.io/badge/frameworks-Claude%20%7C%20Google%20ADK-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What This Demonstrates

Three types of agent memory, all stored in a connected Neo4j graph:

| Memory Type | What It Stores | What It Enables |
|---|---|---|
| **Long-term** | Customer profile, purchases, preferences | Personalization that persists across sessions |
| **Short-term** | Current conversation messages | Follow-ups don't restart from zero |
| **Reasoning** | Decision traces, reusable patterns | Agents that learn from past decisions |

Plus a full **decision audit trail** — every tool call, every Cypher
query, every reasoning step is persisted as a queryable graph.

## Architecture

```
┌──────────────────────────────────┐
│  Next.js frontend (Vercel)       │
│  Side-by-side chat panels         │
│  Graph viz · Decision Trace       │
└──────────────┬───────────────────┘
               │ SSE streaming
               ▼
┌──────────────────────────────────┐
│  FastAPI backend (Vercel/Railway) │
│  ┌─────────────────────────────┐ │
│  │  Claude Sonnet 4 (live)     │ │
│  │  + 6 memory tools           │ │   Path A — production demo
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │  Google ADK + Gemini 2.5    │ │
│  │  + neo4j-agent-memory       │ │   Path B — launch package
│  └─────────────────────────────┘ │
└──────────────┬───────────────────┘
               │ bolt+s://
               ▼
┌──────────────────────────────────┐
│  Neo4j Aura                      │
│  Domain graph + agent memory      │
└──────────────────────────────────┘
```

## Repository Layout

```
shopagent/
├── backend/                       # FastAPI + Claude + Google ADK
│   ├── main.py                    # SSE chat endpoint (Claude path)
│   ├── agent/
│   │   ├── shopagent.py           # Live demo agent (Claude + raw Cypher)
│   │   ├── shopagent_adk.py       # Google ADK + neo4j-agent-memory
│   │   ├── seed_agent_memory.py   # Seeds the agent-memory library schema
│   │   └── prompts.py
│   ├── graph/
│   │   ├── seed.py                # Domain graph seed (8 users, 20 shoes, 72 reviews)
│   │   └── neo4j_client.py
│   ├── GOOGLE_ADK_QUICKSTART.md   # Walkthrough for the ADK integration
│   └── requirements.txt
│
├── frontend/                      # Next.js 14 + Tailwind + D3
│   ├── app/
│   │   ├── demo/page.tsx          # Main side-by-side demo page
│   │   └── api/                   # Proxy routes to backend
│   ├── components/
│   │   ├── AgentPanel.tsx         # Chat panel with memory chips
│   │   ├── MetricsBar.tsx
│   │   ├── GraphViewer.tsx        # D3 force-directed graph
│   │   ├── DecisionTracePanel.tsx
│   │   └── WhyGraphPanel.tsx
│   └── lib/
│
└── README.md                      # You are here
```

## Quick Start

### 1. Set up Neo4j Aura (free tier)

Create an instance at <https://console.neo4j.io>. Note the URI, username, and password.

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
# ANTHROPIC_API_KEY (for Claude path)
# GOOGLE_API_KEY (for ADK path, optional)

# Seed the domain graph (users, shoes, reviews, conversations)
python -c "from dotenv import load_dotenv; load_dotenv(); from graph.seed import run_seed; import os; run_seed(os.environ['NEO4J_URI'], os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD'])"

# Optional: seed the agent-memory library schema for the ADK demo
python -m agent.seed_agent_memory

# Start the API
python main.py
```

### 3. Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# Set NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

npm run dev
```

Open <http://localhost:3000/demo>

## The Two Code Paths

This repo demonstrates the same value proposition with **two integration patterns**:

### Path A — Claude + raw Cypher tools (`agent/shopagent.py`)

The lower-level pattern. The agent connects to Neo4j and writes Cypher
queries directly via tool calls. Maximum flexibility, minimum dependencies.
Used in the live deployed demo.

### Path B — Google ADK + neo4j-agent-memory (`agent/shopagent_adk.py`)

The launch-aligned pattern. Uses the official `neo4j-agent-memory` library
which provides high-level memory primitives (`client.long_term`,
`client.short_term`, `client.reasoning`) on top of Neo4j. The agent uses
these via Google ADK FunctionTools with Gemini.

```bash
pip install neo4j-agent-memory[google-adk]
```

See [`backend/GOOGLE_ADK_QUICKSTART.md`](backend/GOOGLE_ADK_QUICKSTART.md)
for the full walkthrough.

## Demo Scenarios

The demo walks through three scenarios that match the agent memory MPF:

| # | Scenario | Memory Type Demonstrated |
|---|---|---|
| 1 | "I need new running shoes" | Long-term recall vs cold start |
| 2 | "Tell me about heel fit on the Kinvara" | Short-term + cross-reference with long-term |
| 3 | "I went with the Kinvara last time, want more cushion" | Reasoning memory reuse |
| 4 | "I just bought the 1080v13N" | Long-term write-back + audit trail |

See the included demo script for the full talk track and Cypher queries.

## Live Demo

- **Frontend:** <https://frontend-liart-nine-87.vercel.app/demo>
- **Backend:** <https://backend-three-mu-35.vercel.app>

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, D3 |
| Backend | Python, FastAPI, Anthropic SDK, Google ADK |
| Memory | [`neo4j-agent-memory`](https://github.com/neo4j-labs/neo4j-agent-memory) |
| Database | Neo4j Aura |
| Deploy | Vercel (frontend + backend) |

## License

MIT

## The Key Line

> "Same model on both sides. The difference is the data layer.
> That's the Neo4j knowledge layer."
