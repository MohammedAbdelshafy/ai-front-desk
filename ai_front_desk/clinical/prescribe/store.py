"""Prescribe store: tenant-isolated patient records + check history + audit.

Every row carries clinic_id; every query filters by it. Same design
rules as the clinical store (see ../store.py). Synthetic demo data only.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class LockedConnection:
    """Thread-safe wrapper around a sqlite3 connection.

    The server is threaded but each store keeps a single shared connection;
    sqlite3 connections must not be used concurrently even with
    check_same_thread=False, so every statement is serialized through one
    re-entrant lock. (See docs/engineering/RELIABILITY.md — Can't lag.)
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._lock = threading.RLock()

    def execute(self, *args, **kwargs):
        with self._lock:
            return self._conn.execute(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        with self._lock:
            return self._conn.executescript(*args, **kwargs)

    def commit(self):
        with self._lock:
            return self._conn.commit()

    def close(self):
        with self._lock:
            return self._conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS prescribe_patients (
    patient_id   TEXT PRIMARY KEY,
    clinic_id    TEXT NOT NULL,
    label        TEXT NOT NULL,
    allergies_json   TEXT NOT NULL DEFAULT '[]',
    conditions_json  TEXT NOT NULL DEFAULT '[]',
    meds_json        TEXT NOT NULL DEFAULT '[]',
    reports_json     TEXT NOT NULL DEFAULT '{}',
    no_known_allergies INTEGER NOT NULL DEFAULT 0,
    created_at   REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ppat_clinic ON prescribe_patients(clinic_id);
CREATE TABLE IF NOT EXISTS prescribe_checks (
    check_id     TEXT PRIMARY KEY,
    clinic_id    TEXT NOT NULL,
    patient_id   TEXT NOT NULL,
    dentist      TEXT NOT NULL DEFAULT '',
    intended_json TEXT NOT NULL,
    verdict      TEXT NOT NULL,
    flags_json   TEXT NOT NULL,
    review_state TEXT NOT NULL DEFAULT 'ready_for_review',
    review_note  TEXT NOT NULL DEFAULT '',
    reviewed_by  TEXT NOT NULL DEFAULT '',
    reviewed_at  REAL,
    created_at   REAL NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES prescribe_patients(patient_id)
);
CREATE INDEX IF NOT EXISTS idx_pchk_clinic ON prescribe_checks(clinic_id);
CREATE INDEX IF NOT EXISTS idx_pchk_patient ON prescribe_checks(patient_id);
CREATE TABLE IF NOT EXISTS prescribe_audit (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id  TEXT NOT NULL,
    actor      TEXT NOT NULL,
    action     TEXT NOT NULL,
    target     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_paudit_clinic_time ON prescribe_audit(clinic_id, created_at);
"""


class TenantMismatchError(PermissionError):
    pass


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PrescribeStore:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        conn = sqlite3.connect(str(self.path), timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self._db = LockedConnection(conn)
        self._db.row_factory = sqlite3.Row
        # Performance + durability pragmas (see docs/engineering/RELIABILITY.md):
        # WAL allows readers during writes; NORMAL is safe with WAL (only a full
        # OS crash could lose the un-checkpointed tail); busy_timeout makes
        # transient write-write contention wait instead of erroring.
        self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("PRAGMA synchronous = NORMAL")
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA busy_timeout = 5000")
        self._db.executescript(SCHEMA)
        self._db.commit()

    def close(self):
        self._db.close()

    # -- patients ------------------------------------------------------
    def add_patient(
        self,
        clinic_id: str,
        label: str,
        allergies: list[dict] | None = None,
        conditions: list[str] | None = None,
        current_meds: list[dict] | None = None,
        reports: dict | None = None,
        no_known_allergies: bool = False,
    ) -> str:
        patient_id = _new_id("pat")
        self._db.execute(
            """INSERT INTO prescribe_patients
               (patient_id, clinic_id, label, allergies_json, conditions_json,
                meds_json, reports_json, no_known_allergies, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                patient_id,
                clinic_id,
                label,
                json.dumps(allergies or []),
                json.dumps(conditions or []),
                json.dumps(current_meds or []),
                json.dumps(reports or {}),
                1 if no_known_allergies else 0,
                time.time(),
            ),
        )
        self._db.commit()
        return patient_id

    def get_patient(self, clinic_id: str, patient_id: str) -> dict[str, Any]:
        row = self._db.execute(
            "SELECT * FROM prescribe_patients WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown patient {patient_id}")
        if row["clinic_id"] != clinic_id:
            raise TenantMismatchError("cross-tenant patient access denied")
        return _row_to_patient(row)

    def list_patients(self, clinic_id: str) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT * FROM prescribe_patients WHERE clinic_id = ? ORDER BY created_at DESC",
            (clinic_id,),
        ).fetchall()
        return [_row_to_patient(r) for r in rows]

    # -- checks --------------------------------------------------------
    def record_check(
        self,
        clinic_id: str,
        patient_id: str,
        dentist: str,
        intended: dict,
        verdict: str,
        flags: list[dict],
        actor: str = "",
    ) -> str:
        # Verify the patient belongs to this clinic first (tenant gate).
        self.get_patient(clinic_id, patient_id)
        check_id = _new_id("chk")
        self._db.execute(
            """INSERT INTO prescribe_checks
               (check_id, clinic_id, patient_id, dentist, intended_json,
                verdict, flags_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                check_id,
                clinic_id,
                patient_id,
                dentist,
                json.dumps(intended),
                verdict,
                json.dumps(flags),
                time.time(),
            ),
        )
        # RED verdicts demand clinician review before anything else happens.
        initial_state = "review_required" if verdict == "RED" else "ready_for_review"
        self._db.execute(
            "UPDATE prescribe_checks SET review_state = ? WHERE check_id = ?",
            (initial_state, check_id),
        )
        self._audit(clinic_id, actor or dentist or "dentist", "prescribe_check", check_id,
                    f"verdict={verdict} patient={patient_id} review_state={initial_state}")
        self._db.commit()
        return check_id

    # -- clinician review ------------------------------------------------
    # States: incomplete -> ready_for_review -> review_required
    #         -> clinician_reviewed | escalated
    # The dentist records their own conclusion; the app never marks a
    # check reviewed on its own. Missing/uncertain data is never shown
    # as verified-safe: checks stay review_required until a clinician acts.
    REVIEW_STATES = (
        "incomplete",
        "ready_for_review",
        "review_required",
        "clinician_reviewed",
        "escalated",
    )

    def set_review_state(
        self,
        clinic_id: str,
        check_id: str,
        state: str,
        by: str,
        note: str = "",
        actor: str = "",
    ) -> None:
        if state not in self.REVIEW_STATES:
            raise ValueError(f"unknown review state {state}")
        row = self._db.execute(
            "SELECT clinic_id FROM prescribe_checks WHERE check_id = ?",
            (check_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown check {check_id}")
        if row["clinic_id"] != clinic_id:
            raise TenantMismatchError("cross-tenant check access denied")
        self._db.execute(
            "UPDATE prescribe_checks SET review_state = ?, review_note = ?, "
            "reviewed_by = ?, reviewed_at = ? WHERE check_id = ?",
            (state, note, by, time.time(), check_id),
        )
        self._audit(
            clinic_id,
            actor or by or "dentist",
            "prescribe_review",
            check_id,
            f"state={state} by={by} note={note[:120]}",
        )
        self._db.commit()

    def get_check(self, clinic_id: str, check_id: str) -> dict[str, Any]:
        row = self._db.execute(
            "SELECT * FROM prescribe_checks WHERE check_id = ?", (check_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown check {check_id}")
        if row["clinic_id"] != clinic_id:
            raise TenantMismatchError("cross-tenant check access denied")
        return {
            "check_id": row["check_id"],
            "patient_id": row["patient_id"],
            "dentist": row["dentist"],
            "intended": json.loads(row["intended_json"]),
            "verdict": row["verdict"],
            "flags": json.loads(row["flags_json"]),
            "review_state": row["review_state"],
            "review_note": row["review_note"],
            "reviewed_by": row["reviewed_by"],
            "reviewed_at": row["reviewed_at"],
            "created_at": row["created_at"],
        }

    def check_history(self, clinic_id: str, patient_id: str) -> list[dict[str, Any]]:
        self.get_patient(clinic_id, patient_id)  # tenant gate
        rows = self._db.execute(
            "SELECT * FROM prescribe_checks WHERE clinic_id = ? AND patient_id = ? "
            "ORDER BY created_at DESC",
            (clinic_id, patient_id),
        ).fetchall()
        return [
            {
                "check_id": r["check_id"],
                "dentist": r["dentist"],
                "intended": json.loads(r["intended_json"]),
                "verdict": r["verdict"],
                "flags": json.loads(r["flags_json"]),
                "review_state": r["review_state"],
                "review_note": r["review_note"],
                "reviewed_by": r["reviewed_by"],
                "reviewed_at": r["reviewed_at"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # -- audit ---------------------------------------------------------
    def _audit(self, clinic_id: str, actor: str, action: str, target: str, detail: str = ""):
        self._db.execute(
            "INSERT INTO prescribe_audit (clinic_id, actor, action, target, detail, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (clinic_id, actor, action, target, detail, time.time()),
        )

    def audit_trail(self, clinic_id: str, target: str = "") -> list[dict[str, Any]]:
        if target:
            rows = self._db.execute(
                "SELECT * FROM prescribe_audit WHERE clinic_id = ? AND target = ? ORDER BY seq",
                (clinic_id, target),
            ).fetchall()
        else:
            rows = self._db.execute(
                "SELECT * FROM prescribe_audit WHERE clinic_id = ? ORDER BY seq",
                (clinic_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def _row_to_patient(row) -> dict[str, Any]:
    return {
        "patient_id": row["patient_id"],
        "clinic_id": row["clinic_id"],
        "label": row["label"],
        "allergies": json.loads(row["allergies_json"]),
        "conditions": json.loads(row["conditions_json"]),
        "current_meds": json.loads(row["meds_json"]),
        "reports": json.loads(row["reports_json"]),
        "no_known_allergies": bool(row["no_known_allergies"]),
    }
