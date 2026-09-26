-- ============================================================
-- turing-registration — full schema
-- Run this against a fresh Postgres/Neon database to set up all tables.
-- Source of truth. app/*/models.py must always match this exactly.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- for gen_random_uuid()

-- ------------------------------------------------------------
-- ENUM TYPES
-- ------------------------------------------------------------

CREATE TYPE event_type AS ENUM ('workshop', 'seminar', 'hackathon', 'tech_event', 'other');
CREATE TYPE registration_status AS ENUM ('registered', 'cancelled');
CREATE TYPE attendance_status AS ENUM ('not_checked_in', 'checked_in');
CREATE TYPE checkin_method AS ENUM ('qr', 'manual');

-- ------------------------------------------------------------
-- events
-- ------------------------------------------------------------

CREATE TABLE events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_code      VARCHAR(50) UNIQUE NOT NULL,   -- e.g. WORKSHOP-2026-001
    slug            VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    type            event_type NOT NULL,
    min_team_size   INT NOT NULL CHECK (min_team_size >= 1),
    max_team_size   INT NOT NULL CHECK (max_team_size >= 1),
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    reg_open_at     TIMESTAMPTZ NOT NULL,
    reg_close_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT min_le_max CHECK (min_team_size <= max_team_size),
    CONSTRAINT close_after_open CHECK (reg_close_at IS NULL OR reg_close_at > reg_open_at)
);

-- Only one event can be active at a time — DB-enforced, not just app logic
CREATE UNIQUE INDEX only_one_active_event
    ON events (is_active)
    WHERE is_active = TRUE;

-- ------------------------------------------------------------
-- registrations
-- ------------------------------------------------------------

CREATE TABLE registrations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(id),
    team_name       VARCHAR(200),                  -- NULL forced server-side if max_team_size = 1

    p1_name         VARCHAR(200) NOT NULL,
    p1_email        VARCHAR(320) NOT NULL,
    p1_phone        VARCHAR(20)  NOT NULL,
    p1_is_lead      BOOLEAN NOT NULL DEFAULT TRUE,

    p2_name         VARCHAR(200),
    p2_email        VARCHAR(320),
    p2_phone        VARCHAR(20),
    p2_is_lead      BOOLEAN NOT NULL DEFAULT FALSE,

    p3_name         VARCHAR(200),
    p3_email        VARCHAR(320),
    p3_phone        VARCHAR(20),
    p3_is_lead      BOOLEAN NOT NULL DEFAULT FALSE,

    p4_name         VARCHAR(200),
    p4_email        VARCHAR(320),
    p4_phone        VARCHAR(20),
    p4_is_lead      BOOLEAN NOT NULL DEFAULT FALSE,

    status          registration_status NOT NULL DEFAULT 'registered',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_registrations_event_id ON registrations (event_id);

-- Note: duplicate-email prevention across p1–p4 for the same event_id,
-- and "exactly one is_lead = true", are NOT expressible as a single
-- DB constraint across 4 slot-pairs — enforced in app code (registrations/crud.py + validators.py).

-- ------------------------------------------------------------
-- organisers
-- ------------------------------------------------------------

CREATE TABLE organisers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(320) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- attendance
-- ------------------------------------------------------------

CREATE TABLE attendance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id UUID UNIQUE NOT NULL REFERENCES registrations(id),
    event_id        UUID NOT NULL REFERENCES events(id),  -- denormalized for fast per-event dashboard queries

    status          attendance_status NOT NULL DEFAULT 'not_checked_in',
    method          checkin_method,          -- nullable until checked in
    checked_in_at   TIMESTAMPTZ,             -- nullable until checked in
    checked_in_by   UUID REFERENCES organisers(id),  -- nullable until checked in

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- either all three check-in fields are set, or none are
    CONSTRAINT checkin_fields_consistent CHECK (
        (method IS NULL AND checked_in_at IS NULL AND checked_in_by IS NULL)
        OR
        (method IS NOT NULL AND checked_in_at IS NOT NULL AND checked_in_by IS NOT NULL)
    )
);

CREATE INDEX idx_attendance_event_id ON attendance (event_id);