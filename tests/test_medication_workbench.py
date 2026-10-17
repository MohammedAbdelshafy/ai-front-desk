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
    page = render_page({"case_id": "synthetic-case-003", "proposed_assessment": "Synthetic assessment for demo"}, review)
    assert "No verified evidence found" in page
    assert "Do not infer that a medicine is appropriate or safe" in page


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
