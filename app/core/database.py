"""
app/core/database.py

SQLAlchemy engine + session setup, shared across every domain.
Every domain's models.py imports `Base` from here.
Every domain's crud.py (via router.py) uses `get_db` as a FastAPI dependency.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Single engine, shared connection pool for the whole app.
# pool_pre_ping avoids errors from stale connections Neon may have closed
# after a period of inactivity (common on free-tier serverless Postgres).
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Every model in every domain (events/models.py, registrations/models.py,
# attendance/models.py) declares its class as `class X(Base):` — this is
# the single shared declarative base tying them all together.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session for the duration of one request,
    always closes it afterward even if the request raises.

    Usage in a router:
        from app.core.database import get_db
        from fastapi import Depends

        @router.get("/events/active")
        def get_active_event(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()