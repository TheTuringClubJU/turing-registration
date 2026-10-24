# TODO — Attendance, QR & Organiser Check-in

Covers: `attendance/`, organiser-facing scanner UI, `core/security.py`.
Depends on events and registrations existing already (see `todo_events.md`).

**Owners:** Darsh = database + email · Sukrit = backend (QR, attendance, auth) + backend tests · Swapnil = frontend
Each section has an owner. An item tagged `[Name]` overrides its section owner.

---

## Database — Owner: Darsh

- [x] `organisers` table: id, username (unique), password_hash, name, created_at
- [x] `attendance` table: id, registration_id (FK, unique), event_id (FK, denormalized), ticket_code (unique), status (ENUM: not_checked_in / checked_in), method (ENUM: qr / manual, nullable), checked_in_at (nullable), checked_in_by (FK → organisers, nullable), created_at, updated_at
- [x] CHECK constraint: checked_in_at / method / checked_in_by are all NULL or all set together
- [x] Confirm `attendance` row is created in the **same transaction** as the registration insert (status = not_checked_in) — not created lazily on first check-in
- [x] Decide how first organiser account(s) get created — manual insert for now (see Open Decisions)

---

## Backend (FastAPI) — Owner: Sukrit

### `core/`
- [x] `security.py` — organiser login, JWT issue/verify (this is a hard blocker for everything else in this file — build first)
  - [x] password hashing (bcrypt)
  - [x] `POST /auth/login` handler logic
  - [x] dependency for "require valid organiser JWT" used by every attendance route

### `attendance/`
- [x] `models.py` — SQLAlchemy `Attendance` model, mirrors schema above
- [x] `schemas.py` — `CheckinRequest` (registration_id / query), `AttendanceOut` (status, method, checked_in_at, checked_in_by, participant_name, participant_names, team_name, ticket_code), `SummaryOut` (total_registered, checked_in, remaining)
- [x] `qr.py`:
  - [x] `generate_image(registration_id: str) -> bytes` — PNG, encodes raw registration_id or ticket_code, no signing
  - [x] no disk/DB storage of the image — always generated on demand from the ID already in the DB
- [x] `crud.py`:
  - [x] `mark_attended(identifier, method, organiser_id)` — single entrypoint used by both scan and manual routes
  - [x] idempotent: if already checked_in, return existing record instead of erroring (duplicate scans are normal, not failures)
  - [x] 404 if identifier doesn't resolve to an attendance row
  - [x] `get_summary(event_id)` — counts for dashboard
  - [x] `get_list(event_id)` — all registrations + attendance status + participant names, joined once, for the dashboard table
- [x] `router.py`:
  - [x] `POST /attendance/scan` — organiser-auth required, method = qr
  - [x] `POST /attendance/manual-checkin` — organiser-auth required, method = manual
  - [x] `GET /attendance/summary?event_id=`
  - [x] `GET /attendance/list?event_id=`
  - [x] `GET /registrations/{id}/qr` — regenerates and returns PNG on demand

---

## Frontend — Owner: Swapnil

- [x] `OrganiserLogin` — standalone page/modal with handle + password, stores JWT in localStorage
- [x] `AttendanceDashboard` — protected view, pulls data via token
  - [x] live summary counts (registered / checked-in / remaining)
  - [x] mobile-responsive attendee cards with real participant and team names
  - [x] 1.5s visual feedback animation (green checkmark for admitted, red cross for rejected)
- [x] `QRScanner` — camera-based scanning using `html5-qrcode`
  - [x] requests rear camera (`facingMode: environment`) with camera list fallback
  - [x] on successful decode → `POST /attendance/scan`
- [x] `ManualCheckinInput` — short ticket code or UUID manual entry → `POST /attendance/manual-checkin`
- [x] `ResultDisplay` — monochrome check-in status card

---

## Tests (`tests/attendance/`) — Owner: Sukrit

- [x] `test_attendance_row_lifecycle.py` — row created in same transaction as registration, defaults not_checked_in, event_id matches registration's event_id, registration_id unique constraint enforced
- [x] `test_checkin.py` — scan marks checked_in with method=qr, manual marks with method=manual, duplicate check-in is idempotent, invalid registration_id → 404, requires organiser auth → 401 without token, checked_in_by records correct organiser
- [x] `test_dashboard.py` — summary counts correct (total/checked-in/remaining), list returns all registrations with correct status, list scoped to single event_id
- [x] `test_qr.py` — image generated on successful registration, encodes exact registration_id string, regeneration endpoint returns valid PNG, QR generation failure does not fail the registration itself
- [x] `test_auth.py` — valid login returns JWT, invalid credentials rejected, expired/missing token rejected on protected routes
- [x] GitHub Actions: full CI pipeline with backend PostgreSQL matrix tests and Node 22 Vitest frontend component tests

---

## Open Decisions (need sign-off) — Owner: Darsh

- [x] Organiser account creation: manual DB insert for the first few organisers
- [x] Per-event organiser scoping is NOT in this phase — every organiser can check in for every event
- [x] `GET /registrations/{id}/qr` is unauthenticated (relies on registration_id being hard to guess)
- [x] Short 6-character ticket codes (`TTC-XXXX`) implemented to replace entering 36-char UUIDs
