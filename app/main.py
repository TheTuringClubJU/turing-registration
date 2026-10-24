"""
app/main.py

FastAPI entrypoint. Mounts every domain's router.
Currently minimal — routers get added here as each domain implements
its router.py (events, registrations, attendance).
"""

from fastapi import FastAPI
from sqlalchemy import text

# Import all models so SQLAlchemy resolves all cross-model relationship mappers
import app.events.models  # noqa: F401
import app.registrations.models  # noqa: F401
import app.attendance.models  # noqa: F401

from app.attendance.router import router as attendance_router
from app.core.database import engine
from app.core.security import router as auth_router

app = FastAPI(title="Turing Registration API")


@app.get("/health")
def health_check():
    """
    Basic smoke-test endpoint — confirms the app is running AND can reach
    the database, not just that the process started.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    return {"status": "ok", "database": db_status}


app.include_router(auth_router)
app.include_router(attendance_router)
