"""
app/main.py

FastAPI entrypoint. Mounts every domain's router.
Currently minimal — routers get added here as each domain implements
its router.py (events, registrations, attendance).
"""

from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine

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


# Routers get mounted here as they're built, e.g.:
# from app.events.router import router as events_router
# app.include_router(events_router)