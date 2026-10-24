-- Patch to migrate `organisers` table from email to username
-- Run this migration against your Postgres / Neon database:

ALTER TABLE organisers RENAME COLUMN email TO username;

-- Optional: ensure length constraint matches new username schema
ALTER TABLE organisers ALTER COLUMN username TYPE VARCHAR(100);
