"""Live AWS connector.

Pulls real data from an AWS account using boto3 and its standard credential chain
(shared profile, environment variables, instance role, or explicit keys in ``.env``).

Same rules as the Azure live connector: lazy SDK import, graceful mock fallback on
any failure, and credentials are read from the environment only.
"""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any, Dict, List

from app.config import settings
from app.connectors.aws import AWSConnector
from app.logging_config import get_logger

logger = get_logger(__name__)


def _session():
    import boto3

    kwargs: Dict[str, Any] = {"region_name": settings.aws_region or "us-east-1"}
    if settings.aws_profile:
        kwargs["profile_name"] = settings.aws_profile
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.Session(**kwargs)


def _arn_parts(arn: str) -> Dict[str, str]:
    # arn:partition:service:region:account:resource...
    parts = arn.split(":")
    return {
        "service": parts[2] if len(parts) > 2 else "",
        "region": parts[3] if len(parts) > 3 else "",
        "resource": parts[5] if len(parts) > 5 else (parts[-1] if parts else ""),
    }


class AWSLiveConnector(AWSConnector):
    """AWS connector backed by Cost Explorer / Tagging API / CloudTrail / Security Hub."""

    description = "Amazon Web Services (live) — Cost Explorer, Tagging API, CloudTrail, Security Hub."

    # ---- capability checks ------------------------------------------------
    @classmethod
    def sdk_available(cls) -> bool:
        try:
            import boto3  # noqa: F401
            return True
        except Exception:
            return False

    @classmethod
    def credentials_detected(cls) -> bool:
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            return True
        if settings.aws_profile:
            return True
        if not cls.sdk_available():
            return False
        try:
            return _session().get_credentials() is not None
        except Exception:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        if not self.sdk_available():
            return {"ok": False, "detail": "boto3 not installed. pip install -r requirements-cloud.txt"}
        try:
            ident = await asyncio.to_thread(self._ping)
            return {"ok": True, "detail": f"Connected as {ident}."}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}

    def _ping(self) -> str:
        sts = _session().client("sts")
        ident = sts.get_caller_identity()
        return ident.get("Arn", ident.get("Account", "unknown"))

    # ---- data methods (live with mock fallback) ---------------------------
    async def get_cost_data(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_cost)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AWS live cost failed (%s); using mock fallback.", exc)
            return await super().get_cost_data()

    async def get_resources(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_resources)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AWS live resources failed (%s); using mock fallback.", exc)
            return await super().get_resources()

    async def get_events(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_events)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AWS live events failed (%s); using mock fallback.", exc)
            return await super().get_events()

    async def get_security_findings(self) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._live_security)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AWS live security failed (%s); using mock fallback.", exc)
            return await super().get_security_findings()

    # ---- live implementations --------------------------------------------
    def _live_cost(self) -> List[Dict[str, Any]]:
        ce = _session().client("ce")
        end = dt.date.today()
        start = end.replace(day=1)
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        out: List[Dict[str, Any]] = []
        for period in resp.get("ResultsByTime", []):
            date = period.get("TimePeriod", {}).get("Start", "")
            for group in period.get("Groups", []):
                service = (group.get("Keys") or ["AWS"])[0]
                amount = group.get("Metrics", {}).get("UnblendedCost", {})
                out.append(
                    {
                        "date": date,
                        "service": service,
                        "resource_id": "aws",
                        "amount": float(amount.get("Amount", 0.0)),
                        "currency": amount.get("Unit", "USD"),
                    }
                )
        return out

    def _live_resources(self) -> List[Dict[str, Any]]:
        client = _session().client("resourcegroupstaggingapi")
        paginator = client.get_paginator("get_resources")
        out: List[Dict[str, Any]] = []
        for page in paginator.paginate():
            for item in page.get("ResourceTagMappingList", []):
                arn = item.get("ResourceARN", "")
                parts = _arn_parts(arn)
                tags = {t["Key"]: t.get("Value", "") for t in item.get("Tags", [])}
                out.append(
                    {
                        "external_id": arn,
                        "name": parts["resource"],
                        "type": parts["service"],
                        "region": parts["region"],
                        "status": "active",
                        "monthly_cost": 0.0,
                        "tags": tags,
                        "attributes": {},
                    }
                )
                if len(out) >= 500:
                    return out
        return out

    def _live_events(self) -> List[Dict[str, Any]]:
        client = _session().client("cloudtrail")
        end = dt.datetime.now(dt.timezone.utc)
        start = end - dt.timedelta(days=7)
        resp = client.lookup_events(StartTime=start, EndTime=end, MaxResults=200)
        out: List[Dict[str, Any]] = []
        for e in resp.get("Events", []):
            resources = e.get("Resources", [])
            resource_id = resources[0].get("ResourceName", "") if resources else ""
            out.append(
                {
                    "external_id": e.get("EventId", ""),
                    "kind": "cloudtrail",
                    "severity": "info",
                    "title": e.get("EventName", "AWS event"),
                    "description": f"{e.get('EventSource', '')} by {e.get('Username', 'unknown')}",
                    "resource_id": resource_id,
                    "occurred_at": e.get("EventTime").isoformat() if e.get("EventTime") else "",
                    "meta": {"source": e.get("EventSource", "")},
                }
            )
        return out

    def _live_security(self) -> List[Dict[str, Any]]:
        client = _session().client("securityhub")
        resp = client.get_findings(MaxResults=100)
        out: List[Dict[str, Any]] = []
        for f in resp.get("Findings", []):
            sev = (f.get("Severity", {}).get("Label", "LOW") or "LOW").lower()
            resources = f.get("Resources", [])
            resource_id = resources[0].get("Id", "") if resources else ""
            out.append(
                {
                    "external_id": f.get("Id", ""),
                    "title": f.get("Title", "Finding"),
                    "description": f.get("Description", ""),
                    "severity": sev,
                    "category": (f.get("Types") or ["configuration"])[0],
                    "resource_id": resource_id,
                    "cvss": float(f.get("Severity", {}).get("Normalized", 0)) / 10.0,
                    "status": f.get("Workflow", {}).get("Status", "NEW"),
                    "detected_at": f.get("CreatedAt", ""),
                    "meta": {"product": f.get("ProductArn", "")},
                }
            )
        return out
