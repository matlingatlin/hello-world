from fastapi.testclient import TestClient

from scio_engine.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_validate_full_spec_is_buildable():
    res = client.post(
        "/intake/validate",
        json={
            "purpose": {"value": "Guests book a table."},
            "users_and_roles": {"value": ["guests"]},
            "entities": {"value": ["bookings", "tables"]},
            "key_actions": {"value": ["book", "cancel"]},
            "sign_in": {"value": "email link"},
            "data_ownership_sensitivity": {"value": {"owner": "you", "sensitive": False}},
            "non_goals": {"value": []},
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["result"]["buildable"] is True
    assert body["still_needed"] == []


def test_validate_partial_spec_reports_whats_needed():
    res = client.post(
        "/intake/validate",
        json={
            "purpose": {"value": "Guests book a table."},
            "users_and_roles": {"value": ["guests", "staff"]},
            "signals": {"charges_money": True},
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["result"]["buildable"] is False
    assert set(body["result"]["missing_core"]) == {
        "entities",
        "key_actions",
        "sign_in",
        "data_ownership_sensitivity",
    }
    assert set(body["result"]["unresolved_conditionals"]) == {"role_permissions", "payment"}
    assert set(body["triggered"]) == {"role_permissions", "payment"}
    assert set(body["still_needed"]) >= {"entities", "role_permissions", "payment"}


def test_validate_rejects_malformed_bodies():
    res = client.post("/intake/validate", json={"purpose": {"value": 42}})
    assert res.status_code == 422
