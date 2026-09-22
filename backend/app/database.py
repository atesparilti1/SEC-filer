from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# `check_same_thread` is only relevant to SQLite; harmless to set unconditionally
# but only applied when the driver is actually SQLite so a future PostgreSQL
# swap (DATABASE_URL=postgresql+psycopg2://...) needs no code change here.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (ensure models are registered)

    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """Adds newly introduced nullable/defaulted columns to existing SQLite tables.

    A lightweight stand-in for a migration tool, sufficient for this project's
    single additive-column case; a real deployment against PostgreSQL should
    use Alembic instead (see README).
    """
    inspector = inspect(engine)
    if "analyzed_filings" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("analyzed_filings")}
    if "is_demo" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE analyzed_filings ADD COLUMN is_demo BOOLEAN DEFAULT 0"))
