"""Database engine, session, and base model setup."""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _normalized_url() -> str:
    url = settings.database_url
    # Ensure sqlite directory exists for local dev
    if url.startswith("sqlite"):
        path = url.split("///")[-1]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return url


_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    _normalized_url(),
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Imports models to register metadata."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
