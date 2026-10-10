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
"""


class TenantMismatchError(PermissionError):
    pass


class ClinicalStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(SCHEMA)

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
    def save_submission(
        self, clinic_id: str, bank_id: str, bank_version: str,
        patient_ref: str, answers: dict[str, Any], actor: str = "patient",
    ) -> str:
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
        row = self._db.execute(
            "SELECT * FROM intake_submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"submission {submission_id} not found")
        if row["clinic_id"] != clinic_id:
            # Cross-tenant access denied — and we audit the attempt.
            self._audit(clinic_id, "system", "access.denied", submission_id,
                        "cross-tenant read attempt")
            self._db.commit()
            raise TenantMismatchError("submission belongs to a different clinic")
        return _row_to_submission(row)

    def list_submissions(self, clinic_id: str, limit: int = 50) -> list[dict[str, Any]]:
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
        review_id = "rev_" + uuid.uuid4().hex[:12]
        self._db.execute(
            """INSERT INTO reviews
               (review_id, submission_id, clinic_id, reviewer, decision, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (review_id, submission_id, clinic_id, reviewer, decision, note, time.time()),
        )
        self._db.execute(
            "UPDATE intake_submissions SET status = ?, updated_at = ? WHERE submission_id = ?",
            ("reviewed:" + decision, time.time(), submission_id),
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
        old_value = str(sub["answers"].get(qid, ""))
        correction_id = "cor_" + uuid.uuid4().hex[:12]
        self._db.execute(
            """INSERT INTO corrections
               (correction_id, submission_id, clinic_id, qid, old_value,
                new_value, source, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (correction_id, submission_id, clinic_id, qid, old_value,
             new_value, source, author, time.time()),
        )
        self._audit(clinic_id, author, "answer.corrected", submission_id,
                    f"{qid}: {old_value[:40]} -> {new_value[:40]} (source={source})")
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
