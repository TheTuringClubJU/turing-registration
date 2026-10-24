"""Real SQL integration with the existing login, QR and attendance routes."""
from datetime import datetime, timedelta, timezone


def test_login_register_qr_and_checkin(client, organiser, monkeypatch):
    from app.email_templates import send
    from unittest.mock import Mock

    # External delivery is mocked; login, event/registration SQL, QR generation,
    # attendance creation and check-in all use the real application code.
    deliver = Mock()
    monkeypatch.setattr(send, "send_registration_confirmation", deliver, raising=False)
    denied = client.post("/auth/login", json={"username": organiser.username, "password": "wrong"})
    assert denied.status_code == 401
    login = client.post("/auth/login", json={"username": organiser.username, "password": "test-login-password"})
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    now = datetime.now(timezone.utc)
    event_payload = {"slug": "integrated-event", "name": "Integrated Event", "type": "workshop",
                     "min_team_size": 1, "max_team_size": 1, "is_active": True,
                     "reg_open_at": (now - timedelta(hours=1)).isoformat()}
    assert client.post("/events", json=event_payload).status_code == 401
    event = client.post("/events", json=event_payload, headers=headers)
    assert event.status_code == 201, event.text
    registered = client.post("/events/integrated-event/register", json={"participants": [
        {"name": "Integration Tester", "email": "integration@example.com", "phone": "+919876543210"}
    ]})
    assert registered.status_code == 201, registered.text
    identifier = registered.json()["id"]
    deliver.assert_called_once()
    assert deliver.call_args.kwargs["registration_id"] == identifier
    assert deliver.call_args.kwargs["qr_bytes"].startswith(b"\x89PNG\r\n\x1a\n")
    qr = client.get(f"/attendance/registrations/{identifier}/qr")
    assert qr.status_code == 200
    assert qr.content == deliver.call_args.kwargs["qr_bytes"]
    assert client.post("/attendance/scan", json={"registration_id": identifier}).status_code == 401
    scanned = client.post("/attendance/scan", json={"registration_id": identifier}, headers=headers)
    assert scanned.status_code == 200, scanned.text
    assert scanned.json()["status"] == "checked_in"
    assert scanned.json()["checked_in_by"] == str(organiser.id)
    summary = client.get("/attendance/summary", params={"event_id": event.json()["id"]}, headers=headers)
    assert summary.status_code == 200
    assert summary.json() == {"total_registered": 1, "checked_in": 1, "remaining": 0}
