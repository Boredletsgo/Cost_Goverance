# InfraMind — Agentic Infrastructure Intelligence Platform

> The intelligence layer above your infrastructure. Ask *"Why did costs increase yesterday?"* instead of searching ten dashboards.

InfraMind continuously analyzes cloud resources, costs, operational events, incidents, and
security findings across **multiple environments** and surfaces actionable insights through
**autonomous AI agents**. It is **cloud-agnostic, vendor-neutral, plug-and-play, and runs
fully locally with no paid cloud services** — `docker compose up` is all you need.

---

## Why InfraMind

Most AI infra tools are **reactive**. InfraMind is **proactive**: on a schedule it detects
anomalies, identifies waste, correlates events, forecasts spend, performs root-cause
analysis, and produces executive summaries — without you investigating manually.

---

## Architecture

```
┌────────────┐     ┌──────────────────────────────────────────────┐
│  Frontend  │ ──▶ │  FastAPI backend (/api)                      │
│ React + TS │     │                                              │
│ Tailwind   │     │  ┌─────────────┐   ┌──────────────────────┐  │
│ shadcn/ui  │     │  │ Connectors  │──▶│  Ingestion → Postgres│  │
└────────────┘     │  │ BaseConnector│   └──────────────────────┘  │
                   │  │ azure/aws/  │            │                 │
                   │  │ gcp/k8s/gh  │            ▼                 │
                   │  └─────────────┘   ┌──────────────────────┐   │
                   │                    │ LangGraph multi-agent │  │
                   │  ┌─────────────┐   │ cost·incident·security│  │
                   │  │  ChromaDB   │◀─▶│ optimization·executive│  │
                   │  │  RAG store  │   └──────────────────────┘   │
                   │  └─────────────┘            │                 │
                   │  AI: OpenAI│Gemini│Ollama│mock                │
                   └──────────────────────────────────────────────┘
                          ▲                       │
                   ┌──────┴───────┐        ┌──────▼───────┐
                   │ Redis (queue)│◀──────▶│ Celery worker│  (proactive
                   └──────────────┘        │  + beat      │   analysis +
                                           └──────────────┘   weekly email)
```

### Tech stack
| Layer | Technology |
|------|------------|
| Frontend | React, TypeScript, TailwindCSS, shadcn/ui-style components, Recharts |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2 |
| Database | PostgreSQL (SQLite for dev) |
| AI | OpenAI · Gemini · Ollama · **built-in mock (no key needed)** |
| Agents | LangGraph |
| Vector store | ChromaDB (local, persistent) |
| Background jobs | Celery + Redis |
| Deployment | Docker Compose |

Everything has an **offline-friendly default**: the `mock` LLM provider and a hashing
embedder fallback mean the platform is fully functional with **zero API keys**.

---

## The 5 AI Agents

| Agent | Responsibilities |
|-------|------------------|
| **Cost Intelligence** | Cost anomaly detection (z-score), spend forecasting, waste identification, optimization recommendations |
| **Incident Intelligence** | Incident analysis, root-cause via change correlation, impact assessment |
| **Security Intelligence** | Risk prioritization, vulnerability & misconfiguration analysis |
| **Optimization** | Orphaned/idle resource cleanup, rightsizing, efficiency analysis |
| **Executive Intelligence** | Business summaries, weekly reports, cost & risk roll-ups |

Quantitative logic (anomaly detection, forecasting, correlation) is **deterministic Python**;
the LLM only narrates the facts — so results are reproducible and hallucination-free.

---

## Quick start

```bash
# 1. Copy environment defaults (works out of the box, no keys required)
cp .env.example .env

# 2. Launch everything
docker compose up --build
```

Then open:
- **Frontend dashboard** → http://localhost:5173
- **API docs (Swagger)** → http://localhost:8000/docs

On first boot the backend creates tables, ingests all mock connectors, builds the RAG
index, and runs every agent to populate insights.

---

## Using a real LLM (optional)

Edit `.env`:

```bash
# OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# or Gemini
AI_PROVIDER=gemini
GEMINI_API_KEY=...

# or fully-local Ollama
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1
```

If a provider is unavailable, InfraMind automatically falls back to the mock provider.

---

## Connector framework

Every integration implements one interface (`backend/app/connectors/base.py`):

```python
class BaseConnector:
    async def get_cost_data() -> list[dict]
    async def get_resources() -> list[dict]
    async def get_events() -> list[dict]
    async def get_security_findings() -> list[dict]
    async def execute_action(action, params) -> dict
```

Bundled mock connectors (**azure, aws, gcp, kubernetes, github**) load realistic JSON
datasets from `backend/app/connectors/data/<name>/` — no cloud credentials required.

**Add your own connector** in 3 steps:
1. Subclass `BaseConnector` (or `JsonMockConnector`).
2. Register it in `backend/app/connectors/registry.py`.
3. Add its name to `ENABLED_CONNECTORS` in `.env`.

---

## Key API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Status + active LLM provider |
| GET | `/api/dashboard` | Aggregated KPIs, charts, recent insights |
| POST | `/api/chat` | Ask a question → routed to the best agent (LangGraph) |
| GET | `/api/agents` | List agents |
| POST | `/api/agents/{name}/run` | Run a single agent |
| POST | `/api/agents/sweep` | Run all agents and persist insights |
| GET | `/api/insights` | List/filter insights |
| GET | `/api/connectors` | List connectors + capabilities |
| POST | `/api/connectors/refresh` | Re-ingest connector data + reindex RAG |
| GET | `/api/knowledge/search?q=` | RAG semantic search |
| POST | `/api/reports/generate` | Build & dispatch the executive report |

Example:

```bash
curl -s localhost:8000/api/chat -H 'content-type: application/json' \
  -d '{"message":"Why did costs increase yesterday?"}' | jq
```

---

## Proactive / scheduled intelligence

The Celery worker (with beat) runs autonomously:
- **every 15 min** → refresh connectors, reindex RAG, run all agents, persist insights
- **weekly (Mon 08:00 UTC)** → generate and email the executive report

Email uses SMTP if configured in `.env`, otherwise logs to the worker console.

---

## Local development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli init-db
python -m app.cli seed
uvicorn app.main:app --reload
# Worker (separate shell): celery -A app.worker.celery_app worker --beat -l info

# Frontend
cd frontend
npm install
npm run dev
```

For local dev without Postgres/Redis, set in `.env`:
`DATABASE_URL=sqlite:///./.data/inframind.db` (Celery still needs Redis).

---

## Success criteria ✅

`docker compose up` delivers:
- AI-powered cost **anomaly detection**
- **Root-cause analysis** via event correlation
- **Multi-agent reasoning** (LangGraph)
- Infrastructure **recommendations** with $ impact
- **Email-based reporting**
- Interactive **dashboard**
- **RAG-powered** infrastructure knowledge search

…with **no paid cloud resources** required.

---

## Project layout

```
.
├── docker-compose.yml
├── .env.example
├── backend/
│   └── app/
│       ├── main.py  cli.py  config.py  database.py  models.py  schemas.py  worker.py
│       ├── connectors/   # BaseConnector + mock connectors + JSON datasets
│       ├── ai/           # provider abstraction (openai/gemini/ollama/mock) + embeddings
│       ├── agents/       # 5 agents + LangGraph orchestrator
│       ├── rag/          # ChromaDB store + ingestion
│       ├── services/     # ingestion, analytics, insights, reports, email
│       ├── tasks/        # Celery jobs
│       └── api/routes/   # chat, agents, insights, connectors, knowledge, reports, health
└── frontend/
    └── src/
        ├── pages/        # Dashboard, Chat, Insights, Connectors, Knowledge, Reports
        ├── components/   # shadcn/ui-style primitives + cards
        └── lib/          # API client, utils
```
