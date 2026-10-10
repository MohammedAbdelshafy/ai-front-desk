"""Tests for intake processing: validation, contradictions, FHIR responses."""
from pathlib import Path

import pytest

from ai_front_desk.clinical.intake import (
    process_intake, check_contradictions, find_escape_answers,
    to_fhir_questionnaire_response,
)
from ai_front_desk.clinical.question_bank import load_bank

BANK_PATH = Path(__file__).resolve().parent.parent / "ai_front_desk" / "clinical" / "dental_intake_v1.json"


@pytest.fixture()
def bank():
    return load_bank(BANK_PATH)


def valid_answers():
    return {
        "id.full_name": "Synth Patient",
        "id.dob": "1990-01-01",
        "id.phone": "555-0100",
        "id.contact_pref": "Phone call",
        "visit.reason": "Routine checkup / cleaning",
        "med.taking_any": "No",
        "med.antibiotics_recent": "No",
        "allergy.med_allergy": "No",
        "allergy.latex": "No",
        "allergy.anesthesia": "No",
        "consent.accuracy": "Yes",
    }


def test_valid_intake_passes(bank):
    result = process_intake(bank, valid_answers())
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["missing_required"] == []


def test_missing_required_blocks(bank):
    answers = valid_answers()
    del answers["id.full_name"]
    result = process_intake(bank, answers)
    assert result["valid"] is False
    assert "id.full_name" in result["missing_required"]


def test_contradiction_no_meds_but_list(bank):
    answers = valid_answers()
    answers["med.list"] = "Lisinopril 10mg daily"
    result = process_intake(bank, answers)
    assert any(f["type"] == "contradiction" for f in result["contradictions"])
    # contradiction findings are labeled as system checks, not patient facts
    for f in result["contradictions"]:
        assert f["source"] == "system_check"


def test_contradiction_no_allergy_but_details(bank):
    found = check_contradictions({"allergy.med_allergy": "No",
                                  "allergy.med_which": "Penicillin rash"})
    assert len(found) == 1
    assert found[0]["qids"] == ["allergy.med_allergy", "allergy.med_which"]


def test_escape_on_required_needs_confirmation(bank):
    answers = valid_answers()
    answers["id.contact_pref"] = "Prefer not to answer"
    found = find_escape_answers(bank, answers)
    assert any(f["qids"] == ["id.contact_pref"] for f in found)


def test_fhir_questionnaire_response(bank):
    resp = to_fhir_questionnaire_response(bank, valid_answers(), "sub_abc123")
    assert resp["resourceType"] == "QuestionnaireResponse"
    assert resp["id"] == "sub_abc123"
    assert resp["status"] == "completed"
    assert resp["questionnaire"].endswith("/dental-intake/1.0.0")
    # yes_no answers map to booleans
    med = next(i for i in resp["item"] if i["linkId"] == "med.taking_any")
    assert med["answer"] == [{"valueBoolean": False}]
    # unanswered optional questions are omitted, not fabricated
    assert not any(i["linkId"] == "med.list" for i in resp["item"])
