"""Safety contract tests for Mia's clinician-facing medication review engine."""

from ai_front_desk.clinical.medication_support import review_medication_options


def _request(specialty="dentistry", diagnosis_code="DX-001", **fact_overrides):
    facts = {
        "age_years": 38,
        "allergies_reviewed": True,
        "current_medications_reviewed": True,
        "current_medications": [],
        "pregnancy_status": "not_applicable",
        "lactation_status": "not_applicable",
        "severe_allergy": False,
    }
    facts.update(fact_overrides)
    return {
        "specialty": specialty,
        "diagnosis_code": diagnosis_code,
        "patient_facts": facts,
    }


def _entry(**overrides):
    entry = {
        "id": "demo-entry-1",
        "generic_name": "DemoMed-A",
        "specialties": ["dentistry"],
        "diagnosis_codes": ["DX-001"],
        "required_facts": ["pregnancy_status", "lactation_status", "severe_allergy"],
        "contraindications": [
            {
                "fact": "severe_allergy",
                "equals": True,
                "reason": "A clinician must resolve this documented allergy conflict.",
            }
        ],
        "interactions": [
            {
                "medication": "DemoMed-Interaction",
                "severity": "major",
                "reason": "Review the interaction against the cited source.",
            }
        ],
        "teaching": {
            "why_consider": "Synthetic teaching summary from an approved entry.",
            "mechanism": "Synthetic mechanism description.",
            "common_adverse_effects": "Consult the linked official label.",
            "serious_warnings": "Consult the linked official label.",
            "monitoring": "Confirm monitoring with the cited source.",
            "counseling": "Use the clinician-approved counseling material.",
            "dose_summary": "No dose supplied by this demo entry.",
        },
        "source": {
            "title": "Synthetic reference used for software tests",
            "url": "https://example.org/demo-reference",
            "version": "test-v1",
            "effective_date": "2026-01-01",
            "reviewer": "Qualified clinician (synthetic test fixture)",
            "reviewed_at": "2026-10-01",
            "review_due": "2027-10-01",
            "review_status": "approved",
        },
    }
    entry.update(overrides)
    return entry


def test_approved_exact_match_returns_explained_option_and_never_prescribes():
    result = review_medication_options(
        _request(), [_entry()], today="2026-10-23"
    )

    assert result["status"] == "options_for_clinician_review"
    assert [item["id"] for item in result["candidate_options"]] == ["demo-entry-1"]
    candidate = result["candidate_options"][0]
    assert candidate["teaching"]["mechanism"] == "Synthetic mechanism description."
    assert candidate["source"]["url"] == "https://example.org/demo-reference"
    assert result["ranking"] == "none"
    assert result["prescribe_or_order_action"] is False
    assert result["clinician_confirmation_required"] is True


def test_incomplete_allergy_or_medication_reconciliation_blocks_all_options():
    request = _request(allergies_reviewed=False)
    result = review_medication_options(request, [_entry()], today="2026-10-23")

    assert result["status"] == "blocked_incomplete_context"
    assert result["candidate_options"] == []
    assert "allergies_reviewed" in result["missing_context"]
    assert result["prescribe_or_order_action"] is False


def test_unknown_required_patient_factor_withholds_candidate():
    request = _request(pregnancy_status="unknown")
    result = review_medication_options(request, [_entry()], today="2026-10-23")

    assert result["candidate_options"] == []
    assert result["status"] == "no_approved_options"
    assert result["withheld_options"][0]["reason_code"] == "missing_required_fact"
    assert "pregnancy_status" in result["withheld_options"][0]["missing_facts"]


def test_exact_diagnosis_match_only_no_fuzzy_diagnosis_guessing():
    result = review_medication_options(
        _request(diagnosis_code="DX-001-similar"), [_entry()], today="2026-10-23"
    )

    assert result["candidate_options"] == []
    assert result["status"] == "no_approved_options"


def test_other_specialty_entry_is_not_returned():
    entry = _entry(specialties=["gynecology"])
    result = review_medication_options(
        _request(specialty="dentistry"), [entry], today="2026-10-23"
    )

    assert result["candidate_options"] == []
    assert result["status"] == "no_approved_options"


def test_draft_or_unreviewed_reference_never_generates_candidate():
    entry = _entry()
    entry["source"] = {**entry["source"], "review_status": "draft"}
    result = review_medication_options(
        _request(), [entry], today="2026-10-23"
    )

    assert result["candidate_options"] == []
    assert result["status"] == "no_approved_options"


def test_expired_review_date_never_generates_candidate():
    entry = _entry()
    entry["source"] = {**entry["source"], "review_due": "2026-10-22"}
    result = review_medication_options(
        _request(), [entry], today="2026-10-23"
    )

    assert result["candidate_options"] == []
    assert result["status"] == "no_approved_options"


def test_documented_contraindication_withholds_entry():
    result = review_medication_options(
        _request(severe_allergy=True), [_entry()], today="2026-10-23"
    )

    assert result["candidate_options"] == []
    assert result["withheld_options"][0]["reason_code"] == "contraindication"
    assert result["status"] == "no_approved_options"


def test_interaction_conflict_withholds_entry_for_review():
    result = review_medication_options(
        _request(current_medications=["demomed-interaction"]),
        [_entry()],
        today="2026-10-23",
    )

    assert result["candidate_options"] == []
    assert result["withheld_options"][0]["reason_code"] == "interaction_requires_resolution"


def test_gynecology_requires_reproductive_context_when_the_entry_depends_on_it():
    entry = _entry(
        specialties=["gynecology"],
        diagnosis_codes=["GYN-DX-001"],
    )
    request = _request(
        specialty="gynecology",
        diagnosis_code="GYN-DX-001",
        pregnancy_status="unknown",
    )
    result = review_medication_options(request, [entry], today="2026-10-23")

    assert result["candidate_options"] == []
    assert result["withheld_options"][0]["reason_code"] == "missing_required_fact"
    assert "pregnancy_status" in result["withheld_options"][0]["missing_facts"]


def test_untrusted_or_malformed_source_is_not_eligible():
    entry = _entry()
    entry["source"] = {**entry["source"], "url": "http://example.org/demo-reference"}
    result = review_medication_options(
        _request(), [entry], today="2026-10-23"
    )

    assert result["candidate_options"] == []
    assert result["status"] == "no_approved_options"


def test_unknown_specialty_or_missing_diagnosis_fails_closed():
    unsupported = review_medication_options(
        _request(specialty="general-chat"), [_entry()], today="2026-10-23"
    )
    missing_diagnosis = review_medication_options(
        {"specialty": "dentistry", "diagnosis_code": "", "patient_facts": _request()["patient_facts"]},
        [_entry()],
        today="2026-10-23",
    )

    assert unsupported["status"] == "blocked_invalid_request"
    assert unsupported["candidate_options"] == []
    assert missing_diagnosis["status"] == "blocked_incomplete_context"
    assert missing_diagnosis["candidate_options"] == []
