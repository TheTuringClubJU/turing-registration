"""
app/core/router.py

Re-exports the attendance router so any legacy import of
`app.core.router` still resolves.

The canonical router lives in app/attendance/router.py — edit there,
not here.
"""
from app.attendance.router import router  # noqa: F401
