# Attendance & QR Check-in System

This document provides complete technical, architecture, and operational documentation for the **Attendance, QR Scanner, and Organiser Check-in** subsystem in `turing-registration`.

---

## 1. System Overview

The Attendance subsystem handles event day operations for The Turing Club JU:
- **Organiser Authentication**: Role-based access for club leads using unique handles (`@ttc`) and stateless JWTs.
- **Short Ticket Codes**: Human-readable 6-character ticket identifiers (e.g. `TTC-1852`) alongside raw UUIDs for rapid manual check-in without mobile keyboard friction.
- **QR Code Verification**: High-density QR generation and live browser-based camera scanning using `html5-qrcode` with environment camera fallback.
- **Real-Time Visual Feedback**: Fullscreen 1.5-second auto-dismissing visual confirmation (animated green circle checkmark for `ADMITTED`, red circle cross for `REJECTED`).
- **Idempotent Admittance**: Duplicate check-in attempts return the existing attendance record with `status="checked_in"` without raising HTTP errors or overwriting the original check-in timestamp.
- **Dynamic Active Event Detection**: The dashboard automatically queries and binds to the active event (`is_active = TRUE`) in PostgreSQL, with client-side persistence in `localStorage`.

---

## 2. Architecture & Data Flow

```
                      ┌──────────────────────────────────────────────┐
                      │              Attendee Badge                  │
                      │   (QR Code: "TTC-1852" or Registration UUID) │
                      └──────────────────────┬───────────────────────┘
                                             │
                       Camera Scan           │ Manual Short Code
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │       Organiser Check-in Dashboard           │
                      │  (https://turing-registration.vercel.app)    │
                      └──────────────────────┬───────────────────────┘
                                             │
                        Bearer JWT + POST    │
                        /attendance/scan     │ /attendance/manual-checkin
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │            FastAPI Backend                   │
                      │  (https://turing-registration-api.onrender)  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             │ Read / Update Attendance
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          Neon PostgreSQL Database            │
                      │  tables: events, registrations, attendance,  │
                      │          organisers                          │
                      └──────────────────────────────────────────────┘
```

---

## 3. Database Schema

### `organisers` Table
Stores accredited club leads authorised to admit attendees at event doors.
```sql
CREATE TABLE organisers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `registrations` Table (Ticket Code Column)
```sql
CREATE TABLE registrations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(id),
    ticket_code     VARCHAR(16) UNIQUE,
    team_name       VARCHAR(200),
    p1_name         VARCHAR(200) NOT NULL,
    p1_email        VARCHAR(320) NOT NULL,
    p1_phone        VARCHAR(20)  NOT NULL,
    p1_is_lead      BOOLEAN NOT NULL DEFAULT TRUE,
    p2_name         VARCHAR(200),
    p2_email        VARCHAR(320),
    p2_phone        VARCHAR(20),
    p2_is_lead      BOOLEAN NOT NULL DEFAULT FALSE,
    ...
    status          registration_status NOT NULL DEFAULT 'registered',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `attendance` Table
Created in the same transaction as the registration record (`status='not_checked_in'`).
```sql
CREATE TABLE attendance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id UUID UNIQUE NOT NULL REFERENCES registrations(id),
    event_id        UUID NOT NULL REFERENCES events(id),
    ticket_code     VARCHAR(16) UNIQUE,

    status          attendance_status NOT NULL DEFAULT 'not_checked_in',
    method          checkin_method,          -- 'qr' | 'manual'
    checked_in_at   TIMESTAMPTZ,
    checked_in_by   UUID REFERENCES organisers(id),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT checkin_fields_consistent CHECK (
        (method IS NULL AND checked_in_at IS NULL AND checked_in_by IS NULL)
        OR
        (method IS NOT NULL AND checked_in_at IS NOT NULL AND checked_in_by IS NOT NULL)
    )
);
```

---

## 4. API Endpoints Reference

All write endpoints require a Bearer JWT passed via `Authorization: Bearer <token>`.

### Authentication
* **`POST /auth/login`**:
  - Request: `{"username": "techlead@ttc", "password": "..."}`
  - Response (200): `{"access_token": "ey...", "token_type": "bearer"}`
  - Handles case-insensitivity (`func.lower(username)`) and input trimming.

### Active Event Detection
* **`GET /attendance/active-event`** [Auth Required]:
  - Returns the single currently active event in the database (`is_active = TRUE`).
  - Response (200):
    ```json
    {
      "id": "e4936c05-f7d9-43f9-a7d1-8bbac234b8ca",
      "name": "Turing Club Live Workshop 2026",
      "event_code": "WORKSHOP-8522C0",
      "type": "workshop"
    }
    ```

### Check-in Operations
* **`POST /attendance/scan`** [Auth Required]:
  - Accepts raw UUID string or short ticket code (`TTC-XXXX`) scanned by camera.
  - Payload: `{"registration_id": "TTC-1852"}` (also accepts `{"query": "..."}`)
  - Marks `method="qr"`.
* **`POST /attendance/manual-checkin`** [Auth Required]:
  - Accepts short ticket code or UUID entered manually.
  - Marks `method="manual"`.
* **Response Model (`AttendanceOut`)**:
  ```json
  {
    "registration_id": "e1774edc-920e-47d3-ad3f-819b0d598bf1",
    "ticket_code": "TTC-1852",
    "participant_name": "Aarav Sharma",
    "participant_names": ["Aarav Sharma"],
    "team_name": null,
    "status": "checked_in",
    "method": "manual",
    "checked_in_at": "2026-10-24T12:00:00Z",
    "checked_in_by": "86dd9191-7fde-4381-a8b6-3f3bf1fd98a6"
  }
  ```

### Dashboard Aggregations
* **`GET /attendance/summary?event_id=<uuid>`** [Auth Required]:
  - Returns `{ "total_registered": 10, "checked_in": 3, "remaining": 7 }`.
* **`GET /attendance/list?event_id=<uuid>`** [Auth Required]:
  - Returns array of all attendees with participant names, team name, ticket code, and check-in timestamp.
* **`GET /attendance/registrations/{id}/qr`**:
  - Dynamically renders and streams raw PNG bytes without filesystem or DB image bloat.

---

## 5. Frontend Check-in Interface (`frontend/src/attendance/`)

Styled with a strict Apple-inspired minimalist monochrome theme (`#000000`, white, `#161617`, titanium `#242426` borders).

### Key Components
1. **`OrganiserLogin.jsx`**:
   - Organiser handle input with `@ttc` placeholder.
   - Password field with show/hide toggle.
   - Stores JWT in `localStorage.getItem("organiser_token")`.
2. **`AttendanceDashboard.jsx`**:
   - Auto-fetches active event on mount (`GET /attendance/active-event`).
   - Remembers selected event across refreshes via `localStorage.getItem("active_event_id")`.
   - Real-time segmented filter tabs: All, Admitted, and Pending with counter badges.
   - Attendee cards displaying real attendee names (lead + members: `Diya Nair • Vikram Seth`), team pills, and short ticket codes.
3. **`CheckinAnimation.jsx`**:
   - 1.5-second fullscreen visual feedback overlay.
   - Admitted: Glowing green circle with checkmark (`✓`), "ADMITTED", and attendee name.
   - Rejected: Glowing red circle with cross (`✕`), "NOT ADMITTED", and error reason.
4. **`QRScanner.jsx`**:
   - Camera scanner powered by `html5-qrcode`.
   - Selects environment camera with automatic fallback to available device cameras.
5. **`ManualCheckinInput.jsx`**:
   - Input field auto-uppercasing short codes with `16px` font to prevent mobile Safari auto-zoom.

---

## 6. Testing & CI Pipeline

### Backend Suite (`pytest`)
- 34 passing tests across:
  - `test_attendance_row_lifecycle.py`: DB transaction atomicity and default status.
  - `test_auth.py`: JWT generation, hash verification, role handles.
  - `test_checkin.py`: QR/manual check-in, idempotency, organiser attribution.
  - `test_dashboard.py`: Summary counts, attendee list filtering.
  - `test_qr.py`: PNG byte stream generation.
  - `test_schema_constraints.py`: Database integrity constraints.

### Frontend Suite (`vitest`)
- 11 passing component tests across:
  - `AttendanceDashboard.test.jsx`
  - `ManualCheckinInput.test.jsx`
  - `OrganiserLogin.test.jsx`
  - `ResultDisplay.test.jsx`

### GitHub Actions CI (`.github/workflows/ci.yml`)
- **`backend-test`**: Matrix job with live PostgreSQL 16 container service running `pytest` with coverage.
- **`frontend-test`**: Node.js 22 LTS environment running `npm test` (Vitest) and `npm run build` (Vite production verification).
