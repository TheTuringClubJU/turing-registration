"""
app/tests/test_health.py

Smoke test — confirms the FastAPI app boots and the /health endpoint
reports a working DB connection. This is the one test that covers
app/main.py as it currently stands.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok_and_connected():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"