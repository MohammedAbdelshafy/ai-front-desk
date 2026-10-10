import json
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from ai_front_desk.clinical_intake import (
    DEMO_CLINIC_ID,
    FORM_VERSION,
    IntakeNotFoundError,
    IntakeValidationError,
    create_intake,
    get_intake,
    initialize_database,
    list_intakes,
    normalize_intake,
    review_intake,
    seed_demo_records,
)
from ai_front_desk.demo_app import make_server


def valid_payload(**changes):
    payload = {
        "patient_label": "Demo Patient Testing",
        "age_group": "40_64",
        "reason_for_visit": "Fictional routine check-up.",
        "symptom_duration": "",
        "allergy_status": "no",
        "allergy_details": "",
        "medication_status": "no",
        "medication_details": "",
        "antibiotic_status": "no",
        "antibiotic_details": "",
        "condition_status": "no",
        "condition_details": "",
        "surgery_status": "no",
        "surgery_details": "",
        "anesthesia_reaction_status": "no",
        "anesthesia_details": "",
        "dental_history": "Fictional history only.",
    }
    payload.update(changes)
    return payload


def test_normalize_requires_demo_label_and_supported_statuses():
    normalized = normalize_intake(valid_payload())
    assert normalized["patient_label"] == "Demo Patient Testing"
    assert "clinic_id" not in normalized

    with pytest.raises(IntakeValidationError, match="fictional label"):
        normalize_intake(valid_payload(patient_label="Jane Doe"))
    with pytest.raises(IntakeValidationError, match="Choose Yes"):
        normalize_intake(valid_payload(allergy_status="maybe"))


@pytest.mark.parametrize(
    ("status_field", "detail_field"),
    [
        ("allergy_status", "allergy_details"),
        ("medication_status", "medication_details"),
        ("antibiotic_status", "antibiotic_details"),
        ("condition_status", "condition_details"),
        ("surgery_status", "surgery_details"),
        ("anesthesia_reaction_status", "anesthesia_details"),
    ],
)
def test_yes_requires_details_for_review(status_field, detail_field):
    payload = valid_payload(**{status_field: "yes"})
    with pytest.raises(IntakeValidationError, match="Add the details"):
        normalize_intake(payload)
    payload[detail_field] = "Fictional details, as reported."
    assert normalize_intake(payload)[detail_field]


def test_payload_rejects_attempt_to_select_tenant_or_extra_fields():
    with pytest.raises(IntakeValidationError, match="Unexpected intake field"):
        normalize_intake(valid_payload(clinic_id="another-clinic"))


def test_creates_persistent_local_record_with_version_and_audit():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "demo.sqlite3"
        record = create_intake(db, valid_payload())
        assert record["clinic_id"] == DEMO_CLINIC_ID
        assert record["form_version"] == FORM_VERSION
        assert record["status"] == "awaiting_review"
        assert record["answers"]["medication_status"] == "no"
        assert record["audit_events"][0]["action"] == "intake_submitted"
        assert get_intake(db, record["id"])["answers"] == record["answers"]


def test_review_records_history_and_changes_status():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "demo.sqlite3"
        record = create_intake(db, valid_payload())
        updated = review_intake(
            db, record["id"], "Demo Clinician", "needs_clarification", "Fictional note."
        )
        assert updated["status"] == "needs_clarification"
        assert len(updated["reviews"]) == 1
        assert updated["reviews"][0]["notes"] == "Fictional note."
        assert updated["audit_events"][-1]["action"] == "clinical_review_recorded"

        updated_again = review_intake(db, record["id"], "Demo Clinician", "reviewed", "")
        assert updated_again["status"] == "reviewed"
        assert len(updated_again["reviews"]) == 2


def test_unknown_intake_is_not_returned():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "demo.sqlite3"
        initialize_database(db)
        with pytest.raises(IntakeNotFoundError):
            get_intake(db, "f" * 32)


def test_demo_seed_contains_only_explicit_synthetic_labels_and_runs_once():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "demo.sqlite3"
        seed_demo_records(db)
        first = list_intakes(db)
        seed_demo_records(db)
        second = list_intakes(db)
        assert len(first) == 3
        assert len(second) == 3
        assert all(
            record["answers"]["patient_label"].startswith(("Demo ", "Test ", "Sample "))
            for record in first
        )
        assert {record["status"] for record in first} == {
            "awaiting_review", "reviewed", "needs_clarification"
        }


def http_json(base, path, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw), response.headers
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw), exc.headers


def test_http_api_runs_full_local_intake_and_review_flow():
    with tempfile.TemporaryDirectory() as tmp:
        server = make_server(Path(tmp) / "demo.sqlite3", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        try:
            status, health, headers = http_json(base, "/api/health")
            assert status == 200
            assert health["mode"] == "synthetic-demo-only"
            assert health["real_patient_data_allowed"] is False
            assert health["external_messaging_enabled"] is False
            assert headers.get("Content-Security-Policy")

            status, result, _ = http_json(base, "/api/intakes", "POST", valid_payload())
            assert status == 201
            intake_id = result["id"]
            assert result["status"] == "awaiting_review"

            status, listed, _ = http_json(base, "/api/intakes")
            assert status == 200 and len(listed["items"]) == 1

            status, detail, _ = http_json(base, "/api/intakes/" + intake_id)
            assert status == 200 and detail["id"] == intake_id

            status, reviewed, _ = http_json(
                base,
                "/api/intakes/" + intake_id + "/review",
                "POST",
                {"reviewer": "Demo Clinician", "outcome": "reviewed", "notes": "Fictional note."},
            )
            assert status == 200
            assert reviewed["status"] == "reviewed"
            assert reviewed["reviews"][-1]["reviewer"] == "Demo Clinician"

            status, _, _ = http_json(
                base, "/api/intakes", "POST", valid_payload(patient_label="Jane Doe")
            )
            assert status == 400
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


def test_server_refuses_network_binding():
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="127.0.0.1 only"):
            make_server(Path(tmp) / "demo.sqlite3", host="0.0.0.0", port=8765)
