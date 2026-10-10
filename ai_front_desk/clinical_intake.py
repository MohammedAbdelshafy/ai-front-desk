"""Versioned, demo-only dental intake records.

This module uses the Python standard library. It is a local prototype, not an
EHR, not a validated clinical form, and not suitable for real patient data.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

FORM_VERSION = "dental-intake-0.1.0"
DEMO_CLINIC_ID = "demo-clinic"

STATUS_OPTIONS = frozenset({"yes", "no", "unsure"})
AGE_GROUP_OPTIONS = frozenset(
    {"under_18", "18_39", "40_64", "65_plus", "prefer_not_to_say"}
)
REVIEW_OUTCOMES = frozenset({"reviewed", "needs_clarification"})

TEXT_LIMITS = {
    "reason_for_visit": 500,
    "allergy_details": 1500,
    "medication_details": 1500,
    "antibiotic_details": 1500,
    "condition_details": 1500,
    "surgery_details": 1500,
    "anesthesia_details": 1500,
    "symptom_duration": 250,
    "dental_history": 1500,
}
STATUS_FIELDS = (
    "allergy_status",
    "medication_status",
    "antibiotic_status",
    "condition_status",
    "surgery_status",
    "anesthesia_reaction_status",
)
DETAIL_FOR_STATUS = {
    "allergy_status": "allergy_details",
    "medication_status": "medication_details",
    "antibiotic_status": "antibiotic_details",
    "condition_status": "condition_details",
    "surgery_status": "surgery_details",
    "anesthesia_reaction_status": "anesthesia_details",
}
DETAIL_LABELS = {
    "allergy_details": "Allergies and reported reactions",
    "medication_details": "Current medicines and supplements",
    "antibiotic_details": "Current or recent antibiotics",
    "condition_details": "Long-term or ongoing conditions",
    "surgery_details": "Previous surgeries or hospitalizations",
    "anesthesia_details": "Previous anesthesia reactions",
}
FIELD_LABELS = {
    "patient_label": "Synthetic patient label",
    "age_group": "Age group",
    "reason_for_visit": "Reason for visit",
    "allergy_status": "Allergies",
    "allergy_details": DETAIL_LABELS["allergy_details"],
    "medication_status": "Current medicines",
    "medication_details": DETAIL_LABELS["medication_details"],
    "antibiotic_status": "Current or recent antibiotics",
    "antibiotic_details": DETAIL_LABELS["antibiotic_details"],
    "condition_status": "Long-term or ongoing conditions",
    "condition_details": DETAIL_LABELS["condition_details"],
    "surgery_status": "Previous surgery or hospitalization",
    "surgery_details": DETAIL_LABELS["surgery_details"],
    "anesthesia_reaction_status": "Previous anesthesia reactions",
    "anesthesia_details": DETAIL_LABELS["anesthesia_details"],
    "symptom_duration": "Symptom duration or timeline",
    "dental_history": "Relevant dental history",
}
QUESTIONNAIRE = {
    "id": "dental-medical-history",
    "version": FORM_VERSION,
    "title": "Dental medical and dental history",
    "approval_status": "draft_requires_dentist_approval",
    "notice": (
        "Fictional demo only. This draft questionnaire is not clinically approved and "
        "must be reviewed by a qualified dentist before any real clinical use."
    ),
    "sections": [
        {
            "id": "visit",
            "number": "01",
            "title": "About this visit",
            "description": "Basic context to prepare the visit.",
            "fields": [
                {
                    "id": "patient_label", "label": "Fictional patient label", "type": "text",
                    "required": True, "max_length": 50, "full_width": True,
                    "placeholder": "e.g., Demo Patient Casey",
                    "help_text": "Must begin with Demo, Test, or Sample. Never enter a real name.",
                },
                {
                    "id": "age_group", "label": "Age group", "type": "select", "required": True,
                    "full_width": False,
                    "options": [
                        {"value": "under_18", "label": "Under 18"},
                        {"value": "18_39", "label": "18–39"},
                        {"value": "40_64", "label": "40–64"},
                        {"value": "65_plus", "label": "65+"},
                        {"value": "prefer_not_to_say", "label": "Prefer not to say"},
                    ],
                },
                {
                    "id": "symptom_duration", "label": "When did the concern begin?", "type": "text",
                    "required": False, "max_length": 250, "full_width": False,
                    "placeholder": "Fictional example: two days ago",
                },
                {
                    "id": "reason_for_visit", "label": "What brings you to the clinic today?",
                    "type": "textarea", "required": True, "max_length": 500, "full_width": True,
                    "rows": 3, "placeholder": "Describe the reason for this sample visit.",
                },
            ],
        },
        {
            "id": "medicines",
            "number": "02",
            "title": "Medicines and allergies",
            "description": "Include what is known. Do not change any medicine based on this form.",
            "fields": [
                {
                    "id": "allergy_status", "label": "Do you have any allergies, including to medicines or antibiotics?",
                    "type": "choice", "required": True, "full_width": True,
                    "options": [
                        {"value": "yes", "label": "Yes"},
                        {"value": "no", "label": "No"},
                        {"value": "unsure", "label": "Not sure"},
                    ],
                },
                {
                    "id": "allergy_details", "label": "Allergy and reaction details", "type": "textarea",
                    "required": False, "conditional_on": "allergy_status", "conditional_value": "yes",
                    "max_length": 1500, "full_width": True, "rows": 2,
                    "placeholder": "Fictional example: allergen and reported reaction.",
                    "help_text": "Describe the reported reaction; the dentist will review it.",
                },
                {
                    "id": "medication_status",
                    "label": "Do you currently take prescription medicines, over-the-counter medicines, vitamins, or supplements?",
                    "type": "choice", "required": True, "full_width": True,
                    "options": [
                        {"value": "yes", "label": "Yes"},
                        {"value": "no", "label": "No"},
                        {"value": "unsure", "label": "Not sure"},
                    ],
                },
                {
                    "id": "medication_details", "label": "Medicine details", "type": "textarea",
                    "required": False, "conditional_on": "medication_status", "conditional_value": "yes",
                    "max_length": 1500, "full_width": True, "rows": 3,
                    "placeholder": "Fictional example: name, strength, dose, frequency, and reason if known.",
                    "help_text": "Include current and recently changed medicines where known.",
                },
                {
                    "id": "antibiotic_status", "label": "Are you taking antibiotics now, or have you taken any recently?",
                    "type": "choice", "required": True, "full_width": True,
                    "options": [
                        {"value": "yes", "label": "Yes"},
                        {"value": "no", "label": "No"},
                        {"value": "unsure", "label": "Not sure"},
                    ],
                },
                {
                    "id": "antibiotic_details", "label": "Antibiotic details", "type": "textarea",
                    "required": False, "conditional_on": "antibiotic_status", "conditional_value": "yes",
                    "max_length": 1500, "full_width": True, "rows": 2,
                    "placeholder": "Fictional example: medicine name and dates or dose if known.",
                },
            ],
        },
        {
            "id": "conditions",
            "number": "03",
            "title": "Ongoing health conditions",
            "description": "Tell the clinic about conditions that may be relevant to your care.",
            "fields": [
                {
                    "id": "condition_status", "label": "Do you have any long-term or ongoing medical conditions?",
                    "type": "choice", "required": True, "full_width": True,
                    "options": [
                        {"value": "yes", "label": "Yes"},
                        {"value": "no", "label": "No"},
                        {"value": "unsure", "label": "Not sure"},
                    ],
                },
                {
                    "id": "condition_details", "label": "Condition details", "type": "textarea",
                    "required": False, "conditional_on": "condition_status", "conditional_value": "yes",
                    "max_length": 1500, "full_width": True, "rows": 3,
                    "placeholder": "Fictional example: condition and current status, if known.",
                    "help_text": "Examples include diabetes, blood pressure, heart, kidney, liver, respiratory, immune, or bleeding conditions.",
                },
            ],
        },
        {
            "id": "procedures",
            "number": "04",
            "title": "Procedures and dental history",
            "description": "Information for the dentist to review.",
            "fields": [
                {
                    "id": "surgery_status", "label": "Have you had surgery or been hospitalized for a significant illness?",
                    "type": "choice", "required": True, "full_width": True,
                    "options": [
                        {"value": "yes", "label": "Yes"},
                        {"value": "no", "label": "No"},
                        {"value": "unsure", "label": "Not sure"},
                    ],
                },
                {
                    "id": "surgery_details", "label": "Procedure details", "type": "textarea",
                    "required": False, "conditional_on": "surgery_status", "conditional_value": "yes",
                    "max_length": 1500, "full_width": True, "rows": 2,
                    "placeholder": "Fictional example: procedure and approximate date, if known.",
                },
                {
                    "id": "anesthesia_reaction_status", "label": "Have you had a reaction or complication with anesthesia?",
                    "type": "choice", "required": True, "full_width": True,
                    "options": [
                        {"value": "yes", "label": "Yes"},
                        {"value": "no", "label": "No"},
                        {"value": "unsure", "label": "Not sure"},
                    ],
                },
                {
                    "id": "anesthesia_details", "label": "Reaction details", "type": "textarea",
                    "required": False, "conditional_on": "anesthesia_reaction_status", "conditional_value": "yes",
                    "max_length": 1500, "full_width": True, "rows": 2,
                    "placeholder": "Fictional example: what happened, if known.",
                },
                {
                    "id": "dental_history", "label": "Relevant dental history", "type": "textarea",
                    "required": False, "max_length": 1500, "full_width": True, "rows": 2,
                    "placeholder": "Fictional example: previous procedures or relevant context.",
                },
            ],
        },
    ],
}

ALLOWED_FIELDS = frozenset(FIELD_LABELS)
_DEMO_LABEL_RE = re.compile(r"(?:Demo|Test|Sample) [A-Za-z0-9][A-Za-z0-9 -]{1,44}\Z")
_REVIEWER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .'-]{1,78}\Z")


class IntakeValidationError(ValueError):
    """Raised when a demo intake payload is invalid."""


class IntakeNotFoundError(LookupError):
    """Raised when an intake does not exist in this local demo."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value: Any, field: str, limit: int, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise IntakeValidationError(FIELD_LABELS.get(field, field) + " must be text.")
    value = value.strip()
    if "\x00" in value:
        raise IntakeValidationError(FIELD_LABELS.get(field, field) + " contains an invalid character.")
    if len(value) > limit:
        raise IntakeValidationError(
            FIELD_LABELS.get(field, field) + " exceeds the " + str(limit) + "-character limit."
        )
    if required and not value:
        raise IntakeValidationError(FIELD_LABELS.get(field, field) + " is required.")
    return value


def normalize_intake(payload: Mapping[str, Any]) -> dict[str, str]:
    """Validate and normalize patient-reported fields for the synthetic demo."""
    if not isinstance(payload, Mapping):
        raise IntakeValidationError("The intake payload must be an object.")
    unknown = set(payload.keys()) - ALLOWED_FIELDS
    if unknown:
        raise IntakeValidationError("Unexpected intake field: " + str(sorted(unknown)[0]))

    patient_label = _text(payload.get("patient_label"), "patient_label", 50, required=True)
    if not _DEMO_LABEL_RE.fullmatch(patient_label):
        raise IntakeValidationError(
            "Use a fictional label beginning with Demo, Test, or Sample. Do not enter real patient details."
        )

    age_group = _text(payload.get("age_group"), "age_group", 40, required=True)
    if age_group not in AGE_GROUP_OPTIONS:
        raise IntakeValidationError("Select one of the available age-group options.")

    normalized: dict[str, str] = {
        "patient_label": patient_label,
        "age_group": age_group,
    }
    normalized["reason_for_visit"] = _text(
        payload.get("reason_for_visit"), "reason_for_visit", TEXT_LIMITS["reason_for_visit"], required=True
    )

    for status_field in STATUS_FIELDS:
        status = _text(payload.get(status_field), status_field, 16, required=True)
        if status not in STATUS_OPTIONS:
            raise IntakeValidationError("Choose Yes, No, or Not sure for " + FIELD_LABELS[status_field] + ".")
        normalized[status_field] = status

    for field, limit in TEXT_LIMITS.items():
        normalized[field] = _text(payload.get(field), field, limit)
    for status_field, detail_field in DETAIL_FOR_STATUS.items():
        if normalized[status_field] == "yes" and not normalized[detail_field]:
            raise IntakeValidationError(
                "Add the details you know for " + FIELD_LABELS[status_field].lower() + "."
            )
        if normalized[status_field] == "no":
            normalized[detail_field] = ""

    return normalized


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def _connection(db_path: str | Path):
    """Commit or roll back a unit of work, and always close the SQLite handle."""
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path: str | Path) -> None:
    """Create the local demo schema. This schema is not production healthcare storage."""
    path = Path(db_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connection(path) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS intakes (
                id TEXT PRIMARY KEY,
                clinic_id TEXT NOT NULL,
                form_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('awaiting_review', 'reviewed', 'needs_clarification')),
                answers_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_intakes_clinic_created
                ON intakes(clinic_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                intake_id TEXT NOT NULL REFERENCES intakes(id) ON DELETE CASCADE,
                reviewer TEXT NOT NULL,
                outcome TEXT NOT NULL CHECK (outcome IN ('reviewed', 'needs_clarification')),
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_reviews_intake_created
                ON reviews(intake_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                intake_id TEXT NOT NULL REFERENCES intakes(id) ON DELETE CASCADE,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                detail_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_intake_created
                ON audit_events(intake_id, created_at DESC);
            """
        )


def _record(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    intake_id = str(row["id"])
    reviews = conn.execute(
        "SELECT id, reviewer, outcome, notes, created_at FROM reviews "
        "WHERE intake_id = ? ORDER BY created_at ASC, id ASC",
        (intake_id,),
    ).fetchall()
    audits = conn.execute(
        "SELECT action, created_at, detail_json FROM audit_events "
        "WHERE intake_id = ? ORDER BY created_at ASC, id ASC",
        (intake_id,),
    ).fetchall()
    return {
        "id": intake_id,
        "clinic_id": row["clinic_id"],
        "form_version": row["form_version"],
        "created_at": row["created_at"],
        "status": row["status"],
        "answers": json.loads(row["answers_json"]),
        "reviews": [
            {
                "id": item["id"],
                "reviewer": item["reviewer"],
                "outcome": item["outcome"],
                "notes": item["notes"],
                "created_at": item["created_at"],
            }
            for item in reviews
        ],
        "audit_events": [
            {
                "action": item["action"],
                "created_at": item["created_at"],
                "details": json.loads(item["detail_json"]),
            }
            for item in audits
        ],
    }


def create_intake(db_path: str | Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    answers = normalize_intake(payload)
    initialize_database(db_path)
    intake_id = uuid.uuid4().hex
    created_at = _now()
    with _connection(db_path) as conn:
        conn.execute(
            "INSERT INTO intakes (id, clinic_id, form_version, created_at, status, answers_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                intake_id,
                DEMO_CLINIC_ID,
                FORM_VERSION,
                created_at,
                "awaiting_review",
                json.dumps(answers, ensure_ascii=False, separators=(",", ":")),
            ),
        )
        conn.execute(
            "INSERT INTO audit_events (id, intake_id, action, created_at, detail_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, intake_id, "intake_submitted", created_at, json.dumps({"form_version": FORM_VERSION})),
        )
        row = conn.execute("SELECT * FROM intakes WHERE id = ?", (intake_id,)).fetchone()
        return _record(conn, row)


def get_intake(db_path: str | Path, intake_id: str) -> dict[str, Any]:
    initialize_database(db_path)
    with _connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM intakes WHERE id = ? AND clinic_id = ?",
            (intake_id, DEMO_CLINIC_ID),
        ).fetchone()
        if row is None:
            raise IntakeNotFoundError("Demo intake was not found.")
        return _record(conn, row)


def list_intakes(db_path: str | Path, limit: int = 100) -> list[dict[str, Any]]:
    initialize_database(db_path)
    safe_limit = min(max(int(limit), 1), 200)
    with _connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM intakes WHERE clinic_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (DEMO_CLINIC_ID, safe_limit),
        ).fetchall()
        return [_record(conn, row) for row in rows]


def review_intake(
    db_path: str | Path,
    intake_id: str,
    reviewer: Any,
    outcome: Any,
    notes: Any = "",
) -> dict[str, Any]:
    reviewer_name = _text(reviewer, "reviewer", 80, required=True)
    if not _REVIEWER_RE.fullmatch(reviewer_name):
        raise IntakeValidationError("Use a demo reviewer label such as Demo Clinician.")
    review_outcome = _text(outcome, "outcome", 40, required=True)
    if review_outcome not in REVIEW_OUTCOMES:
        raise IntakeValidationError("Choose Reviewed or Needs clarification.")
    review_notes = _text(notes, "review_notes", 1200)

    initialize_database(db_path)
    with _connection(db_path) as conn:
        exists = conn.execute(
            "SELECT id FROM intakes WHERE id = ? AND clinic_id = ?",
            (intake_id, DEMO_CLINIC_ID),
        ).fetchone()
        if exists is None:
            raise IntakeNotFoundError("Demo intake was not found.")
        created_at = _now()
        conn.execute(
            "INSERT INTO reviews (id, intake_id, reviewer, outcome, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, intake_id, reviewer_name, review_outcome, review_notes, created_at),
        )
        conn.execute(
            "UPDATE intakes SET status = ? WHERE id = ? AND clinic_id = ?",
            (review_outcome, intake_id, DEMO_CLINIC_ID),
        )
        conn.execute(
            "INSERT INTO audit_events (id, intake_id, action, created_at, detail_json) VALUES (?, ?, ?, ?, ?)",
            (
                uuid.uuid4().hex,
                intake_id,
                "clinical_review_recorded",
                created_at,
                json.dumps({"outcome": review_outcome, "reviewer": reviewer_name}),
            ),
        )
        row = conn.execute("SELECT * FROM intakes WHERE id = ?", (intake_id,)).fetchone()
        return _record(conn, row)


def seed_demo_records(db_path: str | Path) -> None:
    """Create fictional UI examples once, without importing real patient data."""
    initialize_database(db_path)
    with _connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM intakes WHERE clinic_id = ?", (DEMO_CLINIC_ID,)).fetchone()[0]
    if count:
        return

    common = {
        "age_group": "40_64",
        "reason_for_visit": "Routine check-up. Fictional example only.",
        "allergy_status": "no",
        "allergy_details": "",
        "medication_status": "no",
        "medication_details": "",
        "antibiotic_status": "no",
        "antibiotic_details": "",
        "condition_status": "no",
        "condition_details": "",
        "surgery_status": "no",
        "surgery_details": "",
        "anesthesia_reaction_status": "no",
        "anesthesia_details": "",
        "symptom_duration": "",
        "dental_history": "Fictional demo entry.",
    }
    needs_review = dict(common)
    needs_review.update({
        "patient_label": "Demo Patient Alex",
        "reason_for_visit": "Tooth discomfort; fictional demonstration text.",
        "allergy_status": "yes",
        "allergy_details": "Fictional allergy A. Placeholder reaction details, not a real patient record.",
        "medication_status": "yes",
        "medication_details": "Fictional medication A. Placeholder dose and frequency.",
        "antibiotic_status": "unsure",
        "antibiotic_details": "",
        "condition_status": "no",
    })
    clarification = dict(common)
    clarification.update({
        "patient_label": "Test Patient Jordan",
        "reason_for_visit": "New-patient consultation. Fictional example only.",
        "allergy_status": "unsure",
        "medication_status": "unsure",
        "antibiotic_status": "no",
        "condition_status": "yes",
        "condition_details": "Fictional chronic condition A. Placeholder text.",
    })
    complete = dict(common)
    complete.update({
        "patient_label": "Sample Patient Morgan",
        "reason_for_visit": "Routine cleaning. Fictional example only.",
        "dental_history": "Fictional past cleaning; no real patient details.",
    })
    first = create_intake(db_path, needs_review)
    second = create_intake(db_path, clarification)
    third = create_intake(db_path, complete)
    review_intake(db_path, second["id"], "Demo Clinician", "needs_clarification", "Synthetic example: confirm unknown history.")
    review_intake(db_path, third["id"], "Demo Clinician", "reviewed", "Synthetic example: reviewed for UI demonstration.")
