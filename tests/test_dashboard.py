"""Tests for the dentist brief: labeling, flags, corrections overlay."""
from pathlib import Path

import pytest

from ai_front_desk.clinical.dashboard import generate_brief
from ai_front_desk.clinical.question_bank import load_bank

BANK_PATH = Path(__file__).resolve().parent.parent / "ai_front_desk" / "clinical" / "dental_intake_v1.json"


@pytest.fixture()
def bank():
    return load_bank(BANK_PATH)


def _submission(answers):
    return {
        "submission_id": "sub_test1",
        "clinic_id": "clinic-a",
        "bank_id": "dental-intake",
        "bank_version": "1.0.0",
        "patient_ref": "Synth Patient",
        "answers": answers,
        "status": "submitted",
        "created_at": 0,
        "updated_at": 0,
    }


def test_brief_labels_patient_reported(bank):
    answers = {"id.demo_label": "Demo Patient Synth", "id.contact_pref": "Phone call",
               "visit.reason": "Tooth pain", "med.taking_any": "Yes",
               "med.list": "Ibuprofen 200mg as needed",
               "med.antibiotics_recent": "No", "allergy.med_allergy": "Yes",
               "allergy.med_which": "Penicillin — rash",
               "allergy.latex": "No", "allergy.anesthesia": "No",
               "consent.accuracy": "Yes"}
    brief = generate_brief(bank, _submission(answers))
    for entries in brief["sections"].values():
        for e in entries:
            assert e["source"] == "patient_reported"
    assert brief["original_answers_preserved"] is True


def test_brief_flags_contradiction(bank):
    answers = {"id.demo_label": "Demo Patient P",
               "id.contact_pref": "Phone call", "visit.reason": "Tooth pain",
               "med.taking_any": "No", "med.list": "Lisinopril",
               "med.antibiotics_recent": "No", "allergy.med_allergy": "No",
               "allergy.latex": "No", "allergy.anesthesia": "No",
               "consent.accuracy": "Yes"}
    brief = generate_brief(bank, _submission(answers))
    assert any(f["type"] == "contradiction" and f["severity"] == "high"
               for f in brief["flags"])


def test_brief_flags_missing_required(bank):
    answers = {"id.demo_label": "Demo Patient P",
               "id.contact_pref": "Phone call", "visit.reason": "Tooth pain",
               "med.taking_any": "No", "med.antibiotics_recent": "No",
               "allergy.med_allergy": "No", "allergy.latex": "No",
               "allergy.anesthesia": "No", "consent.accuracy": "Yes"}
    brief = generate_brief(bank, _submission(answers))
    # consent.accuracy present; id.demo_label etc present — nothing missing
    assert not any(f["type"] == "missing" for f in brief["flags"])
    del answers["consent.accuracy"]
    brief2 = generate_brief(bank, _submission(answers))
    assert any(f["type"] == "missing" for f in brief2["flags"])


def test_structured_rollup_labeled_not_ai_or_clinical(bank):
    answers = {"id.demo_label": "Demo Patient P",
               "id.contact_pref": "Phone call", "visit.reason": "Tooth pain",
               "med.taking_any": "No", "med.antibiotics_recent": "No",
               "allergy.med_allergy": "No", "allergy.latex": "No",
               "allergy.anesthesia": "No", "consent.accuracy": "Yes"}
    brief = generate_brief(bank, _submission(answers))
    assert brief["structured_rollup"]["source"] == "structured_rollup"
    assert "not a clinical interpretation" in brief["structured_rollup"]["disclaimer"]


def test_correction_overlay_does_not_rewrite_original(bank):
    answers = {"id.demo_label": "Demo Patient P",
               "id.contact_pref": "Phone call", "visit.reason": "Tooth pain",
               "med.taking_any": "Yes", "med.list": "Old Med",
               "med.antibiotics_recent": "No", "allergy.med_allergy": "No",
               "allergy.latex": "No", "allergy.anesthesia": "No",
               "consent.accuracy": "Yes"}
    corrections = [{"qid": "med.list", "new_value": "New Med 5mg",
                    "source": "staff_verified", "author": "Nurse Synth"}]
    brief = generate_brief(bank, _submission(answers), corrections)
    med_entries = brief["sections"]["medications"]
    entry = next(e for e in med_entries if e["qid"] == "med.list")
    assert entry["answer"] == "Old Med"  # original preserved
    assert entry["corrected_answer"] == "New Med 5mg"
    assert "med.list" in brief["corrected_qids"]


def test_priority_sections_first(bank):
    answers = {"id.demo_label": "Demo Patient P",
               "id.contact_pref": "Phone call", "visit.reason": "Tooth pain",
               "med.taking_any": "No", "med.antibiotics_recent": "No",
               "allergy.med_allergy": "No", "allergy.latex": "No",
               "allergy.anesthesia": "No", "consent.accuracy": "Yes"}
    brief = generate_brief(bank, _submission(answers))
    order = brief["section_order"]
    # allergies and medications surface before identity
    assert order.index("allergies") < order.index("identity")
