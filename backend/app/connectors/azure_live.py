"""Live Azure connector.

Pulls real data from an Azure subscription using the azure-mgmt-* SDKs and
``DefaultAzureCredential`` (so ``az login``, managed identity, environment vars,
or an explicit service principal in ``.env`` all work).

Design rules:
* Cloud SDKs are imported lazily so the lite install (mock-only) never needs them.
* Every data method falls back to the bundled mock dataset on ANY failure, so the
  platform keeps working even with partial permissions or transient API errors.
* Credentials are read from the environment only and never persisted.
"""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any, Dict, List, Tuple

from app.config import settings
from app.connectors.azure import AzureConnector
from app.logging_config import get_logger

logger = get_logger(__name__)


def _azure_credential():
    """Build the best available Azure credential."""
    from azure.identity import ClientSecretCredential, DefaultAzureCredential

    if settings.azure_client_id and settings.azure_client_secret and settings.azure_tenant_id:
        return ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)


class AzureLiveConnector(AzureConnector):
    """Azure connector backed by live Cost Management / Resource Graph / Monitor APIs."""

    description = "Microsoft Azure (live) — Cost Management, Resources, Activity Log, Defender."

    # ---- capability checks (used by the Setup page) -----------------------
    @classmethod
    def sdk_available(cls) -> bool:
        try:
            import azure.identity  # noqa: F401
            import azure.mgmt.resource  # noqa: F401
            return True
        except Exception:
            return False

    @classmethod
    def credentials_detected(cls) -> bool:
        # A subscription id is the minimum; the credential itself is validated by test_connection.
        return bool(settings.azure_subscription_id)

    async def test_connection(self) -> Dict[str, Any]:
        if not self.sdk_available():
            return {"ok": False, "detail": "Azure SDKs not installed. pip install -r requirements-cloud.txt"}
        if not settings.azure_subscription_id:
            return {"ok": False, "detail": "AZURE_SUBSCRIPTION_ID is not set."}
        try:
            count = await asyncio.to_thread(self._ping)
            return {"ok": True, "detail": f"Connected to subscription; {count} resources visible."}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}

    def _ping(self) -> int:
        from azure.mgmt.resource import ResourceManagementClient

        client = ResourceManagementClient(_azure_credential(), settings.azure_subscription_id)
        return sum(1 for _ in client.resources.list(top=5))

    # ---- data methods (live with mock fallback) ---------------------------
    async def get_cost_data(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_cost)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Azure live cost failed (%s); using mock fallback.", exc)
            return await super().get_cost_data()

    async def get_resources(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_resources)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Azure live resources failed (%s); using mock fallback.", exc)
            return await super().get_resources()

    async def get_events(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_events)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Azure live events failed (%s); using mock fallback.", exc)
            return await super().get_events()

    async def get_security_findings(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_security)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Azure live security failed (%s); using mock fallback.", exc)
            return await super().get_security_findings()

    # ---- live implementations (synchronous SDK calls) ---------------------
    def _scope(self) -> str:
        return f"/subscriptions/{settings.azure_subscription_id}"

    def _live_cost(self) -> List[Dict[str, Any]]:
        from azure.mgmt.costmanagement import CostManagementClient

        client = CostManagementClient(_azure_credential())
        parameters = {
            "type": "ActualCost",
            "timeframe": "MonthToDate",
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ServiceName"}],
            },
        }
        result = client.query.usage(scope=self._scope(), parameters=parameters)
        cols = [c.name for c in result.columns]
        idx = {name: i for i, name in enumerate(cols)}
        out: List[Dict[str, Any]] = []
        for row in result.rows or []:
            raw_date = str(row[idx.get("UsageDate", 1)])
            # UsageDate comes back as YYYYMMDD int
            date = (
                f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                if raw_date.isdigit() and len(raw_date) == 8
                else raw_date
            )
            out.append(
                {
                    "date": date,
                    "service": row[idx.get("ServiceName", 2)] if "ServiceName" in idx else "Azure",
                    "resource_id": "azure",
                    "amount": float(row[idx.get("Cost", 0)]),
                    "currency": row[idx.get("Currency", len(row) - 1)] if "Currency" in idx else "USD",
                }
            )
        return out

    def _live_resources(self) -> List[Dict[str, Any]]:
        from azure.mgmt.resource import ResourceManagementClient

        client = ResourceManagementClient(_azure_credential(), settings.azure_subscription_id)
        out: List[Dict[str, Any]] = []
        for r in client.resources.list():
            out.append(
                {
                    "external_id": r.id or "",
                    "name": r.name or "",
                    "type": r.type or "",
                    "region": r.location or "",
                    "status": "active",
                    "monthly_cost": 0.0,
                    "tags": dict(r.tags or {}),
                    "attributes": {"kind": getattr(r, "kind", None), "sku": str(getattr(r, "sku", "") or "")},
                }
            )
        return out

    def _live_events(self) -> List[Dict[str, Any]]:
        from azure.mgmt.monitor import MonitorManagementClient

        client = MonitorManagementClient(_azure_credential(), settings.azure_subscription_id)
        now = dt.datetime.now(dt.timezone.utc)
        start = now - dt.timedelta(days=7)
        filt = (
            f"eventTimestamp ge '{start.isoformat()}' and eventTimestamp le '{now.isoformat()}'"
        )
        out: List[Dict[str, Any]] = []
        for e in client.activity_logs.list(filter=filt):
            level = (getattr(e, "level", None) or "").lower()
            severity = {"critical": "critical", "error": "high", "warning": "medium"}.get(level, "info")
            out.append(
                {
                    "external_id": getattr(e, "event_data_id", "") or "",
                    "kind": "activity",
                    "severity": severity,
                    "title": (getattr(e.operation_name, "localized_value", None) if e.operation_name else None)
                    or "Azure activity",
                    "description": (getattr(e.status, "localized_value", "") if e.status else "") or "",
                    "resource_id": getattr(e, "resource_id", "") or "",
                    "occurred_at": e.event_timestamp.isoformat() if getattr(e, "event_timestamp", None) else "",
                    "meta": {"category": getattr(e.category, "localized_value", None) if e.category else None},
                }
            )
            if len(out) >= 200:
                break
        return out

    def _live_security(self) -> List[Dict[str, Any]]:
        from azure.mgmt.security import SecurityCenter

        client = SecurityCenter(_azure_credential(), settings.azure_subscription_id)
        out: List[Dict[str, Any]] = []
        for a in client.assessments.list(self._scope()):
            status = getattr(getattr(a, "status", None), "code", "") or ""
            if status.lower() == "healthy":
                continue
            sev = (getattr(getattr(a, "metadata", None), "severity", None) or "medium")
            out.append(
                {
                    "external_id": a.name or "",
                    "title": getattr(a, "display_name", None) or a.name or "Assessment",
                    "description": getattr(getattr(a, "status", None), "description", "") or "",
                    "severity": str(sev).lower(),
                    "category": "configuration",
                    "resource_id": getattr(a, "resource_details", None) and getattr(a.resource_details, "id", "") or "",
                    "cvss": 0.0,
                    "status": status,
                    "detected_at": "",
                    "meta": {},
                }
            )
            if len(out) >= 200:
                break
        return out
