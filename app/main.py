"""
app/main.py

FastAPI entrypoint. Mounts every domain's router.
Currently minimal — routers get added here as each domain implements
its router.py (events, registrations, attendance).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Import all models so SQLAlchemy resolves all cross-model relationship mappers
import app.events.models  # noqa: F401
import app.registrations.models  # noqa: F401
import app.attendance.models  # noqa: F401

from app.attendance.router import router as attendance_router
from app.core.database import engine
from app.core.security import router as auth_router
from app.events.router import router as events_router
from app.registrations.router import router as registrations_router

app = FastAPI(title="Turing Registration API")

# Allow requests from Vercel frontend, local dev, and public form
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://turing-registration.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root info endpoint so root URL doesn't return 404."""
    return {
        "status": "ok",
        "name": "Turing Registration API",
        "docs": "/docs",
        "health": "/health",
    }


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

app.include_router(events_router)
app.include_router(registrations_router)
