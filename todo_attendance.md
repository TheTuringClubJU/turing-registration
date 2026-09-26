# TODO — Attendance, QR & Organiser Check-in

Covers: `attendance/`, organiser-facing scanner UI, `core/security.py`. Depends on `events` and `registrations` existing already (see `todo_events.md`).

---

## Database

- [ ] `organisers` table: id, email (unique), password_hash, name, created_at
- [ ] `attendance` table: id, registration_id (FK, unique), event_id (FK, denormalized), status (ENUM: not_checked_in / checked_in), method (ENUM: qr / manual, nullable), checked_in_at (nullable), checked_in_by (FK → organisers, nullable), created_at, updated_at
- [ ] CHECK constraint: checked_in_at / method / checked_in_by are all NULL or all set together
- [ ] Confirm `attendance` row is created in the **same transaction** as the registration insert (status = not_checked_in) — not created lazily on first check-in
- [ ] Decide how first organiser account(s) get created — manual insert for now (see Open Decisions)

---

## Backend (FastAPI)

### `core/`
- [ ] `security.py` — organiser login, JWT issue/verify (this is a hard blocker for everything else in this file — build first)
  - [ ] password hashing (passlib/bcrypt)
  - [ ] `POST /auth/login` handler logic
  - [ ] dependency for "require valid organiser JWT" used by every attendance route

### `attendance/`
- [ ] `models.py` — SQLAlchemy `Attendance` model, mirrors schema above
- [ ] `schemas.py` — `CheckinRequest` (registration_id), `AttendanceOut` (status, method, checked_in_at, checked_in_by), `SummaryOut` (total_registered, checked_in, remaining)
- [ ] `qr.py`:
  - [ ] `generate_image(registration_id: str) -> bytes` — PNG, encodes raw registration_id, no signing
  - [ ] no disk/DB storage of the image — always generated on demand from the ID already in the DB
- [ ] `crud.py`:
  - [ ] `mark_attended(registration_id, method, organiser_id)` — single entrypoint used by both scan and manual routes
  - [ ] idempotent: if already checked_in, return existing record instead of erroring (duplicate scans are normal, not failures)
  - [ ] 404 if registration_id doesn't resolve to an attendance row
  - [ ] `get_summary(event_id)` — counts for dashboard
  - [ ] `get_list(event_id)` — all registrations + attendance status, joined once, for the dashboard table
- [ ] `router.py`:
  - [ ] `POST /attendance/scan` — organiser-auth required, method = qr
  - [ ] `POST /attendance/manual-checkin` — organiser-auth required, method = manual
  - [ ] `GET /attendance/summary?event_id=`
  - [ ] `GET /attendance/list?event_id=`
  - [ ] `GET /registrations/{id}/qr` — regenerates and returns PNG on demand (no auth for now — see Open Decisions)

### Certificates (separate send, reuses this data — build after attendance is working)
- [ ] Small standalone script/admin endpoint: query all `attendance` rows with status = checked_in for an event
- [ ] Sequential send with rate-limit delay (Brevo free tier: 300/day cap)
- [ ] Track `certificate_sent` boolean + `sent_at` per registration so a partial run is safely resumable
- [ ] Do **not** run this inside a single request/response cycle — 200 sequential sends will exceed typical timeouts

---

## Frontend

Two things here: the organiser-only dashboard/scanner, and the QR image already embedded in the registration email (built in `todo_events.md` — nothing new needed on the registrant-facing side).

- [ ] `OrganiserLogin` — simple email/password form, stores JWT (memory or localStorage)
- [ ] `AttendanceDashboard` — protected route (redirects to login if no valid JWT)
  - [ ] live summary counts (registered / checked-in / remaining) — `GET /attendance/summary`
  - [ ] table view of all registrations + status — `GET /attendance/list`
- [ ] `QRScanner` — camera-based scanning using `html5-qrcode`
  - [ ] requests rear camera (`facingMode: environment`)
  - [ ] on successful decode → `POST /attendance/scan`
  - [ ] shows clear success/already-checked-in/error states after each scan
- [ ] `ManualCheckinInput` — plain text field, organiser types/pastes registration_id → `POST /attendance/manual-checkin`
  - [ ] same success/error states as scanner, shares one result-display component with `QRScanner`

Keep this to about 5 files — login, dashboard (which composes scanner + manual input + summary + table), scanner, manual input, and one shared result/status display. Don't split scanner and manual-input result handling into separate components — they should render through the same one since they hit the same backend logic.

---

## Tests (`tests/attendance/`)

- [ ] `test_attendance_row_lifecycle.py` — row created in same transaction as registration, defaults not_checked_in, event_id matches registration's event_id, registration_id unique constraint enforced
- [ ] `test_checkin.py` — scan marks checked_in with method=qr, manual marks with method=manual, duplicate check-in is idempotent, invalid registration_id → 404, requires organiser auth → 401 without token, checked_in_by records correct organiser
- [ ] `test_dashboard.py` — summary counts correct (total/checked-in/remaining), list returns all registrations with correct status, list scoped to single event_id
- [ ] `test_qr.py` — image generated on successful registration, encodes exact registration_id string, regeneration endpoint returns valid PNG, QR generation failure does not fail the registration itself
- [ ] `test_auth.py` — valid login returns JWT, invalid credentials rejected, expired/missing token rejected on protected routes
- [ ] GitHub Actions: same CI wiring as events/registrations — ephemeral/branched Postgres, block merge on failure or coverage drop

---

## Open Decisions (need sign-off)

- [ ] Organiser account creation: manual DB insert for the first few organisers vs a minimal signup/invite flow
- [ ] Per-event organiser scoping is NOT in this phase — every organiser can check in for every event. Confirm acceptable.
- [ ] `GET /registrations/{id}/qr` is currently unauthenticated (relies on registration_id being hard to guess). Confirm acceptable, or add a lightweight gate (e.g. also require the registrant's email).
- [ ] Certificate send mechanism: standalone script run manually vs a protected admin endpoint triggered from the dashboard — pick one before building
