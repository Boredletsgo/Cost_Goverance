"""Deterministic analytics used by the agents (anomaly detection, aggregation).

Keeping the quantitative logic in Python (not the LLM) makes results
reproducible and free of hallucination; the LLM only narrates these facts.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Dict, List

from sqlalchemy.orm import Session

from app import models


def daily_totals(db: Session) -> List[dict]:
    """Total spend per day across all connectors."""
    totals: Dict[str, float] = defaultdict(float)
    for rec in db.query(models.CostRecord).all():
        totals[rec.date] += rec.amount
    return [{"date": d, "amount": round(a, 2)} for d, a in sorted(totals.items())]


def cost_by_service(db: Session) -> List[dict]:
    totals: Dict[str, float] = defaultdict(float)
    for rec in db.query(models.CostRecord).all():
        totals[f"{rec.connector}:{rec.service}"] += rec.amount
    rows = [
        {"service": k.split(":", 1)[1], "connector": k.split(":", 1)[0], "amount": round(v, 2)}
        for k, v in totals.items()
    ]
    return sorted(rows, key=lambda r: r["amount"], reverse=True)


def detect_cost_anomalies(db: Session, z_threshold: float = 2.5) -> List[dict]:
    """Per service/connector, flag days whose spend is a statistical outlier.

    Uses a rolling baseline (all prior days) and z-score. Also reports the
    absolute and percentage increase so impact can be quantified.
    """
    series: Dict[str, List[tuple]] = defaultdict(list)
    for rec in db.query(models.CostRecord).order_by(models.CostRecord.date).all():
        key = f"{rec.connector}:{rec.service}:{rec.resource_id}"
        series[key].append((rec.date, rec.amount))

    anomalies: List[dict] = []
    for key, points in series.items():
        if len(points) < 5:
            continue
        connector, service, resource_id = key.split(":", 2)
        amounts = [a for _, a in points]
        for i in range(4, len(points)):
            history = amounts[:i]
            mean = statistics.mean(history)
            stdev = statistics.pstdev(history) or 1e-9
            date, value = points[i]
            z = (value - mean) / stdev
            if z >= z_threshold and value > mean:
                anomalies.append(
                    {
                        "connector": connector,
                        "service": service,
                        "resource_id": resource_id,
                        "date": date,
                        "amount": round(value, 2),
                        "baseline": round(mean, 2),
                        "delta": round(value - mean, 2),
                        "increase_pct": round((value - mean) / mean * 100, 1),
                        "z_score": round(z, 2),
                    }
                )
    return sorted(anomalies, key=lambda a: a["delta"], reverse=True)


def forecast_monthly(db: Session) -> dict:
    """Naive run-rate forecast from the most recent days of total spend."""
    totals = daily_totals(db)
    if not totals:
        return {"daily_run_rate": 0.0, "projected_30d": 0.0, "trend_pct": 0.0}
    recent = totals[-3:] if len(totals) >= 3 else totals
    run_rate = statistics.mean([t["amount"] for t in recent])
    if len(totals) >= 6:
        prior = statistics.mean([t["amount"] for t in totals[-6:-3]])
        trend = (run_rate - prior) / prior * 100 if prior else 0.0
    else:
        trend = 0.0
    return {
        "daily_run_rate": round(run_rate, 2),
        "projected_30d": round(run_rate * 30, 2),
        "trend_pct": round(trend, 1),
    }


def find_waste(db: Session) -> List[dict]:
    """Identify wasteful resources: orphaned, idle, over-provisioned, untiered."""
    waste: List[dict] = []
    for r in db.query(models.Resource).all():
        attrs = r.attributes or {}
        reason = None
        monthly = r.monthly_cost
        if r.status in ("unattached", "unassociated", "available") and not attrs.get("attached", True):
            reason = "orphaned"
        elif attrs.get("idle") or (isinstance(attrs.get("avg_cpu_pct"), (int, float)) and attrs["avg_cpu_pct"] < 5):
            reason = "idle / very low utilization"
        elif attrs.get("overprovisioned"):
            reason = "over-provisioned requests vs usage"
        elif attrs.get("lifecycle_policy") is False:
            reason = "no storage lifecycle policy (cold data in hot tier)"
            monthly = r.monthly_cost * 0.6  # estimated recoverable portion
        elif r.type == "Snapshot" and attrs.get("age_days", 0) > 120:
            reason = "stale snapshot"
        if reason:
            waste.append(
                {
                    "resource_id": r.external_id,
                    "name": r.name,
                    "connector": r.connector,
                    "type": r.type,
                    "reason": reason,
                    "monthly_savings": round(monthly, 2),
                }
            )
    return sorted(waste, key=lambda w: w["monthly_savings"], reverse=True)


def severity_rank(sev: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(sev.lower(), 0)
