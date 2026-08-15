from fastapi.testclient import TestClient

from scio_engine.execution.matrix import default_matrix
from scio_engine.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["providers"] in {"fake", "real"}


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


def test_matrix_tasks_lists_ranked_models():
    res = client.get("/matrix/tasks")
    assert res.status_code == 200
    body = res.json()
    assert "codegen" in body
    assert len(body["codegen"]) == 3


def test_generate_plan_returns_models_and_narration():
    res = client.post("/generate/plan", json={"task": "codegen", "prompt": "Build it"})
    assert res.status_code == 200
    body = res.json()
    assert body["passes"] == 4
    assert len(body["models"]) == 3
    assert body["models"][0] in body["narration"]


def test_generate_plan_clamps_passes():
    res = client.post(
        "/generate/plan",
        json={"task": "codegen", "prompt": "x", "options": {"passes": 99}},
    )
    assert res.json()["passes"] == 4


def test_unknown_task_is_a_400():
    res = client.post("/generate", json={"task": "teleportation", "prompt": "x"})
    assert res.status_code == 400
    assert "Unknown task" in res.json()["detail"]


def test_generate_streams_narration_passes_and_result():
    """Full relay over SSE with the fake provider (no keys needed)."""
    with client.stream(
        "POST",
        "/generate",
        json={"task": "codegen", "prompt": "Build a booking form"},
    ) as res:
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/event-stream")
        body = "".join(res.iter_text())

    events = [line[len("event: ") :] for line in body.splitlines() if line.startswith("event: ")]
    assert events == ["narration", "pass", "pass", "pass", "pass", "result"]
    # The matrix is data and its rankings shift; what must hold is that the
    # stream names the model it actually ran.
    assert default_matrix().top_n("codegen")[0].id in body


def test_generate_honours_a_single_pass():
    with client.stream(
        "POST",
        "/generate",
        json={"task": "light_edit", "prompt": "tweak", "options": {"passes": 1}},
    ) as res:
        body = "".join(res.iter_text())
    events = [line[len("event: ") :] for line in body.splitlines() if line.startswith("event: ")]
    assert events == ["narration", "pass", "result"]


def test_generate_reports_budget_errors_as_an_event():
    with client.stream(
        "POST",
        "/generate",
        json={"task": "codegen", "prompt": "x", "options": {"budget_usd": 0.0000001}},
    ) as res:
        body = "".join(res.iter_text())
    assert "event: error" in body
    assert "budget_exceeded" in body


def test_intake_step_asks_the_first_question_on_an_empty_conversation():
    res = client.post(
        "/intake/step",
        json={"messages": [{"role": "user", "text": "I want an app for my restaurant."}]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["buildable"] is False
    assert body["next_question"]["field"]  # something concrete is being asked
    assert body["next_question"]["example"]  # never a bare question
    assert body["updated_spec"]["platform"]["source"] == "default"


def test_intake_step_carries_a_spec_forward():
    res = client.post(
        "/intake/step",
        json={
            "messages": [{"id": "m1", "role": "user", "text": "Guests book a table."}],
            "spec": {"purpose": {"value": "Guests book a table."}},
        },
    )
    assert res.status_code == 200
    body = res.json()
    # The spec that came in is still intact, and the turn moved the wizard on.
    #
    # This used to assert `parsed is False`: without keys the FakeProvider
    # returned a digest, extraction could not read it, and NOTHING was ever
    # recorded — which meant the wizard asked the same question forever and the
    # free path could not reach a build at all. The first local click-through
    # found it (B064); intake now has a stand-in, like the builder always did.
    assert body["updated_spec"]["purpose"]["value"] == "Guests book a table."
    assert body["extraction"]["parsed"] is True
    # It moved on rather than asking about purpose again.
    assert body["next_question"]["field"] != "purpose"
    assert "purpose" not in body["gate"]["missing_core"]


def test_the_keyless_wizard_actually_records_what_was_said():
    """The free path has to be able to finish, or it is a demo that cannot demo."""
    res = client.post(
        "/intake/step",
        json={
            "messages": [
                {"id": "m1", "role": "user", "text": "Guests book a table."},
                {
                    "id": "m2",
                    "role": "assistant",
                    "text": "Who uses it — and is there more than one kind of user?",
                },
                {"id": "m3", "role": "user", "text": "Guests, and staff."},
            ],
            "spec": {"purpose": {"value": "Guests book a table."}},
        },
    )

    body = res.json()
    recorded = body["updated_spec"]["users_and_roles"]
    # Filed under the question that was asked, in the person's own words, cited
    # to the message they said it in. Never invented.
    assert recorded["value"] == ["Guests", "staff"]
    assert recorded["provenance"] == ["m3"]
    assert "users_and_roles" not in body["gate"]["missing_core"]
