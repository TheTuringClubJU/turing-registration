"""
app/tests/conftest.py

Shared pytest fixtures for the whole test suite. Every domain's tests
(events, registrations, attendance) use the `db_session` fixture from here
rather than creating their own DB connection.

Expects DATABASE_URL (set via CI's Postgres service container, or a local
test database) to point at a database where schema.sql has already been run.
This fixture does NOT create tables — it assumes schema.sql is the source
of truth and has already been applied, then wraps each test in a transaction
that's rolled back afterward so tests never leave data behind.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

test_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="function")
def db_session():
    """
    Yields a DB session wrapped in a transaction that's rolled back after
    the test finishes — so every test starts from a clean slate and never
    leaves rows behind for the next test, without needing to manually
    delete anything.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()