"""Tests for the clinical question bank: validation, conditionals, FHIR export."""
import json
from pathlib import Path

import pytest

from ai_front_desk.clinical.question_bank import (
    Question, QuestionBank, load_bank, bank_snapshot,
)

BANK_PATH = Path(__file__).resolve().parent.parent / "ai_front_desk" / "clinical" / "dental_intake_v1.json"


@pytest.fixture()
def bank():
    return load_bank(BANK_PATH)


def test_bank_loads_with_expected_sections(bank):
    sections = {q.section for q in bank.questions}
    for expected in ("identity", "visit", "medications", "allergies",
                     "conditions", "history", "other", "consent"):
        assert expected in sections
    assert bank.version == "1.0.0"
    assert bank.specialty == "dentistry"


def test_bank_marked_draft_pending_dentist_review(bank):
    # Honesty: the questionnaire structure is NOT dentist-approved yet.
    assert bank.review_status == "draft"


def test_conditional_questions_hidden_until_triggered(bank):
    hidden = bank.visible_questions({})
    qids = {q.qid for q in hidden}
    assert "med.list" not in qids
    assert "visit.reason_other" not in qids

    shown = bank.visible_questions({"med.taking_any": "Yes"})
    assert "med.list" in {q.qid for q in shown}

    shown2 = bank.visible_questions({"visit.reason": "Other"})
    assert "visit.reason_other" in {q.qid for q in shown2}


def test_escape_answers_always_valid(bank):
    q = bank.get("id.contact_pref")
    assert q.validate("I don't know") == []
    assert q.validate("Prefer not to answer") == []


def test_invalid_choice_rejected(bank):
    q = bank.get("id.contact_pref")
    errors = q.validate("telepathy")
    assert len(errors) == 1


def test_required_missing_flagged(bank):
    missing = bank.missing_required({})
    assert "id.demo_label" in missing
    assert "consent.accuracy" in missing


def test_answer_to_hidden_question_flagged(bank):
    errors = bank.validate_answers({"med.list": "Aspirin"})
    assert any("med.list" in e and "not currently visible" in e for e in errors)


def test_fhir_questionnaire_export_shape(bank):
    fhir = bank.to_fhir_questionnaire()
    assert fhir["resourceType"] == "Questionnaire"
    assert fhir["version"] == "1.0.0"
    assert len(fhir["item"]) == len(bank.questions)
    # conditional question carries enableWhen
    med_list = next(i for i in fhir["item"] if i["linkId"] == "med.list")
    assert med_list["enableWhen"][0]["question"] == "med.taking_any"
    # escape options exported as answer options
    contact = next(i for i in fhir["item"] if i["linkId"] == "id.contact_pref")
    values = [o["valueString"] for o in contact["answerOption"]]
    assert "I don't know" in values


def test_bank_snapshot_immutable_provenance(bank):
    snap = bank_snapshot(bank)
    assert snap == {"bank_id": "dental-intake", "version": "1.0.0",
                    "title": bank.title, "review_status": "draft",
                    "review_date": "", "question_count": len(bank.questions)}
