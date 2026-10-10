"""Dentist-facing patient history brief.

Generates a structured, readable summary from a submission. Strict labeling:
- patient_reported: exactly what the patient answered (never altered).
- system_check: omissions, contradictions, items needing confirmation.
- ai_summary: clearly labeled derived text; never overwrites patient answers.
- clinician_entered: reviews and corrections by staff.

No diagnosis, no treatment recommendation, no medication advice.
"""
from __future__ import annotations

from typing import Any

from .intake import process_intake, _is_answered
from .question_bank import QuestionBank, ESCAPE_OPTIONS


SECTION_LABELS = {
    "identity": "Patient",
    "visit": "Visit",
    "medications": "Medications",
    "allergies": "Allergies",
    "conditions": "Conditions",
    "history": "Medical history",
    "other": "Other",
    "consent": "Consent",
}

# Sections the dentist scans first.
PRIORITY_SECTIONS = ("allergies", "medications", "conditions", "visit")


def _fmt_value(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value)


def generate_brief(
    bank: QuestionBank,
    submission: dict[str, Any],
    corrections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the dentist brief. Returns a structured dict for UI rendering."""
    answers = submission["answers"]
    result = process_intake(bank, answers)

    sections: dict[str, list[dict[str, Any]]] = {}
    for q in bank.visible_questions(answers):
        v = answers.get(q.qid)
        if not _is_answered(v):
            continue
        entry: dict[str, Any] = {
            "qid": q.qid,
            "question": q.text,
            "answer": _fmt_value(v),
            "source": "patient_reported",
        }
        if isinstance(v, str) and v in ESCAPE_OPTIONS:
            entry["flag"] = "escape_answer"
        sections.setdefault(q.section, []).append(entry)

    # Apply corrections as overlays — originals preserved in the audit trail.
    corrected_qids = set()
    for c in corrections or []:
        corrected_qids.add(c["qid"])
        for entries in sections.values():
            for e in entries:
                if e["qid"] == c["qid"]:
                    e["corrected_answer"] = c["new_value"]
                    e["correction_source"] = c["source"]
                    e["corrected_by"] = c["author"]

    flags: list[dict[str, Any]] = []
    for c in result["contradictions"]:
        flags.append({**c, "severity": "high"})
    for n in result["needs_confirmation"]:
        flags.append({**n, "severity": "medium"})
    for qid in result["missing_required"]:
        q = bank.get(qid)
        flags.append({
            "type": "missing",
            "source": "system_check",
            "severity": "high",
            "qids": [qid],
            "message": f"Required question unanswered: '{q.text if q else qid}'.",
        })

    # ai_summary: a labeled, conservative rollup — facts only, no inference.
    allergy_items = [e for e in sections.get("allergies", [])]
    med_items = [e for e in sections.get("medications", [])]
    summary_lines = []
    if allergy_items:
        reported = [e for e in allergy_items if e["answer"] not in ESCAPE_OPTIONS and e["answer"] != "No"]
        summary_lines.append(
            "Allergies reported: " + (", ".join(e["answer"] for e in reported) if reported else "none reported")
        )
    if med_items:
        summary_lines.append(f"{len(med_items)} medication question(s) answered; see details below.")

    return {
        "submission_id": submission["submission_id"],
        "patient_ref": submission["patient_ref"],
        "status": submission["status"],
        "bank": {"bank_id": bank.bank_id, "version": bank.version,
                 "review_status": bank.review_status},
        "sections": sections,
        "section_order": [s for s in PRIORITY_SECTIONS if s in sections]
                         + [s for s in sections if s not in PRIORITY_SECTIONS],
        "section_labels": SECTION_LABELS,
        "flags": flags,
        "flag_count": len(flags),
        "corrected_qids": sorted(corrected_qids),
        "ai_summary": {
            "source": "ai_summary",
            "lines": summary_lines,
            "disclaimer": "Derived rollup of patient-reported answers only. "
                          "Not a clinical interpretation.",
        },
        "original_answers_preserved": True,
    }
