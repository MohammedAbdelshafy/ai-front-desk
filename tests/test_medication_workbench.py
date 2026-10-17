from datetime import date

from ai_front_desk.clinical.medication_support import ClinicianCase, build_evidence_review
from ai_front_desk.clinical.medication_workbench import case_from_form, render_page, run_review


def test_workbench_renders_brand_and_synthetic_warning():
    page = render_page()
    assert "Dr. Mia" in page
    assert "DO NOT ENTER REAL PATIENT" in page
    assert "Review a synthetic case" in page
    assert "Medication suggestions" not in page


def test_workbench_escapes_user_supplied_fields():
    page = render_page({"case_id": "synthetic-case-001", "proposed_assessment": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_form_captures_context_without_patient_identity_fields():
    case = case_from_form({
        "case_id": "synthetic-case-002",
        "proposed_assessment": "Synthetic assessment",
        "symptoms": "example symptom, another example",
        "reported_allergies": "fictional allergy context",
        "current_medications": "fictional medicine context",
        "relevant_medical_history": "fictional history",
        "reviewed_allergies": "1",
        "reviewed_current_medications": "1",
        "jurisdiction": "US",
    })
    assert case.reported_allergies == "fictional allergy context"
    assert case.current_medications == "fictional medicine context"
    assert case.relevant_medical_history == "fictional history"
    assert case.reviewed_factors == ("allergies", "current_medications")
    assert case.symptoms == ("example symptom", "another example")


def test_workbench_empty_registry_returns_no_verified_evidence():
    review, _case = run_review({
        "case_id": "synthetic-case-003",
        "proposed_assessment": "Synthetic assessment for demo",
        "jurisdiction": "US",
    })
    assert review["status"] == "no_verified_evidence"
    assert review["matched_evidence"] == []
    assert {flag.get("factor") for flag in review["flags"] if flag["code"] == "patient_factor_needs_review"} >= {"allergies", "current_medications"}
    page = render_page({"case_id": "synthetic-case-003", "proposed_assessment": "Synthetic assessment for demo"}, review)
    assert "No verified evidence found" in page
    assert "Do not infer that a medicine is appropriate or safe" in page
    assert "Clinical quality checklist" in page
    assert "Supervising dentist review" in page
    assert "not a clinical quality score" in page.lower()


def test_workbench_rejects_non_synthetic_case_reference():
    try:
        case_from_form({"case_id": "Jane Doe", "proposed_assessment": "Synthetic"})
    except ValueError as exc:
        assert "case_id" in str(exc)
    else:
        raise AssertionError("real-person-like case reference should not pass")


def test_workbench_refuses_non_us_scope():
    try:
        case_from_form({"case_id": "synthetic-case-004", "proposed_assessment": "Synthetic", "jurisdiction": "UK"})
    except ValueError as exc:
        assert "US jurisdiction" in str(exc)
    else:
        raise AssertionError("out-of-scope jurisdiction should be rejected")


# HTTP smoke tests exercise the actual local handler, using loopback and an ephemeral port.
import threading
from http.server import HTTPServer
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest

from ai_front_desk.clinical.medication_workbench import WorkbenchHandler


@pytest.fixture
def workbench_url():
    server = HTTPServer(("127.0.0.1", 0), WorkbenchHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d" % server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_workbench_http_smoke_and_security_headers(workbench_url):
    with urlopen(workbench_url + "/") as response:
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Dr. Mia" in body
        assert "DO NOT ENTER REAL PATIENT" in body
        assert response.headers["Cache-Control"] == "no-store"
        assert "default-src 'none'" in response.headers["Content-Security-Policy"]
        assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_workbench_http_post_returns_no_evidence_for_candidate_only_registry(workbench_url):
    payload = {
        "case_id": "synthetic-case-http-01",
        "proposed_assessment": "Synthetic smoke-test scenario",
        "symptoms": "synthetic symptom",
        "reported_allergies": "fictional allergy",
        "current_medications": "fictional medication",
        "relevant_medical_history": "fictional history",
        "jurisdiction": "US",
    }
    request = Request(
        workbench_url + "/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "No verified evidence found" in body
        assert "fictional allergy" in body
        assert "do not infer that any medicine is appropriate or safe" in body.lower()
        assert response.headers["Cache-Control"] == "no-store"


def test_workbench_http_unknown_routes_return_404(workbench_url):
    with pytest.raises(HTTPError) as exc:
        urlopen(workbench_url + "/unknown")
    assert exc.value.code == 404


def test_checked_box_does_not_override_blank_critical_context():
    case = case_from_form({
        "case_id": "synthetic-case-005",
        "proposed_assessment": "Synthetic assessment",
        "reviewed_allergies": "1",
        "reviewed_current_medications": "1",
        "reported_allergies": "",
        "current_medications": "",
        "jurisdiction": "US",
    })
    assert "allergies" not in case.reviewed_factors
    assert "current_medications" not in case.reviewed_factors


def test_opt_in_public_lookup_sends_only_name(workbench_url, monkeypatch):
    from ai_front_desk.clinical import medication_workbench as workbench

    seen = []
    def fake_lookup(term):
        seen.append(term)
        return {
            "status": "found",
            "lookup_term": term,
            "patient_context_sent": False,
            "rxnorm": {"status": "found", "items": [
                {"rxcui": "99999", "name": "Synthetic example ingredient", "term_type": "IN"}
            ]},
            "openfda_labels": {"status": "not_found", "items": []},
        }
    monkeypatch.setattr(workbench, "lookup_public_drug_metadata", fake_lookup)
    payload = {
        "case_id": "synthetic-case-http-02",
        "proposed_assessment": "Synthetic clinical scenario",
        "symptoms": "fictional symptom",
        "reported_allergies": "fictional allergy context",
        "current_medications": "fictional medicine context",
        "relevant_medical_history": "fictional history",
        "drug_lookup_name": "Synthetic example ingredient",
        "lookup_public_sources": "1",
        "jurisdiction": "US",
    }
    request = Request(
        workbench_url + "/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Public source lookup" in body
        assert "Synthetic example ingredient" in body
        assert "only the standalone medicine name is sent" in body
    assert seen == ["Synthetic example ingredient"]


def test_opt_in_learning_shelf_is_local_only(workbench_url, monkeypatch):
    from ai_front_desk.clinical import medication_workbench as workbench

    called = []
    def fake_search(topic):
        called.append(topic)
        return {
            "query": topic,
            "status": "found",
            "result_count": 1,
            "message": "Educational retrieval only.",
            "results": [{
                "id": "test-learning-card",
                "title": "Synthetic Pharmacology Learning Note",
                "summary": "A local educational summary.",
                "learning_points": ["Concept one", "Concept two"],
                "source_refs": [{
                    "title": "Open source educational book",
                    "url": "https://example.org/open-book/chapter",
                    "license_id": "CC-BY-4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "attribution": "Synthetic attribution for test."
                }],
                "use_scope": "education_only",
                "cannot_support": ["diagnosis", "medicine_selection"]
            }]
        }
    monkeypatch.setattr(workbench, "search_pharmacology_education", fake_search)
    payload = {
        "case_id": "synthetic-case-http-03",
        "proposed_assessment": "Synthetic clinical scenario",
        "symptoms": "fictional symptom",
        "reported_allergies": "fictional allergy context",
        "current_medications": "fictional medicine context",
        "relevant_medical_history": "fictional history",
        "learning_topic": "pharmacokinetics",
        "search_learning_library": "1",
        "jurisdiction": "US",
    }
    request = Request(
        workbench_url + "/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Pharmacology foundations" in body
        assert "Synthetic Pharmacology Learning Note" in body
        assert "Open source educational book" in body
        assert "CC-BY-4.0" in body
    assert called == ["pharmacokinetics"]


def test_learning_shelf_requires_a_topic_when_enabled(workbench_url):
    payload = {
        "case_id": "synthetic-case-http-04",
        "proposed_assessment": "Synthetic clinical scenario",
        "search_learning_library": "1",
        "jurisdiction": "US",
    }
    request = Request(
        workbench_url + "/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Enter a pharmacology learning topic" in body
