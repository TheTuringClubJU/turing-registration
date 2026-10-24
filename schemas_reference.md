# Schemas Reference

> Source of truth for all Pydantic schemas (`schemas.py` files) used across the project.
> Every field listed here must match both the SQLAlchemy models and `schema.sql`.

---

## `app/attendance/schemas.py`

### `CheckinRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registration_id` | `UUID` | ✅ | The unique registration UUID of the attendee being checked in |

### `AttendanceOut`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registration_id` | `UUID` | ✅ | The registration this attendance record belongs to |
| `status` | `AttendanceStatus` enum | ✅ | `not_checked_in` or `checked_in` |
| `method` | `CheckinMethod` enum \| `null` | ❌ | `qr` or `manual`; `null` until checked in |
| `checked_in_at` | `datetime` \| `null` | ❌ | UTC timestamp of check-in; `null` until checked in |
| `checked_in_by` | `UUID` \| `null` | ❌ | UUID of the organiser who performed the check-in; `null` until checked in |

> **Config:** `from_attributes = True` (reads from SQLAlchemy ORM objects directly)

### `SummaryOut`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_registered` | `int` | ✅ | Total attendance rows for the event (= total registrations) |
| `checked_in` | `int` | ✅ | Count of rows with `status = checked_in` |
| `remaining` | `int` | ✅ | `total_registered − checked_in` |

> **Config:** `from_attributes = True`

---

## `app/events/schemas.py`

> Currently empty — pending implementation. Will document `EventOut` and `EventCreate` schemas once built.

---

## `app/registrations/schemas.py`

> Currently empty — pending implementation. Will document `RegistrationCreate` and `RegistrationOut` schemas once built.

---

## `app/core/schemas.py`

Shared cross-domain schemas, including authentication request/response models.

### `LoginRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | `str` \| `null` | ❌ | Organiser email address (either `email` or `username` accepted) |
| `username` | `str` \| `null` | ❌ | Alias for organiser email for OAuth compatibility |
| `password` | `str` | ✅ | Organiser plaintext password |

### `TokenResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_token` | `str` | ✅ | Bearer JWT token |
| `token_type` | `str` | ✅ | Token type (defaults to `"bearer"`) |

---

## Enum Reference

These enums are defined in their respective `models.py` files and imported into `schemas.py`.

| Enum | Values | Defined in |
|------|--------|------------|
| `AttendanceStatus` | `not_checked_in`, `checked_in` | `app/attendance/models.py` |
| `CheckinMethod` | `qr`, `manual` | `app/attendance/models.py` |
| `EventType` | `workshop`, `seminar`, `hackathon`, `tech_event`, `other` | `app/events/models.py` |
| `RegistrationStatus` | `registered`, `cancelled` | `app/registrations/models.py` |

---

## ORM Model Style

All models now use the **`Mapped` / `mapped_column` API** (SQLAlchemy 2.x declarative style).
This is required for Pylance / pyright to resolve instance attribute types correctly.
The old `Column(...)` style causes all attributes to appear as `Column[X]` to the type-checker,
which breaks assignment checks and conditional checks in `crud.py` and tests.

| File | ORM style | Status |
|------|-----------|--------|
| `app/attendance/models.py` | `Mapped` / `mapped_column` | ✅ canonical |
| `app/events/models.py` | `Mapped` / `mapped_column` | ✅ migrated |
| `app/registrations/models.py` | `Mapped` / `mapped_column` | ✅ migrated |
| `app/core/models.py` | re-export shim only | ✅ (no columns defined here) |

---

## Router Deduplication

`app/core/router.py` and `app/attendance/router.py` previously both defined overlapping
attendance routes. The canonical router is `app/attendance/router.py`.
`app/core/router.py` is now a one-line re-export shim.

| File | Role |
|------|------|
| `app/attendance/router.py` | **Canonical** — all 5 attendance routes live here |
| `app/core/router.py` | Re-export shim (`from app.attendance.router import router`) |

---

## Datatype Consistency Rules

All the following types must be consistent across `schema.sql`, `models.py`, `schemas.py`, and test fixtures:

| Entity | PK / field type | FK references | SQL type | Notes |
|--------|----------------|---------------|----------|-------|
| `events.id` | `UUID` | — | `UUID` | |
| `registrations.id` | `UUID` | — | `UUID` | |
| `registrations.event_id` | `UUID` | `events.id` | `UUID` | |
| `organisers.id` | `UUID` | — | `UUID` | |
| `attendance.id` | `UUID` | — | `UUID` | |
| `attendance.registration_id` | `UUID` | `registrations.id` | `UUID` | UNIQUE |
| `attendance.event_id` | `UUID` | `events.id` | `UUID` | denormalized |
| `attendance.checked_in_by` | `UUID \| None` | `organisers.id` | `UUID` nullable | |
| `attendance.status` | `AttendanceStatus` | — | `attendance_status` ENUM | |
| `attendance.method` | `CheckinMethod \| None` | — | `checkin_method` ENUM nullable | |
| `attendance.checked_in_at` | `datetime \| None` | — | `TIMESTAMPTZ` nullable | |

> [!WARNING]
> `app/core/models.py` previously defined duplicate `Organiser` and `Attendance` models using `Integer` PKs (wrong). It now re-exports from `app/attendance/models.py` which uses UUID throughout, matching `schema.sql`.

> [!IMPORTANT]
> `app/core/router.py` previously defined duplicate attendance routes including `response_model=BytesIO` (invalid — `BytesIO` is not a Pydantic model and was not imported) and a call to `generate_registration_qr` which was never defined. That file is now a clean re-export shim.
