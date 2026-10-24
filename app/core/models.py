"""
app/core/models.py

Re-exports attendance-domain models so that any legacy imports from
app.core.models still resolve correctly.

The canonical definitions live in app/attendance/models.py — edit there,
not here.
"""
from app.attendance.models import (  # noqa: F401
    Organiser,
    Attendance,
    AttendanceStatus,
    CheckinMethod,
)
