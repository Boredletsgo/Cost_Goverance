"""Command-line entrypoints used by docker-compose and local dev."""
from __future__ import annotations

import sys

from app.database import SessionLocal, init_db as _init_db
from app.logging_config import configure_logging, get_logger
from app.rag.ingest import ingest_db_records, ingest_knowledge_base
from app.services.ingestion import ingest_all
from app.services.insights import run_and_persist

logger = get_logger(__name__)


def init_db() -> None:
    _init_db()
    logger.info("Database tables created.")


def seed() -> None:
    """Idempotent: load connectors, build RAG index, run agents."""
    db = SessionLocal()
    try:
        counts = ingest_all(db)
        logger.info("Connector ingestion: %s", counts)
        ingest_knowledge_base()
        ingest_db_records(db)
        insights = run_and_persist(db, replace=True)
        logger.info("Seed complete. %d insights generated.", len(insights))
    finally:
        db.close()


def main() -> None:
    configure_logging()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init-db":
        init_db()
    elif cmd == "seed":
        seed()
    else:
        print("Usage: python -m app.cli [init-db|seed]")
        sys.exit(1)


if __name__ == "__main__":
    main()
