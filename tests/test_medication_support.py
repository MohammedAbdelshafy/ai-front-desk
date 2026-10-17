from datetime import date
import json

import pytest

from ai_front_desk.clinical.medication_support import (
    ClinicianCase, EvidenceCard, EvidenceSource, build_evidence_review, load_registry,
)

TODAY = date(2026, 10, 17)


def make_source(**overrides):
    data = {
        "source_id": "demo-source-1",
        "title": "Synthetic Demonstration Reference (not clinical content)",
        "publisher": "Example publisher", "jurisdiction": "US",
        "url": "https://example.org/demo-reference",
        "content_rights": "approved_summary", "approval_status": "approved",
        "reviewer": "Qualified reviewer role (test fixture)",
        "reviewed_on": "2026-10-01", "review_due_on": "2027-10-01",
        "edition": "Demo edition 1", "version": "test-1", "published_on": "2026-01-01",
    }
    data.update(overrides)
    return EvidenceSource.from_dict(data)


def make_card(**overrides):
    data = {
        "evidence_id": "demo-card-1", "source_id": "demo-source-1",
        "medicine_or_class": "Synthetic demo class X (not a real medication recommendation)",
        "evidence_summary": "Synthetic test-only summary; not clinical guidance.",
        "assessment_terms": ["synthetic dental scenario"], "section": "Demo section 1",
        "jurisdiction": "US", "approval_status": "approved",
        "reviewer": "Qualified reviewer role (test fixture)",
        "reviewed_on": "2026-10-01", "review_due_on": "2027-10-01",
        "required_patient_factors": ["allergies", "current_medications"],
        "caution_tags": ["demo-risk-tag"],
    }
    data.update(overrides)
    return EvidenceCard.from_dict(data)


def make_case(**overrides):
    data = {
        "case_id": "synthetic-case-001", "proposed_assessment": "Synthetic dental scenario for testing",
        "symptoms": ["synthetic test symptom"], "jurisdiction": "US",
        "reviewed_factors": [], "patient_risk_tags": [],
    }
    data.update(overrides)
    return ClinicianCase.from_dict(data)


def test_retrieves_approved_current_evidence_with_provenance():
    result = build_evidence_review(make_case(), [make_source()], [make_card()], today=TODAY)
    assert result["status"] == "clinician_review_required"
    assert len(result["matched_evidence"]) == 1
    item = result["matched_evidence"][0]
    assert item["source_reference"]["title"].startswith("Synthetic Demonstration")
    assert item["source_reference"]["section_or_page"] == "Demo section 1"
    assert item["safety_assessment"] == "not_performed_by_this_module"
    assert result["autonomous_prescribing"] is False
    assert result["dose_calculation_performed"] is False
    assert result["comprehensive_interaction_check_performed"] is False


def test_unapproved_source_fails_closed():
    result = build_evidence_review(make_case(), [make_source(approval_status="draft")], [make_card()], today=TODAY)
    assert result["matched_evidence"] == []
    assert result["status"] == "no_verified_evidence"
    assert result["safety_conclusion"] == "not_established"


def test_overdue_source_review_fails_closed():
    result = build_evidence_review(make_case(), [make_source(review_due_on="2026-10-16")], [make_card()], today=TODAY)
    assert result["matched_evidence"] == []
    assert result["excluded_source_count"] == 1


def test_uncleared_rights_fails_closed():
    result = build_evidence_review(make_case(), [make_source(content_rights="unknown")], [make_card()], today=TODAY)
    assert result["matched_evidence"] == []


def test_jurisdiction_must_match_both_card_and_source():
    result = build_evidence_review(make_case(jurisdiction="CA"), [make_source()], [make_card()], today=TODAY)
    assert result["matched_evidence"] == []
    result = build_evidence_review(make_case(), [make_source(jurisdiction="UK")], [make_card()], today=TODAY)
    assert result["matched_evidence"] == []


def test_missing_patient_factors_become_review_prompts_not_safety_conclusions():
    result = build_evidence_review(make_case(), [make_source()], [make_card()], today=TODAY)
    prompts = [flag for flag in result["flags"] if flag["code"] == "patient_factor_needs_review"]
    assert {flag["factor"] for flag in prompts} == {"allergies", "current_medications"}
    assert result["safety_conclusion"] == "not_established"


def test_configured_caution_tag_surfaces_review_prompt():
    result = build_evidence_review(
        make_case(patient_risk_tags=["demo-risk-tag"]), [make_source()], [make_card()], today=TODAY
    )
    assert any(flag["code"] == "configured_caution_tag_match" for flag in result["flags"])


def test_no_matching_evidence_never_invents_a_card():
    result = build_evidence_review(
        make_case(proposed_assessment="Different synthetic scenario"),
        [make_source()], [make_card()], today=TODAY
    )
    assert result["matched_evidence"] == []
    assert result["status"] == "no_verified_evidence"
    assert "Do not infer" in result["message"]


def test_missing_assessment_returns_for_input():
    result = build_evidence_review(
        make_case(proposed_assessment="   "), [make_source()], [make_card()], today=TODAY
    )
    assert result["status"] == "needs_clinician_input"
    assert result["matched_evidence"] == []
    assert result["flags"][0]["code"] == "missing_clinician_assessment"


def test_case_reference_must_not_be_direct_identifier():
    with pytest.raises(ValueError):
        make_case(case_id="1234567890")
    with pytest.raises(ValueError):
        make_case(case_id="Jane Doe")


def test_registry_loader_rejects_duplicate_source_ids(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({
        "schema_version": "1.0",
        "sources": [
            {"source_id": "same", "title": "A", "publisher": "P", "jurisdiction": "US", "url": "https://example.org/a"},
            {"source_id": "same", "title": "B", "publisher": "P", "jurisdiction": "US", "url": "https://example.org/b"},
        ],
        "evidence_cards": [],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate source_id"):
        load_registry(path)


def test_empty_registry_yields_no_verified_evidence(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"schema_version": "1.0", "sources": [], "evidence_cards": []}), encoding="utf-8")
    sources, cards = load_registry(path)
    result = build_evidence_review(make_case(), sources, cards, today=TODAY)
    assert result["matched_evidence"] == []
    assert result["status"] == "no_verified_evidence"


def test_source_date_after_today_is_rejected():
    result = build_evidence_review(
        make_case(), [make_source(reviewed_on="2026-11-01")], [make_card()], today=TODAY
    )
    assert result["matched_evidence"] == []
