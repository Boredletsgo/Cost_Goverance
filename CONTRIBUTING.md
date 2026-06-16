# Contributing to InfraMind

Thanks for your interest in improving InfraMind! This project is **open-source first**,
**cloud-agnostic**, and **extensible** — contributions of connectors, agents, analytics,
and UI are all welcome.

## Getting set up

The fastest path needs **no Docker, no API keys, no Postgres/Redis**:

```bash
# macOS / Linux
./scripts/dev.sh
```
```powershell
# Windows
./scripts/dev.ps1
```

This creates the backend virtualenv, installs the lite dependencies, seeds a demo
SQLite database, and starts both servers. See [README.md](README.md) for details and
the Docker-based full-stack option.

## Project layout

| Path | What lives here |
|------|-----------------|
| `backend/app/connectors/` | Integrations (`BaseConnector` + mock JSON datasets) |
| `backend/app/agents/` | LangGraph agents + router |
| `backend/app/services/` | Deterministic analytics, ingestion, insights, reports |
| `backend/app/ai/` | LLM provider abstraction + embeddings |
| `backend/app/api/routes/` | FastAPI endpoints |
| `frontend/src/` | React + TypeScript + Tailwind UI |
| `docs/` | Extension guides (e.g. writing a connector) |

## Development guidelines

- **Keep the offline default working.** Anything you add must run with `AI_PROVIDER=mock`
  and the hashing embedder — no required API keys.
- **Analytics is deterministic.** Quantitative logic (anomaly detection, forecasting,
  correlation) lives in `services/` as plain Python. The LLM only *narrates* results.
- **Connectors are uniform.** Implement the small `BaseConnector` contract; don't leak
  vendor SDK specifics into agents or the UI. See [docs/CONNECTORS.md](docs/CONNECTORS.md).
- **Style:** Python is type-hinted; keep functions small and pure where practical.
  Frontend uses functional components and the existing `components/ui` primitives.

## Before you open a PR

Run the same checks CI runs:

```bash
# Backend: byte-compile + validate mock datasets
cd backend
python -m compileall app
python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('app/connectors/data/**/*.json',recursive=True)]"

# Frontend: type-check + build
cd ../frontend
npm ci
npm run build
```

Please:
1. Keep PRs focused and describe the change + how you tested it.
2. Add or update mock data when adding a connector so it works for everyone offline.
3. Update docs/README when you change behavior or add endpoints.

## Reporting issues

Open a GitHub issue with reproduction steps, expected vs. actual behavior, and your OS /
Python / Node versions. Security-sensitive reports: please disclose privately first.
