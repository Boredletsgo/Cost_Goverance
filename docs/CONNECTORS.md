# Writing an InfraMind Connector

Connectors are how InfraMind ingests data from any source — a cloud provider, a
Kubernetes cluster, a SaaS API, or a flat file. Every connector implements the same
small contract, so the rest of the platform (ingestion, analytics, agents, RAG, UI)
stays fully decoupled from any vendor SDK.

This guide shows how to add one. The bundled connectors (`azure`, `aws`, `gcp`,
`kubernetes`, `github`) are mock connectors that read JSON datasets, so the whole
platform runs offline with zero credentials.

---

## The contract

Every connector subclasses `BaseConnector`
([backend/app/connectors/base.py](../backend/app/connectors/base.py)) and returns
**normalized** records:

```python
class BaseConnector:
    name: str                      # stable id, e.g. "datadog"
    description: str               # shown in the UI
    capabilities: list[ConnectorCapability]

    async def get_cost_data(self)         -> list[dict]
    async def get_resources(self)         -> list[dict]
    async def get_events(self)            -> list[dict]
    async def get_security_findings(self) -> list[dict]
    async def execute_action(self, action, params) -> dict
```

### Normalized record shapes

| Method | Each item must contain |
|--------|------------------------|
| `get_cost_data` | `{date, service, resource_id, amount, currency}` |
| `get_resources` | `{external_id, name, type, region, status, monthly_cost, tags, attributes}` |
| `get_events` | `{external_id, kind, severity, title, description, resource_id, occurred_at, meta}` |
| `get_security_findings` | `{external_id, title, description, severity, category, resource_id, cvss, status, detected_at, meta}` |
| `execute_action` | returns `{ok, detail, data}` |

`capabilities` advertises which of these the connector supports (`COST`, `RESOURCES`,
`EVENTS`, `SECURITY`, `ACTIONS`), driving what the UI shows and what agents call.

---

## Option 1 — A mock/JSON connector (easiest)

Great for demos, tests, or air-gapped environments. Subclass `JsonMockConnector`
([backend/app/connectors/mock_base.py](../backend/app/connectors/mock_base.py)),
which loads `app/connectors/data/<name>/{cost,resources,events,security}.json`.

**1. Create the connector class** — `backend/app/connectors/datadog.py`:

```python
from app.connectors.mock_base import JsonMockConnector


class DatadogConnector(JsonMockConnector):
    name = "datadog"
    description = "Datadog (mock) — monitors, SLOs, cost."
```

**2. Add datasets** under `backend/app/connectors/data/datadog/`:

```jsonc
// cost.json
[
  { "date": "2026-06-15", "service": "APM", "resource_id": "dd-apm",
    "amount": 142.50, "currency": "USD" }
]
```
(plus `resources.json`, `events.json`, `security.json` — see existing folders for
realistic examples).

**3. Register it** in
[backend/app/connectors/registry.py](../backend/app/connectors/registry.py):

```python
from app.connectors.datadog import DatadogConnector

_REGISTRY = {
    # ...existing...
    DatadogConnector.name: DatadogConnector,
}
```

**4. Enable it** by adding `datadog` to `ENABLED_CONNECTORS` in your `.env`:

```bash
ENABLED_CONNECTORS=azure,aws,gcp,kubernetes,github,datadog
```

---

## Option 2 — A live connector

Subclass `BaseConnector` directly and call the real API/SDK inside each method.
Keep all credentials in config/env — never hardcode secrets.

```python
import httpx
from app.connectors.base import BaseConnector, ConnectorCapability
from app.config import settings


class DatadogConnector(BaseConnector):
    name = "datadog"
    description = "Datadog — live monitors, SLOs, and cost."
    capabilities = [ConnectorCapability.COST, ConnectorCapability.EVENTS]

    def __init__(self, config=None):
        super().__init__(config)
        self._api_key = self.config.get("api_key") or settings.datadog_api_key

    async def get_cost_data(self):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://api.datadoghq.com/api/v2/usage/cost_by_org",
                headers={"DD-API-KEY": self._api_key},
            )
            resp.raise_for_status()
            raw = resp.json()
        # Normalize to InfraMind's shape:
        return [
            {
                "date": row["date"],
                "service": row["product"],
                "resource_id": row.get("org_name", "datadog"),
                "amount": float(row["cost"]),
                "currency": "USD",
            }
            for row in raw["data"]
        ]

    async def get_resources(self):  return []
    async def get_events(self):     return []
    async def get_security_findings(self): return []

    async def execute_action(self, action, params):
        return {"ok": False, "detail": "actions not supported", "data": {}}
```

Add any new settings (e.g. `datadog_api_key`) to
[backend/app/config.py](../backend/app/config.py), then register + enable exactly
as in Option 1.

> **Tip:** Only return the capabilities you actually implement. Returning `[]` from
> an unsupported method is fine; agents simply skip empty data.

---

## Verifying your connector

```bash
cd backend
python -m app.cli init-db
python -m app.cli seed          # ingests every enabled connector
# then check it shows up:
curl -s localhost:8000/api/connectors | jq '.[].name'
# re-ingest at any time without a restart:
curl -s -X POST localhost:8000/api/connectors/refresh
```

Once data is ingested, the agents, dashboard, anomaly detection, and RAG search all
pick it up automatically — no further wiring required.

---

## Registering at runtime (plugins)

Third-party packages can register a connector without editing the registry file:

```python
from app.connectors.registry import registry
registry.register(MyConnector)
```

This makes it possible to ship connectors as separate pip packages.
