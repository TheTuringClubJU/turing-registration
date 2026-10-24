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
    # Application CRUD calls commit/rollback itself. SAVEPOINTs keep those
    # boundaries inside the test's outer transaction, including error paths.
    session = TestSessionLocal(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture(name="test_engine")
def committed_test_engine():
    """Independent connections are only allowed in the disposable CI service."""
    import os
    from sqlalchemy.engine import make_url

    url = make_url(settings.DATABASE_URL)
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or url.host not in {"localhost", "127.0.0.1"}
            or url.database != "turing_registration_test"):
        pytest.skip("Committed concurrency checks require the isolated GitHub Actions database")
    return test_engine


@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient
    from app.core.database import get_db
    from app.main import app

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides = previous


@pytest.fixture
def offline_client(monkeypatch):
    from fastapi.testclient import TestClient
    from app.core.database import engine, get_db
    from app.main import app

    def denied(*args, **kwargs):
        raise AssertionError("Offline contract test attempted a database connection")

    monkeypatch.setattr(engine, "connect", denied)
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: None
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides = previous


@pytest.fixture
def organiser(db_session):
    from app.attendance.models import Organiser
    from app.core.security import hash_password

    organiser = Organiser(username="events-test@ttc", name="Test Organiser",
                          password_hash=hash_password("test-login-password"))
    db_session.add(organiser)
    db_session.flush()
    return organiser
