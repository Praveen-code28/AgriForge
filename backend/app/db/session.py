import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _create_engine():
    database_url = settings.DATABASE_URL
    if database_url.startswith(("postgresql://", "postgres://")):
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return engine
        except Exception as exc:  # pragma: no cover - local fallback path
            logger.warning("PostgreSQL unavailable; falling back to SQLite for local development: %s", exc)

    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})

    return create_engine("sqlite:///./agriforge.db", connect_args={"check_same_thread": False})


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from backend.app.models import Base

    Base.metadata.create_all(bind=engine)


init_db()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
