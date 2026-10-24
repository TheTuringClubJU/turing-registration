# Event registration branch for Darsh's local review

Branch: `feat/event-registerations` (the spelling requested in the handoff).
Based on official main `e1db1a5`. No PR is needed for this branch review.

## Integration

- Shahan's public form is at `/register` in this repository's existing frontend.
  The root login/dashboard route remains intact. Same-origin `/events` requests
  use the existing Vite/hosting proxy pattern.
- Vishad's registration backend and the earlier event API work were ported from
  private branch `fix/events-scope` (`ce634f1`). Only the events/registration code
  and relevant tests were carried over; the combined club website and old CI
  setup were not copied into this service.
- Event creation uses the current organiser authentication dependency and
  `next_event_code()` function. Registration creates its attendance row in the
  same transaction. Confirmation uses the upstream QR generator after commit.
- `schema.sql`, all existing ORM models, auth/QR/attendance code and tests, and
  `.github/workflows/ci.yml` are retained from official main.
- Ordinary SQL tests use the shared connection/outer transaction fixture.
  Added SQLAlchemy savepoints allow CRUD rollback/commit without destroying
  the test setup. Fixture cleanup now also runs when a test fails.

## Testing

The official CI workflow runs on pushes. It provisions PostgreSQL 16, applies
the unchanged `schema.sql`, runs the full backend suite with coverage, and runs
the full frontend suite and build. This branch does not substitute mocked
checks for those real SQL checks or add a different database/schema.

The attendance tests were reviewed as reference: password hashing/token expiry,
QR PNG generation, attendance lifecycle, check-in and dashboard counts, plus
the frontend login/dashboard tests. New integration coverage exercises actual
login, authenticated event creation, public registration, QR generation and
authenticated check-in together. Only email delivery is mocked in that test.
Simultaneous registration requests are tested on independent SQL connections.

Concurrency tests commit data, so the `test_engine` fixture permits them only
on the named localhost database inside GitHub Actions. Ordinary tests roll
back row changes. Rollbacks do not make production testing safe: sequences,
external requests, locks and separately committed connections can have effects.
Use a dedicated test database, never production Neon, for local SQL tests.

Local validation uses dummy settings and blocks SQLAlchemy engine connections:
81 backend tests pass and 68 SQL-dependent tests are deselected for that local
run. All 26 frontend tests and the production build pass. Full SQL validation
is performed by the official branch CI, not that local offline run.

To review locally:

```sh
git fetch origin
git switch --track origin/feat/event-registerations
cd frontend
npm ci
npm test
npm run build
```

Run backend `python -m pytest --cov=app --cov-report=term-missing` only with
`DATABASE_URL` pointing to an approved test database with the current schema.
Keep credentials in ignored `.env`/environment variables.

## Remaining owner decisions

- Darsh's email sender is still a placeholder on main. Registration logs pending
  confirmation when that provider is missing; email delivery is not verified.
- Current main removed the database max-four-team-size constraint while the TODO
  still mentions it. The API rejects sizes over four and the form refuses invalid
  configuration; this branch does not change Darsh's SQL or pretend the DB has
  that constraint. Schema-owner review is needed for manually inserted events.
- The schema counter's three-character `lpad` can truncate numbers beyond 999;
  leave that SQL change to the schema owner.
- Inactive events are rejected, cancelled registrations permit re-registration,
  and phones use international `+` format. These retained policies still need
  owner sign-off as noted in `todo_events.md`.
- Existing nullable ticket-code fields are preserved. New registrations use the
  UUID for QR/manual check-in; no new ticket-code algorithm is introduced.
