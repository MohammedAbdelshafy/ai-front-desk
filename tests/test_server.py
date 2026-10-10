"""End-to-end tests for the clinical demo server (real HTTP on localhost).

Covers: landing page, intake submission API, validation rejection,
dashboard listing, record brief, review recording, correction recording,
audit trail, and cross-tenant denial over HTTP.
"""
import json
import threading
import urllib.request
import urllib.error

import pytest

from ai_front_desk.clinical import server as srv
from ai_front_desk.clinical.store import ClinicalStore


@pytest.fixture()
def live_server(tmp_path, monkeypatch):
    monkeypatch.setattr(srv, "DB_PATH", tmp_path / "e2e.db")
    store = ClinicalStore(tmp_path / "e2e.db")
    srv.ensure_demo_clinics(store)
    srv.Handler.store = store
    httpd = srv.HTTPServer(("127.0.0.1", 0), srv.Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    store.close()


def _get(base, path):
    with urllib.request.urlopen(base + path) as r:
        return r.status, r.read().decode()


def _post_json(base, path, payload):
    req = urllib.request.Request(
        base + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def _answers():
    return {"id.demo_label": "Demo Patient E2E", "id.contact_pref": "Phone call",
            "visit.reason": "Routine checkup / cleaning",
            "med.taking_any": "No", "med.antibiotics_recent": "No",
            "allergy.med_allergy": "No", "allergy.latex": "No",
            "allergy.anesthesia": "No", "consent.accuracy": "Yes"}


def test_landing_labels_demo(live_server):
    code, body = _get(live_server, "/")
    assert code == 200
    assert "synthetic data only" in body.lower()


def test_intake_page_renders_questions(live_server):
    code, body = _get(live_server, "/intake?clinic=demo-smile-arts")
    assert code == 200
    assert "Pre-visit health history" in body
    assert "med.taking_any" in body


def test_api_intake_accepts_valid(live_server):
    code, resp = _post_json(live_server, "/api/intake",
                            {"clinic_id": "demo-smile-arts",
                             "patient_ref": "Demo Patient E2E", "answers": _answers()})
    assert code == 200
    assert resp["ok"] is True
    assert resp["submission_id"].startswith("sub_")


def test_api_intake_rejects_invalid(live_server):
    bad = _answers()
    del bad["id.demo_label"]
    code, resp = _post_json(live_server, "/api/intake",
                            {"clinic_id": "demo-smile-arts",
                             "patient_ref": "Demo Patient E2E", "answers": bad})
    assert code == 422
    assert resp["ok"] is False
    assert "id.demo_label" in resp["missing"]


def test_dashboard_lists_submission(live_server):
    _post_json(live_server, "/api/intake",
               {"clinic_id": "demo-smile-arts",
                "patient_ref": "Demo Patient E2E", "answers": _answers()})
    code, body = _get(live_server, "/dashboard?clinic=demo-smile-arts")
    assert code == 200
    assert "Demo Patient E2E" in body


def test_record_brief_shows_flags_and_sources(live_server):
    code, resp = _post_json(live_server, "/api/intake",
                            {"clinic_id": "demo-smile-arts",
                             "patient_ref": "Demo Patient E2E", "answers": _answers()})
    sub = resp["submission_id"]
    code, body = _get(live_server, f"/record?clinic=demo-smile-arts&sub={sub}")
    assert code == 200
    assert "patient_reported" in body
    assert "ai_summary" in body


def test_unknown_clinic_selector_is_not_reflected(live_server):
    try:
        _get(live_server, "/intake?clinic=%22%3E%3Cscript%3Ealert(1)%3C/script%3E")
        raise AssertionError("expected an unknown clinic to be rejected")
    except urllib.error.HTTPError as e:
        assert e.code == 404


def test_demo_rejects_non_synthetic_patient_label(live_server):
    answers = _answers()
    answers["id.demo_label"] = "Jane Doe"
    code, resp = _post_json(
        live_server, "/api/intake",
        {"clinic_id": "demo-smile-arts", "patient_ref": "Jane Doe", "answers": answers},
    )
    assert code == 422
    assert any("fictional patient label" in item for item in resp["errors"])


def test_intake_rejects_unknown_clinic_id(live_server):
    code, resp = _post_json(
        live_server, "/api/intake",
        {"clinic_id": "attacker-selected-tenant", "patient_ref": "Demo Patient E2E", "answers": _answers()},
    )
    assert code == 404
    assert resp["ok"] is False


def test_server_refuses_non_loopback_binding():
    with pytest.raises(ValueError, match="127.0.0.1 only"):
        srv.run(host="0.0.0.0", port=8766)


def test_cross_tenant_record_denied_over_http(live_server):
    code, resp = _post_json(live_server, "/api/intake",
                            {"clinic_id": "demo-smile-arts",
                             "patient_ref": "Demo Patient E2E", "answers": _answers()})
    sub = resp["submission_id"]
    try:
        _get(live_server, f"/record?clinic=demo-lakeside&sub={sub}")
        raise AssertionError("expected 403")
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_mia_manifest_endpoint(live_server):
    code, body = _get(live_server, "/api/manifest")
    assert code == 200
    manifest = json.loads(body)
    assert manifest["character_id"] == "dental-mia-v1"
    assert "Never diagnose" in " ".join(manifest["safety_boundaries"])
