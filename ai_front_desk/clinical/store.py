"""SQLite clinical store: tenant-isolated persistence + append-only audit log.

Design rules:
- Every row carries a tenant_id (clinic_id). Every query filters by it.
- tenant_id is passed by the server from authenticated routing, never taken
  from patient-supplied input.
- Audit log is append-only: who did what to which record, when.
- Synthetic data only unless the deployment configures a real backend.
- This is a local-dev store, not a HIPAA-compliant EHR. Medplum remains the
  leading production candidate (see docs/adr/001-clinical-data-store.md).
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS clinics (
    clinic_id   TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS intake_submissions (
    submission_id TEXT PRIMARY KEY,
    clinic_id     TEXT NOT NULL,
    bank_id       TEXT NOT NULL,
    bank_version  TEXT NOT NULL,
    patient_ref   TEXT NOT NULL,
    answers_json  TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'submitted',
    created_at    REAL NOT NULL,
    updated_at    REAL NOT NULL,
    FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id)
);
CREATE INDEX IF NOT EXISTS idx_sub_clinic ON intake_submissions(clinic_id);
CREATE TABLE IF NOT EXISTS reviews (
    review_id     TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    clinic_id     TEXT NOT NULL,
    reviewer      TEXT NOT NULL,
    decision      TEXT NOT NULL,
    note          TEXT NOT NULL DEFAULT '',
    created_at    REAL NOT NULL,
    FOREIGN KEY (submission_id) REFERENCES intake_submissions(submission_id)
);
CREATE TABLE IF NOT EXISTS corrections (
    correction_id TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    clinic_id     TEXT NOT NULL,
    qid           TEXT NOT NULL,
    old_value     TEXT NOT NULL,
    new_value     TEXT NOT NULL,
    source        TEXT NOT NULL,
    author        TEXT NOT NULL,
    created_at    REAL NOT NULL,
    FOREIGN KEY (submission_id) REFERENCES intake_submissions(submission_id)
);
CREATE TABLE IF NOT EXISTS audit_log (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id  TEXT NOT NULL,
    actor      TEXT NOT NULL,
    action     TEXT NOT NULL,
    target     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS operational_events (
    event_id        TEXT PRIMARY KEY,
    clinic_id       TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    source          TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    occurred_at     REAL NOT NULL,
    created_at      REAL NOT NULL,
    actor           TEXT NOT NULL,
    UNIQUE (clinic_id, idempotency_key),
    FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id)
);
CREATE INDEX IF NOT EXISTS idx_operational_events_clinic_time
    ON operational_events(clinic_id, occurred_at);
"""


class TenantMismatchError(PermissionError):
    pass


class OperationalEventConflictError(ValueError):
    """Raised when an idempotency key is reused for a different event payload."""
    pass


OPERATIONAL_EVENT_TYPES = (
    "new_inquiry_received",
    "missed_call",
    "missed_call_recovered",
    "appointment_booked",
    "appointment_attended",
    "appointment_cancelled",
    "no_show",
    "no_show_followup_completed",
    "intake_started",
    "intake_completed",
    "intake_reviewed",
    "staff_task_opened",
    "staff_task_completed",
    "marketing_lead_received",
    "new_patient_attended",
    "recall_booked",
)

OPERATIONAL_EVENT_SOURCES = {
    "staff", "system", "website", "phone", "sms", "whatsapp",
    "marketing", "pms", "demo_synthetic",
}
OPERATIONAL_IDEMPOTENCY_KEY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,99}\\Z")


class ClinicalStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        existed = self.path.exists()
        self._db = sqlite3.connect(str(self.path), timeout=5.0, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA busy_timeout = 5000")
        self._db.executescript(SCHEMA)
        if not existed:
            try:
                self.path.chmod(0o600)
            except OSError:
                # Windows or restricted filesystems may not implement POSIX modes.
                pass

    def close(self):
        self._db.close()

    # -- clinics ---------------------------------------------------------
    def register_clinic(self, clinic_id: str, name: str) -> None:
        now = time.time()
        self._db.execute(
            "INSERT OR IGNORE INTO clinics (clinic_id, name, created_at) VALUES (?, ?, ?)",
            (clinic_id, name, now),
        )
        self._db.commit()

    # -- submissions ------------------------------------------------------
    def is_registered_clinic(self, clinic_id: str) -> bool:
        row = self._db.execute(
            "SELECT 1 FROM clinics WHERE clinic_id = ?", (clinic_id,)
        ).fetchone()
        return row is not None

    def save_submission(
        self, clinic_id: str, bank_id: str, bank_version: str,
        patient_ref: str, answers: dict[str, Any], actor: str = "patient",
    ) -> str:
        if not self.is_registered_clinic(clinic_id):
            self._audit(clinic_id, "system", "submission.denied", "", "unknown clinic")
            self._db.commit()
            raise TenantMismatchError("unknown clinic")
        if not isinstance(patient_ref, str) or not patient_ref.strip() or len(patient_ref) > 80:
            raise ValueError("patient reference must be non-empty text of at most 80 characters")
        if not isinstance(answers, dict):
            raise ValueError("answers must be an object")
        submission_id = "sub_" + uuid.uuid4().hex[:12]
        now = time.time()
        self._db.execute(
            """INSERT INTO intake_submissions
               (submission_id, clinic_id, bank_id, bank_version, patient_ref,
                answers_json, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'submitted', ?, ?)""",
            (submission_id, clinic_id, bank_id, bank_version, patient_ref,
             json.dumps(answers), now, now),
        )
        self._audit(clinic_id, actor, "submission.created", submission_id,
                    f"bank={bank_id}@{bank_version}")
        self._db.commit()
        return submission_id

    def get_submission(self, clinic_id: str, submission_id: str) -> dict[str, Any]:
        # The primary record query is tenant-scoped. Do not load answers from
        # another tenant before checking ownership.
        row = self._db.execute(
            "SELECT * FROM intake_submissions WHERE submission_id = ? AND clinic_id = ?",
            (submission_id, clinic_id),
        ).fetchone()
        if row is not None:
            return _row_to_submission(row)

        owner = self._db.execute(
            "SELECT clinic_id FROM intake_submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if owner is not None and owner["clinic_id"] != clinic_id:
            self._audit(clinic_id, "system", "access.denied", submission_id,
                        "cross-tenant read attempt")
            self._db.commit()
            raise TenantMismatchError("submission belongs to a different clinic")
        raise KeyError(f"submission {submission_id} not found")

    def list_submissions(self, clinic_id: str, limit: int = 50) -> list[dict[str, Any]]:
        try:
            limit = max(1, min(int(limit), 200))
        except (TypeError, ValueError):
            limit = 50
        rows = self._db.execute(
            """SELECT * FROM intake_submissions WHERE clinic_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (clinic_id, limit),
        ).fetchall()
        return [_row_to_submission(r) for r in rows]

    # -- reviews -----------------------------------------------------------
    def record_review(
        self, clinic_id: str, submission_id: str, reviewer: str,
        decision: str, note: str = "",
    ) -> str:
        self.get_submission(clinic_id, submission_id)  # enforces tenant
        if decision not in ("approved", "needs_clarification", "flagged"):
            raise ValueError(f"unknown review decision: {decision}")
        if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 120:
            raise ValueError("reviewer label must be 1–120 characters")
        if not isinstance(note, str) or len(note) > 2000:
            raise ValueError("review note must be text of at most 2000 characters")
        review_id = "rev_" + uuid.uuid4().hex[:12]
        self._db.execute(
            """INSERT INTO reviews
               (review_id, submission_id, clinic_id, reviewer, decision, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (review_id, submission_id, clinic_id, reviewer, decision, note, time.time()),
        )
        self._db.execute(
            """UPDATE intake_submissions SET status = ?, updated_at = ?
               WHERE submission_id = ? AND clinic_id = ?""",
            ("reviewed:" + decision, time.time(), submission_id, clinic_id),
        )
        self._audit(clinic_id, reviewer, "submission.reviewed", submission_id,
                    f"decision={decision}")
        self._db.commit()
        return review_id

    # -- corrections --------------------------------------------------------
    def record_correction(
        self, clinic_id: str, submission_id: str, qid: str,
        new_value: str, source: str, author: str,
    ) -> str:
        sub = self.get_submission(clinic_id, submission_id)  # enforces tenant
        if not isinstance(qid, str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,99}", qid):
            raise ValueError("invalid question identifier")
        if not isinstance(new_value, str) or len(new_value) > 5000:
            raise ValueError("correction must be text of at most 5000 characters")
        if source not in ("staff_verified", "patient_correction"):
            raise ValueError("unknown correction source")
        if not isinstance(author, str) or not author.strip() or len(author) > 120:
            raise ValueError("author label must be 1–120 characters")
        latest = self._db.execute(
            """SELECT new_value FROM corrections
               WHERE submission_id = ? AND clinic_id = ? AND qid = ?
               ORDER BY rowid DESC LIMIT 1""",
            (submission_id, clinic_id, qid),
        ).fetchone()
        old_value = (
            str(latest["new_value"]) if latest is not None
            else str(sub["answers"].get(qid, ""))
        )
        correction_id = "cor_" + uuid.uuid4().hex[:12]
        created_at = time.time()
        self._db.execute(
            """INSERT INTO corrections
               (correction_id, submission_id, clinic_id, qid, old_value,
                new_value, source, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (correction_id, submission_id, clinic_id, qid, old_value,
             new_value, source, author, created_at),
        )
        # Keep health values in the corrections table, not duplicated in audit logs.
        self._audit(clinic_id, author, "answer.corrected", submission_id,
                    f"qid={qid}; source={source}")
        self._db.commit()
        return correction_id

    def list_corrections(self, clinic_id: str, submission_id: str) -> list[dict[str, Any]]:
        self.get_submission(clinic_id, submission_id)  # enforces tenant
        rows = self._db.execute(
            """SELECT * FROM corrections WHERE submission_id = ? AND clinic_id = ?
               ORDER BY created_at""",
            (submission_id, clinic_id),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- operational event ledger -------------------------------------------
    def record_operational_event(
        self, clinic_id: str, event_type: str, *, source: str,
        idempotency_key: str, occurred_at: float | None = None,
        actor: str = "system",
    ) -> str:
        """Append a count-only operational event and return its stable event ID.

        Do not pass patient identifiers, message text, phone numbers, diagnoses,
        or other clinical details. Use an opaque idempotency key generated by
        the calling integration. Replays of the same event type/source are safe.
        """
        if not self.is_registered_clinic(clinic_id):
            raise TenantMismatchError("unknown clinic")
        if event_type not in OPERATIONAL_EVENT_TYPES:
            raise ValueError(f"unknown operational event type: {event_type}")
        if source not in OPERATIONAL_EVENT_SOURCES:
            raise ValueError(f"unknown operational event source: {source}")
        if (not isinstance(idempotency_key, str)
                or not OPERATIONAL_IDEMPOTENCY_KEY_RE.fullmatch(idempotency_key)):
            raise ValueError("idempotency key must be an opaque 1–100 character token")
        if not isinstance(actor, str) or not actor.strip() or len(actor) > 120:
            raise ValueError("actor label must be 1–120 characters")
        if occurred_at is None:
            occurred_at = time.time()
        if isinstance(occurred_at, bool) or not isinstance(occurred_at, (int, float)):
            raise ValueError("occurred_at must be a numeric Unix timestamp")
        occurred_at = float(occurred_at)
        if not 0 < occurred_at < float("inf"):
            raise ValueError("occurred_at must be a finite positive Unix timestamp")

        existing = self._db.execute(
            """SELECT event_id, event_type, source FROM operational_events
               WHERE clinic_id = ? AND idempotency_key = ?""",
            (clinic_id, idempotency_key),
        ).fetchone()
        if existing is not None:
            if existing["event_type"] != event_type or existing["source"] != source:
                raise OperationalEventConflictError(
                    "idempotency key already belongs to a different event payload"
                )
            return str(existing["event_id"])

        event_id = "evt_" + uuid.uuid4().hex[:12]
        created_at = time.time()
        self._db.execute(
            """INSERT INTO operational_events
               (event_id, clinic_id, event_type, source, idempotency_key,
                occurred_at, created_at, actor)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, clinic_id, event_type, source, idempotency_key,
             occurred_at, created_at, actor.strip()),
        )
        # The audit trail stores only event classification, never the idempotency
        # key, patient data, or message contents.
        self._audit(clinic_id, actor.strip(), "operational_event.recorded", event_id,
                    f"type={event_type}; source={source}")
        self._db.commit()
        return event_id

    def list_operational_events(
        self, clinic_id: str, start_at: float | None = None,
        end_at: float | None = None,
    ) -> list[dict[str, Any]]:
        """Return count-only event metadata for one clinic and optional time window."""
        if not self.is_registered_clinic(clinic_id):
            raise TenantMismatchError("unknown clinic")
        clauses = ["clinic_id = ?"]
        params: list[Any] = [clinic_id]
        if start_at is not None:
            clauses.append("occurred_at >= ?")
            params.append(float(start_at))
        if end_at is not None:
            clauses.append("occurred_at < ?")
            params.append(float(end_at))
        rows = self._db.execute(
            "SELECT event_id, clinic_id, event_type, source, occurred_at, created_at, actor "
            "FROM operational_events WHERE " + " AND ".join(clauses) +
            " ORDER BY occurred_at, event_id",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def daily_scorecard(
        self, clinic_id: str, start_at: float, end_at: float,
    ) -> dict[str, Any]:
        """Aggregate observed event counts without inventing conversion or ROI rates."""
        if not self.is_registered_clinic(clinic_id):
            raise TenantMismatchError("unknown clinic")
        if (isinstance(start_at, bool) or isinstance(end_at, bool)
                or not isinstance(start_at, (int, float))
                or not isinstance(end_at, (int, float))
                or not float(start_at) < float(end_at)):
            raise ValueError("scorecard requires a valid increasing timestamp window")

        rows = self._db.execute(
            """SELECT event_type, source, COUNT(*) AS event_count
               FROM operational_events
               WHERE clinic_id = ? AND occurred_at >= ? AND occurred_at < ?
               GROUP BY event_type, source""",
            (clinic_id, float(start_at), float(end_at)),
        ).fetchall()
        counts = {event_type: 0 for event_type in OPERATIONAL_EVENT_TYPES}
        event_count = 0
        synthetic_count = 0
        for row in rows:
            counts[row["event_type"]] = counts.get(row["event_type"], 0) + int(row["event_count"])
            event_count += int(row["event_count"])
            if row["source"] == "demo_synthetic":
                synthetic_count += int(row["event_count"])

        if event_count == 0:
            data_mode = "no_events"
        elif synthetic_count == event_count:
            data_mode = "synthetic_demo"
        elif synthetic_count:
            data_mode = "mixed_demo_and_operational"
        else:
            data_mode = "operational_events"

        return {
            "clinic_id": clinic_id,
            "period_start": float(start_at),
            "period_end": float(end_at),
            "event_count": event_count,
            "counts": counts,
            "synthetic_event_count": synthetic_count,
            "data_mode": data_mode,
            "limitations": [
                "Counts reflect recorded events in this time window; unrecorded work is not included.",
                "Counts alone do not establish cause, recovered revenue, or clinical outcomes.",
                "Bookings and attendances are separate daily counts; no cohort conversion rate is calculated.",
                "Synthetic demo events are labeled and must never be presented as clinic results.",
            ],
        }

    # -- audit ---------------------------------------------------------------
    def _audit(self, clinic_id: str, actor: str, action: str, target: str, detail: str = ""):
        self._db.execute(
            """INSERT INTO audit_log (clinic_id, actor, action, target, detail, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (clinic_id, actor, action, target, detail, time.time()),
        )

    def audit_trail(self, clinic_id: str, target: str = "") -> list[dict[str, Any]]:
        if target:
            rows = self._db.execute(
                """SELECT * FROM audit_log WHERE clinic_id = ? AND target = ?
                   ORDER BY seq""",
                (clinic_id, target),
            ).fetchall()
        else:
            rows = self._db.execute(
                "SELECT * FROM audit_log WHERE clinic_id = ? ORDER BY seq",
                (clinic_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def _row_to_submission(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "submission_id": row["submission_id"],
        "clinic_id": row["clinic_id"],
        "bank_id": row["bank_id"],
        "bank_version": row["bank_version"],
        "patient_ref": row["patient_ref"],
        "answers": json.loads(row["answers_json"]),
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
