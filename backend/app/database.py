"""Database engine + session management (SQLAlchemy)."""
from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine, inspect, text
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
    """Create all tables and automatically add any missing columns to existing tables."""
    from . import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)

    # Inspect AFTER create_all so we see the true current schema.
    # Each ALTER TABLE runs in its own committed transaction so the column
    # is fully visible to subsequent queries (important for Postgres).
    for table_name, table in Base.metadata.tables.items():
        inspector = inspect(engine)  # fresh inspector per table to avoid stale cache
        try:
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        except Exception:
            continue

        for col_name, column in table.columns.items():
            if col_name not in existing_cols:
                col_type = column.type.compile(engine.dialect)
                nullable = "NULL" if column.nullable else "NOT NULL"
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable}"
                with engine.begin() as conn:
                    conn.execute(text(alter_query))

