# TODO — Events, Registrations & Email

Covers: `events/`, `registrations/`, `email_templates/`, `core/`. Attendance/QR/organiser-scan is tracked separately in `todo_attendance.md`.

---

## Database

- [ ] Write `schema.sql` — source of truth, run manually to create tables
- [ ] `events` table: id, event_code, slug, name, type (ENUM), min_team_size, max_team_size, is_active, reg_open_at, reg_close_at, created_at, updated_at
- [ ] `registrations` table: id, event_id (FK), team_name, p1–p4 name/email/phone slots, status (ENUM), created_at, updated_at
- [ ] CHECK constraint: min_team_size ≤ max_team_size, both ≥ 1
- [ ] Partial unique index: only one `events` row can have is_active = TRUE
- [ ] CHECK constraint: reg_close_at > reg_open_at when set
- [ ] Confirm Neon project created, connection string in hand (not committed anywhere)
- [ ] Set up a Neon branch for CI (or confirm local Postgres container fallback — see Open Decisions)

---

## Backend (FastAPI)

### `core/`
- [ ] `config.py` — env vars: DB URL, Brevo API key, JWT secret, CORS allowed origins
- [ ] `database.py` — SQLAlchemy engine + session, shared by every domain
- [ ] `security.py` — organiser JWT auth (needed for attendance later, but scaffold now so both modules share it)

### `events/`
- [ ] `models.py` — SQLAlchemy `Event` model, mirrors schema.sql exactly
- [ ] `schemas.py` — `EventOut` (id, code, slug, name, type, min/max team size, reg_open bool), `EventCreate` (for the internal POST endpoint, fast-follow)
- [ ] `crud.py` — `get_active_event()`, `get_event_by_slug()`, `create_event()` (fast-follow)
- [ ] `router.py` — `GET /events/active`, `GET /events/{slug}`, `POST /events` (fast-follow, admin-only later)

### `registrations/`
- [ ] `models.py` — SQLAlchemy `Registration` model, p1–p4 slot columns
- [ ] `schemas.py` — `RegistrationCreate` (team_name optional, participants list), `RegistrationOut` (id, status, created_at)
- [ ] `validators.py` — pure functions, no DB access:
  - [ ] participant count within [min_team_size, max_team_size]
  - [ ] team_name required/blank rules based on max_team_size
  - [ ] exactly one `is_team_lead = true` for team events; forced true for solo
  - [ ] email/phone format checks
  - [ ] no duplicate email within a single submission
- [ ] `crud.py`:
  - [ ] `create_registration()` — single DB transaction, no partial writes
  - [ ] duplicate-email check across p1–p4 for the same event_id
  - [ ] calls `qr` generation (from `attendance/qr.py`) after commit — see integration note below
  - [ ] fires `email_templates.send_registration_confirmation()` via `BackgroundTasks`
- [ ] `router.py` — `POST /events/{slug}/register`
  - [ ] rejects if reg_open is false / reg_close_at passed / event not active (pending Open Decision)
  - [ ] returns structured 422 with field-level errors on validation failure

### `email_templates/`
- [ ] `send.py` — `send_registration_confirmation(to, event, team_name, participants, qr_bytes, registration_id)`
  - [ ] one hardcoded HTML template (not a general editor — that's a later phase)
  - [ ] QR image embedded inline at the bottom of the email body (`cid:` reference), not as a PDF
  - [ ] raw registration_id printed as plain text below the QR (fallback-fallback)
  - [ ] sent via Brevo transactional email API
- [ ] Confirm Brevo account created, sender domain verified, API key stored as env var only

---

## Frontend

One dynamic form component — no per-event pages, no hardcoding.

- [ ] `RegistrationForm` component
  - [ ] on load: `GET /events/active` → drives all rendering
  - [ ] "registration closed" state when no event is active (not a broken/empty form)
  - [ ] renders exactly `max_team_size` participant blocks, always fully rendered upfront — no add/remove button
  - [ ] first `min_team_size` blocks required, remainder marked optional
  - [ ] `team_name` field only rendered when `max_team_size > 1`
  - [ ] slot 1 labelled "Team Lead" (team) or "Your Details" (solo)
  - [ ] submit disabled when reg_open is false
  - [ ] client-side validation is UX sugar only — mirrors backend rules but backend is source of truth
- [ ] `SubmissionHandler` — builds payload per spec shape, omits empty optional slots (not null)
- [ ] `ErrorDisplay` — surfaces 422 field-level errors inline per field, not a generic toast
- [ ] `StaleEventNotice` — distinct message when backend hard-rejects a stale tab ("event no longer open, refresh")
- [ ] `ConfirmationScreen` — shown after successful submit (registration_id, "check your email" message)

Keep this to roughly 4–5 files — one form, one submission handler, one error component, one confirmation screen, plus the event-fetch hook. Don't split further than that; don't cram it all into one file either.

---

## Tests (`tests/events/`, `tests/registrations/`)

- [ ] `test_event_config.py` — event code format, sequential codes, concurrent creation race, min≤max enforced, only-one-active enforced, active/slug lookups
- [ ] `test_form_field_shape.py` — response includes min/max team size, solo vs team ranges correct
- [ ] `test_participant_count.py` — solo accepts exactly 1, team accepts min/max/middle, rejects below/above
- [ ] `test_team_name.py` — solo forces null even if client sends one, team rejects missing/blank, accepts valid
- [ ] `test_team_lead.py` — solo forces lead true, team rejects zero/multiple leads
- [ ] `test_duplicates.py` — same event rejected across all slots, within-submission rejected, different event/type allowed
- [ ] `test_data_integrity.py` — invalid email/phone rejected, empty required rejected, empty optional ignored, insert is atomic
- [ ] `test_open_close.py` — rejected when reg_open false, after reg_close_at, if not active (pending decision), succeeds within window
- [ ] `test_api_contract.py` — same contract across solo/team payloads, returns registration_id, field-level error format
- [ ] `test_email.py` — confirmation sent on success (mocked Brevo), includes QR + plain-text ID + participant names, registration still succeeds if email send fails
- [ ] GitHub Actions: run on every PR against ephemeral/branched Postgres, block merge on failure or coverage drop

---

## Open Decisions (need sign-off)

- [ ] Does `is_active = false` (but reg_open still true) block registration, or only reg_open/reg_close_at matter?
- [ ] Event creation: manual SQL insert for first 1–2 events vs minimal `POST /events` endpoint now
- [ ] Phone number format / country restriction — currently unspecified
- [ ] Neon branch-per-PR vs local Postgres container in CI — depends on Neon API key availability as a CI secret
