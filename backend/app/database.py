"""Database engine + session management (SQLAlchemy)."""
from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

_connect_args = {}
if db_url.startswith("sqlite"):
    # Needed for SQLite when used across FastAPI's threadpool.
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. For real migrations use Alembic."""
    from . import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)
