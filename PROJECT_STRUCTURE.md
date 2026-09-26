# Project Structure

This document explains **why** each folder exists and **what belongs inside it**. Read this before adding a new file — if you're unsure where something goes, check here first instead of guessing.

---

## Top-level layout

```
turing-registration/
├── .github/
├── app/
├── frontend/
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CONTRIBUTING.md
└── CONTRIBUTORS.md
```

- **`app/`** — the FastAPI backend. Everything that runs on the server.
- **`frontend/`** — the React/Vite frontend. Everything that runs in the browser.
- Everything else at the root is project-level config/docs, not code.

These two are kept as siblings, not nested inside each other, because they're deployed separately (backend on Render, frontend on Vercel) and have completely different dependency ecosystems (Python vs JS). Mixing them into one folder would make it unclear which `requirements.txt`/`package.json` applies to what.

---

## `.github/`

GitHub-specific config — none of this is application code, it configures how the *repository* behaves.

| File | Purpose |
|---|---|
| `ISSUE_TEMPLATE/bug_report.md` | Template shown when someone opens a bug issue — keeps bug reports consistent |
| `ISSUE_TEMPLATE/feature_task.md` | Template for a new feature/task issue |
| `ISSUE_TEMPLATE/config.yml` | Controls the issue-template picker (e.g. disables blank issues) |
| `workflows/ci.yml` | The CI/CD pipeline — runs pytest on every PR against a throwaway Postgres |
| `CODEOWNERS` | Maps folders to people who must review PRs touching them (e.g. `attendance/` → attendance lead) |
| `PULL_REQUEST_TEMPLATE.md` | Auto-fills every new PR description with a consistent checklist |

**Why it's a hidden top-level folder and not inside `app/`:** it's not part of the running application — it only matters to GitHub's UI and Actions runner, so it lives at the repo root where GitHub expects it.

---

## `app/` — the backend

### `app/main.py`
The single entrypoint. Creates the FastAPI app instance and mounts every domain's router (`events`, `registrations`, `attendance`). Should stay thin — no business logic here, just wiring.

### `app/core/`
Shared infrastructure every domain depends on. Nothing here is specific to events, registrations, or attendance — if a file only matters to one domain, it does **not** belong here.

| File | Purpose |
|---|---|
| `config.py` | Reads environment variables (`DATABASE_URL`, `BREVO_API_KEY`, `JWT_SECRET`) into typed settings. The only place `os.environ` should be touched. |
| `database.py` | SQLAlchemy engine + session setup, shared connection to Neon. Every domain's `crud.py` imports the session from here. |
| `security.py` | Organiser login + JWT issue/verify. Shared because `attendance` routes need it, and potentially other admin routes later. |

### `app/events/`, `app/registrations/`, `app/attendance/` — domain folders

These three are **siblings**, not nested inside each other, even though registrations belong to events and attendance belongs to registrations at the database level. That's a foreign-key relationship, not a folder-ownership relationship — see the rationale below.

Each domain folder follows the exact same internal shape, so once you understand one, you understand all three:

| File | Purpose |
|---|---|
| `models.py` | SQLAlchemy model(s) for this domain's table(s). Mirrors `schema.sql` exactly — if they drift, `schema.sql` is source of truth. |
| `schemas.py` | Pydantic request/response shapes (e.g. `EventOut`, `RegistrationCreate`). What the API actually sends/receives — never expose a raw SQLAlchemy model directly. |
| `crud.py` | All database queries/writes for this domain, separated from route handlers so they're testable without spinning up HTTP. |
| `router.py` | The actual FastAPI endpoints. Should mostly call into `crud.py` — keep routing thin, keep logic in `crud`/`validators`. |
| `validators.py` *(registrations only)* | Pure functions with no DB access — team size rules, team_name rules, lead rules. Separated from `crud.py` because these are easy to unit-test in isolation without touching the database. |
| `qr.py` *(attendance only)* | QR generation, nested here because nothing outside attendance ever needs it — not a shared `core/` utility. |

**Why registrations/attendance aren't nested inside `events/`:** folder nesting should mirror *code ownership* (which team/PR owns this set of files), not *foreign key chains*. If it mirrored FKs, you'd end up with `events/registrations/attendance/`, three folders deep, and every import would have to route through someone else's parent folder. Flat siblings mean any domain can cleanly import any other (e.g. `attendance/crud.py` importing `Registration` from `registrations/models.py`) without reaching up and back down through an unrelated folder.

### `app/email_templates/`
One file for now: `send.py`, holding a single hardcoded `send_registration_confirmation()` function that calls the Brevo API. Kept as its own folder (not inside `registrations/`) because it's a distinct concern — content/delivery, not registration validation — and it'll grow (certificate emails, later a template editor) independently of the registration logic that triggers it.

### `app/tests/`
Mirrors the domain folder structure exactly — `tests/events/`, `tests/registrations/`, `tests/attendance/`, plus `tests/email/`. If you add a new file to `app/registrations/`, its test belongs in `app/tests/registrations/`, not scattered elsewhere. `conftest.py` holds shared pytest fixtures (test DB session, test client) used across all test files.

---

## `frontend/`

### `frontend/src/registration/`
Everything a **registrant** (the person filling out the form) sees. One dynamic form component, not one component per event — it renders based on whatever `GET /events/active` returns.

| File | Purpose |
|---|---|
| `RegistrationForm.jsx` | The form itself — fetches active event, renders participant blocks dynamically |
| `SubmissionHandler.js` | Builds the POST payload, calls the register endpoint |
| `ErrorDisplay.jsx` | Renders field-level 422 errors inline |
| `ConfirmationScreen.jsx` | Shown after a successful submit |

### `frontend/src/attendance/`
Everything an **organiser** (staff checking people in) sees — a separate, login-gated part of the frontend.

| File | Purpose |
|---|---|
| `OrganiserLogin.jsx` | Email/password login, stores the JWT |
| `AttendanceDashboard.jsx` | The main protected screen — composes the scanner, manual input, and live counts |
| `QRScanner.jsx` | Camera-based scanning via `html5-qrcode` |
| `ManualCheckinInput.jsx` | Plain text fallback input for a registration ID |
| `ResultDisplay.jsx` | Shared success/error/already-checked-in feedback — used by **both** the scanner and manual input, since they hit the same backend logic and should look the same to the organiser |

**Why registration and attendance are separate folders inside `frontend/src/`:** one is public-facing (anyone can open it), the other is behind organiser login — keeping them visually and structurally separate makes it obvious at a glance which code is exposed to the public internet and which requires auth.

---

## Root-level files

| File | Purpose |
|---|---|
| `schema.sql` | Source of truth for the database. Run this to create every table — `models.py` files across the app should always match what's here. |
| `requirements.txt` | Python dependencies for `app/`. Lives at root (not inside `app/`) because `pip install -r requirements.txt` and Render's auto-deploy both expect it there by convention. |
| `.env.example` | Template showing which environment variables are needed (`DATABASE_URL`, `BREVO_API_KEY`, `JWT_SECRET`), with fake placeholder values. Safe to commit — the real `.env` never is. |
| `.gitignore` | Excludes `.env`, `__pycache__/`, `node_modules/`, and other machine-specific/secret files from being committed. |
| `README.md` | What this project is, how to run it locally. |
| `CONTRIBUTING.md` | Branch naming, PR process, commit conventions. |
| `CONTRIBUTORS.md` | Who's worked on this. |

---

## Quick rule of thumb when adding a new file

1. **Does it talk to the database for one specific domain?** → that domain's `crud.py`
2. **Does it define what an API request/response looks like?** → that domain's `schemas.py`
3. **Is it a pure validation rule with no DB access?** → `registrations/validators.py` (or a new `validators.py` if another domain needs one)
4. **Is it shared by every domain (DB connection, auth, config)?** → `core/`
5. **Does only one domain ever use it?** → nested inside that domain's folder (like `attendance/qr.py`), not `core/`
6. **Is it browser-facing UI?** → `frontend/src/`, split into `registration/` or `attendance/` depending on who sees it