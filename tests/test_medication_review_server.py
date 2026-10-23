"""HTTP smoke tests for the synthetic-only medication review demo."""
import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

from ai_front_desk.clinical.server import Handler


def _with_demo_server(run):
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        return run(f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_medication_review_page_is_available_for_demo_clinic():
    def run(base_url):
        with urllib.request.urlopen(
            base_url + "/medication-review?clinic=demo-smile-arts", timeout=3
        ) as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
        assert "Medication teaching and safety review" in body
        assert "catalogue is intentionally empty" in body
        assert "/api/medication-review" in body
        assert "Do not enter real patient data" in body or "synthetic" in body.lower()

    _with_demo_server(run)


def test_medication_review_api_returns_empty_unapproved_catalogue_without_writing():
    def run(base_url):
        payload = {
            "clinic_id": "demo-smile-arts",
            "demo_patient_label": "Demo Patient 01",
            "specialty": "dentistry",
            "diagnosis_code": "DUMMY-DX-1",
            "age_years": 35,
            "allergies_reviewed": True,
            "allergies": [],
            "current_medications_reviewed": True,
            "current_medications": [],
            "pregnancy_status": "not_applicable",
            "lactation_status": "not_applicable",
            "severe_allergy": False,
            "renal_function": "unknown",
            "hepatic_function": "unknown",
            "additional_facts": {},
        }
        request = urllib.request.Request(
            base_url + "/api/medication-review",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            result = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
        assert result["ok"] is True
        assert result["catalog"]["status"] == "draft"
        assert result["review"]["candidate_options"] == []
        assert result["review"]["prescribe_or_order_action"] is False
        assert result["persisted"] is False
        assert result["prescription_created"] is False

    _with_demo_server(run)


def test_medication_review_api_rejects_real_person_label():
    def run(base_url):
        payload = {
            "clinic_id": "demo-smile-arts",
            "demo_patient_label": "Jane Realperson",
            "specialty": "dentistry",
            "diagnosis_code": "DUMMY-DX-1",
        }
        request = urllib.request.Request(
            base_url + "/api/medication-review",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=3)
            raise AssertionError("A non-synthetic patient label should be rejected.")
        except urllib.error.HTTPError as error:
            assert error.code == 422
            body = json.loads(error.read().decode("utf-8"))
            assert "fictional label" in body["error"]

    _with_demo_server(run)
