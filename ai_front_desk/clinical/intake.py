"""Intake workflow: validate answers, detect omissions and contradictions.

This module never performs clinical reasoning. It reports:
- validation errors (structural problems),
- missing required answers (omissions),
- contradictory answers (e.g. "taking no medications" + a medication list),
- items needing staff confirmation (escape-hatch answers on required items).

Every finding is labeled with its source: patient_reported | system_check.
AI-generated summaries are always labeled ai_summary and never overwrite
patient answers.
"""
from __future__ import annotations

from typing import Any

from .question_bank import QuestionBank, ESCAPE_OPTIONS


# Pairs of (qid_a, expected_a, qid_b) where answering qid_b while qid_a has
# expected_a is contradictory.
CONTRADICTION_RULES: tuple[tuple[str, Any, str], ...] = (
    ("med.taking_any", "No", "med.list"),
    ("med.antibiotics_recent", "No", "med.antibiotics_which"),
    ("allergy.med_allergy", "No", "allergy.med_which"),
    ("allergy.anesthesia", "No", "allergy.anesthesia_detail"),
)


def _is_answered(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return len(value) > 0
    return True


def check_contradictions(answers: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for qid_a, expected_a, qid_b in CONTRADICTION_RULES:
        a = answers.get(qid_a)
        b = answers.get(qid_b)
        if a == expected_a and _is_answered(b) and b not in ESCAPE_OPTIONS:
            findings.append({
                "type": "contradiction",
                "source": "system_check",
                "qids": [qid_a, qid_b],
                "message": (
                    f"Answered '{expected_a}' to {qid_a} but also provided "
                    f"an answer to {qid_b}. Staff should confirm which is correct."
                ),
            })
    return findings


def find_escape_answers(bank: QuestionBank, answers: dict[str, Any]) -> list[dict[str, Any]]:
    """Required questions answered with an escape hatch need staff confirmation."""
    findings = []
    for q in bank.visible_questions(answers):
        v = answers.get(q.qid)
        if q.required and isinstance(v, str) and v in ESCAPE_OPTIONS:
            findings.append({
                "type": "needs_confirmation",
                "source": "system_check",
                "qids": [q.qid],
                "message": f"Required question '{q.text}' answered '{v}'. Confirm with patient.",
            })
    return findings


def process_intake(
    bank: QuestionBank, answers: dict[str, Any]
) -> dict[str, Any]:
    """Validate a completed intake and return a structured result.

    Returns dict with: valid, errors, missing_required, contradictions,
    needs_confirmation, visible_question_ids.
    """
    if not isinstance(answers, dict):
        return {
            "valid": False,
            "errors": ["answers: expected an object keyed by question id"],
            "missing_required": bank.missing_required({}),
            "contradictions": [],
            "needs_confirmation": [],
            "visible_question_ids": [q.qid for q in bank.visible_questions({})],
            "bank": {"bank_id": bank.bank_id, "version": bank.version},
        }
    visible = bank.visible_questions(answers)
    errors = bank.validate_answers(answers)
    missing = bank.missing_required(answers)
    contradictions = check_contradictions(answers)
    needs_confirmation = find_escape_answers(bank, answers)
    return {
        "valid": not errors and not missing,
        "errors": errors,
        "missing_required": missing,
        "contradictions": contradictions,
        "needs_confirmation": needs_confirmation,
        "visible_question_ids": [q.qid for q in visible],
        "bank": {"bank_id": bank.bank_id, "version": bank.version},
    }


def to_fhir_questionnaire_response(
    bank: QuestionBank, answers: dict[str, Any], submission_id: str
) -> dict[str, Any]:
    """FHIR R4 QuestionnaireResponse for interoperability / future EHR export."""
    items = []
    for q in bank.visible_questions(answers):
        v = answers.get(q.qid)
        if not _is_answered(v):
            continue
        if isinstance(v, list):
            answer = [{"valueString": str(x)} for x in v]
        elif q.qtype in ("choice", "yes_no"):
            # Choice answers remain strings so "I don't know" is never coerced to "No".
            answer = [{"valueString": str(v)}]
        elif q.qtype == "date":
            answer = [{"valueDate": str(v)}]
        elif q.qtype == "number":
            answer = [{"valueDecimal": float(v)}]
        else:
            answer = [{"valueString": str(v)}]
        items.append({"linkId": q.qid, "text": q.text, "answer": answer})
    return {
        "resourceType": "QuestionnaireResponse",
        "id": submission_id,
        "questionnaire": f"https://mbm.example/fhir/Questionnaire/{bank.bank_id}/{bank.version}",
        "status": "completed",
        "item": items,
    }
