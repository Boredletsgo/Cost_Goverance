"""Ingest infrastructure data + best-practice knowledge into the RAG store."""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app import models
from app.logging_config import get_logger
from app.rag.store import get_store

logger = get_logger(__name__)

# Static infrastructure best-practice knowledge base. In production this would be
# sourced from runbooks, wikis, and vendor docs via connectors.
_KNOWLEDGE_BASE: List[dict] = [
    {
        "id": "kb-cost-anomaly",
        "text": "A cost anomaly is a statistically significant deviation from a "
        "service's recent spend baseline. Common causes: a new code path issuing "
        "expensive queries, missing database indexes causing full scans, runaway "
        "data egress, autoscaling loops, and orphaned resources left after a "
        "deployment. Investigate by correlating the spike date with deployments "
        "and change events on the same resource.",
        "metadata": {"topic": "cost", "source": "playbook"},
    },
    {
        "id": "kb-db-dtu",
        "text": "Sustained high DTU/CPU on a managed SQL database after a release "
        "usually indicates a missing index or a non-sargable query. Remediation: "
        "capture the top queries, add a covering index, and set a statement "
        "timeout. This also reduces cost because compute scales with query work.",
        "metadata": {"topic": "incident", "source": "playbook"},
    },
    {
        "id": "kb-orphaned",
        "text": "Orphaned resources (unattached disks, unassociated public IPs, "
        "detached EBS volumes, stale snapshots) incur cost with zero value. Safe "
        "cleanup: confirm no recent attachment, snapshot if needed for recovery, "
        "then delete. These are the lowest-risk, fastest cost wins.",
        "metadata": {"topic": "optimization", "source": "playbook"},
    },
    {
        "id": "kb-rightsizing",
        "text": "Rightsizing matches provisioned capacity to actual utilization. "
        "VMs/instances below ~10% average CPU for 14+ days are downsizing "
        "candidates. Kubernetes deployments where used CPU/memory is far below "
        "requests are over-provisioned; reduce requests to improve bin-packing.",
        "metadata": {"topic": "optimization", "source": "playbook"},
    },
    {
        "id": "kb-public-exposure",
        "text": "Internet-exposed management ports (SSH 22, RDP 3389, DB ports like "
        "3306/5432) open to 0.0.0.0/0 are critical risks. Restrict to known CIDRs "
        "or a bastion, and prefer private endpoints. Treat these as top priority "
        "in any security triage.",
        "metadata": {"topic": "security", "source": "playbook"},
    },
    {
        "id": "kb-secrets",
        "text": "Hardcoded secrets in source control are critical. Rotate the "
        "exposed credential immediately, purge it from history, and move it to a "
        "secret manager. Stale/unrotated access keys older than 90 days should be "
        "rotated on a schedule.",
        "metadata": {"topic": "security", "source": "playbook"},
    },
    {
        "id": "kb-storage-tiering",
        "text": "Object storage holding cold data in a hot/standard tier wastes "
        "money. Apply lifecycle policies to transition infrequently accessed data "
        "to IA/Cool/Glacier tiers. Logs older than 30-90 days are typical "
        "candidates.",
        "metadata": {"topic": "optimization", "source": "playbook"},
    },
    {
        "id": "kb-oomkill",
        "text": "OOMKilled crashloops occur when a container's memory limit is below "
        "its working set, often after a model/image upgrade. Remediation: raise "
        "memory limits to observed peak plus headroom, or reduce footprint. Set "
        "requests to typical usage and limits to peak.",
        "metadata": {"topic": "incident", "source": "playbook"},
    },
]


def ingest_knowledge_base() -> int:
    return get_store().add(_KNOWLEDGE_BASE)


def ingest_db_records(db: Session) -> int:
    """Index live resources, events, findings, and insights for semantic search."""
    docs: List[dict] = []

    for r in db.query(models.Resource).all():
        docs.append(
            {
                "id": f"res-{r.id}",
                "text": (
                    f"Resource {r.name} ({r.type}) on {r.connector} in {r.region}. "
                    f"Status {r.status}. Monthly cost ${r.monthly_cost:.0f}. "
                    f"Attributes: {r.attributes}."
                ),
                "metadata": {"kind": "resource", "connector": r.connector, "ref": r.external_id},
            }
        )

    for e in db.query(models.Event).all():
        docs.append(
            {
                "id": f"evt-{e.id}",
                "text": f"[{e.kind}/{e.severity}] {e.title}. {e.description} "
                f"(resource {e.resource_id}, {e.occurred_at}, {e.connector}).",
                "metadata": {"kind": "event", "connector": e.connector, "ref": e.external_id},
            }
        )

    for f in db.query(models.SecurityFinding).all():
        docs.append(
            {
                "id": f"sec-{f.id}",
                "text": f"[{f.severity}] {f.title}. {f.description} "
                f"(category {f.category}, resource {f.resource_id}, {f.connector}).",
                "metadata": {"kind": "security", "connector": f.connector, "ref": f.external_id},
            }
        )

    for i in db.query(models.Insight).all():
        docs.append(
            {
                "id": f"ins-{i.id}",
                "text": f"[{i.agent}/{i.kind}] {i.title}. {i.summary}",
                "metadata": {"kind": "insight", "agent": i.agent},
            }
        )

    added = get_store().add(docs)
    logger.info("Indexed %d DB records into knowledge store.", added)
    return added
