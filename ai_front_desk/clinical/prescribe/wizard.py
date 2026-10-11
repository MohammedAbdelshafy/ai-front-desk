"""Guided question wizard — walks the dentist through the right questions
in order BEFORE any safety check runs.

Steps: indication -> patient factors -> allergies -> medications ->
conditions -> summary (editable, missing-info flags) -> choose prescription
-> safety check.

The wizard NEVER selects a prescription. It gathers context, presents
cited reference options, and hands the dentist's explicit choice to the
checker. Unknown safety answers stay "cannot verify", never green.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from .reference_data import INDICATIONS, INDICATION_ORDER

STEPS = ["indication", "factors", "allergies", "medications", "conditions", "summary", "choose"]

# Steps that must be POST-completed (in order) before finish is allowed.
# summary/choose are GET review pages gated on the five POST steps.
STEPS_REQUIRED = ["indication", "factors", "allergies", "medications", "conditions"]

UNKNOWN = "don't know"
NA = "not applicable"

AGE_BANDS = ["18–30", "31–50", "51–70", "70+", UNKNOWN, NA]
YES_NO_UNK = ["yes", "no", UNKNOWN, NA]

CONDITION_CHECKLIST = [
    "hypertension",
    "diabetes",
    "heart disease",
    "bleeding disorder",
    "chronic kidney disease",
    "renal impairment",
    "liver disease",
    "stomach ulcer",
    "gastrointestinal bleeding",
    "asthma",
    "immune suppression",
    "pregnancy",
]


def new_wizard(clinic_id: str, patient: dict | None = None) -> dict:
    """Create wizard state, pre-filled from an existing patient record."""
    state: dict[str, Any] = {
        "token": f"wz_{uuid.uuid4().hex[:12]}",
        "clinic_id": clinic_id,
        "patient_id": patient["patient_id"] if patient else None,
        "patient_label": patient["label"] if patient else "",
        "created_at": time.time(),
        "indication": "",
        "indication_notes": "",
        "factors": {
            "age_band": "",
            "pregnancy": "",
            "lactation": "",
            "renal": "",
            "hepatic": "",
            "weight_kg": "",
        },
        "allergies": [dict(a) for a in (patient.get("allergies") or [])] if patient else [],
        "no_known_allergies": bool(patient and patient.get("no_known_allergies")),
        "latex_allergy": "",
        "anesthesia_history": "",
        "meds": [dict(m) for m in (patient.get("current_meds") or [])] if patient else [],
        "conditions": list(patient.get("conditions") or []) if patient else [],
        # Correctness tracking (server-enforced, never trusted from client):
        "steps_done": [],          # POST-completed steps, in order
        "finished_check_id": None,  # set once by finish; double-finish is idempotent
    }
    return state


def step_is_unlocked(state: dict, step: str) -> bool:
    """Can this step be viewed/submitted? All earlier POST steps must be done."""
    if step not in STEPS:
        return False
    idx = STEPS.index(step)
    done = state.get("steps_done") or []
    for earlier in STEPS[:idx]:
        if earlier in STEPS_REQUIRED and earlier not in done:
            return False
    return True


def first_incomplete_step(state: dict) -> str:
    """First required step not yet completed (for redirects)."""
    done = state.get("steps_done") or []
    for s in STEPS_REQUIRED:
        if s not in done:
            return s
    return "summary"


def can_finish(state: dict) -> tuple[bool, str]:
    """Are the finish *preconditions* met? Returns (ok, reason).

    This checks steps + indication only. Idempotency (already finished /
    finish in progress) is handled by the server before calling this —
    see the finish branch in server.py.
    """
    done = state.get("steps_done") or []
    missing = [s for s in STEPS_REQUIRED if s not in done]
    if missing:
        return False, f"steps not completed: {', '.join(missing)}"
    if not (state.get("indication") or "").strip():
        return False, "indication is required"
    return True, ""


class WizardSessions:
    """In-memory wizard state (demo). Server-side; nothing lives in the client."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, dict] = {}

    def create(self, clinic_id: str, patient: dict | None = None) -> dict:
        state = new_wizard(clinic_id, patient)
        with self._lock:
            self._sessions[state["token"]] = state
        return state

    def get(self, token: str) -> dict | None:
        with self._lock:
            return self._sessions.get(token)

    def update(self, token: str, patch: dict) -> dict | None:
        with self._lock:
            state = self._sessions.get(token)
            if state is None:
                return None
            state.update(patch)
            return state

    def complete_step(self, token: str, step: str) -> dict | None:
        """Mark a POST step done (idempotent, order-preserving)."""
        with self._lock:
            state = self._sessions.get(token)
            if state is None:
                return None
            done = state.setdefault("steps_done", [])
            if step not in done:
                done.append(step)
            return state

    def claim_finish(self, token: str) -> tuple[bool, str | None]:
        """Atomically claim the finish for a wizard.

        Returns (claimed, existing_check_id). Only the first caller gets
        claimed=True; every later double-submit gets the existing check id.
        This is what makes double-finish idempotent under concurrency.
        """
        with self._lock:
            state = self._sessions.get(token)
            if state is None:
                return False, None
            existing = state.get("finished_check_id")
            if existing:
                return False, existing
            # Reserve the slot so a concurrent second finish sees it taken.
            state["finished_check_id"] = "PENDING"
            return True, None

    def set_finished(self, token: str, check_id: str) -> None:
        with self._lock:
            state = self._sessions.get(token)
            if state is not None:
                state["finished_check_id"] = check_id

    def release_finish_claim(self, token: str) -> None:
        """Release a PENDING claim if check creation failed (allows retry)."""
        with self._lock:
            state = self._sessions.get(token)
            if state is not None and state.get("finished_check_id") == "PENDING":
                state["finished_check_id"] = None


def missing_info_flags(state: dict, drug_key: str | None = None,
                       drug_classes: list[str] | None = None) -> list[dict]:
    """Flags for answers that could materially affect safety.

    Never presented as verified-safe; these ride along as info flags on the
    check result so the dentist sees exactly what is still unknown.
    """
    flags: list[dict] = []
    f = state.get("factors", {})
    allergies = state.get("allergies") or []

    if not allergies and not state.get("no_known_allergies"):
        flags.append({
            "severity": "info",
            "reason": "Drug-allergy history not recorded in this check — safety cannot be fully verified.",
            "source": "guided check — missing data",
            "rule_id": None,
        })
    if f.get("pregnancy") in ("", UNKNOWN):
        flags.append({
            "severity": "info",
            "reason": "Pregnancy status unknown — confirm before prescribing drugs contraindicated in pregnancy (e.g. tetracyclines).",
            "source": "guided check — missing data",
            "rule_id": None,
        })
    if f.get("renal") in ("", UNKNOWN):
        flags.append({
            "severity": "info",
            "reason": "Renal status unknown — NSAIDs and dose adjustments depend on it.",
            "source": "guided check — missing data",
            "rule_id": None,
        })
    if not state.get("indication"):
        flags.append({
            "severity": "info",
            "reason": "No indication recorded — the check ran without indication-specific guidance.",
            "source": "guided check — missing data",
            "rule_id": None,
        })
    return flags


def build_patient_context(state: dict) -> dict:
    """Merge wizard answers into a patient-shaped dict for the checker."""
    conditions = list(state.get("conditions") or [])
    f = state.get("factors", {})
    if f.get("pregnancy") == "yes" and "pregnancy" not in conditions:
        conditions.append("pregnancy")
    if f.get("renal") == "yes":
        conditions.append("renal impairment")
    if f.get("hepatic") == "yes":
        conditions.append("liver disease")
    allergies = list(state.get("allergies") or [])
    latex = (state.get("latex_allergy") or "").strip().lower()
    if latex == "yes":
        allergies.append({"substance": "latex", "reaction": "not recorded",
                          "recorded_at": "wizard"})
    return {
        "allergies": allergies,
        "no_known_allergies": bool(state.get("no_known_allergies")),
        "conditions": conditions,
        "current_meds": list(state.get("meds") or []),
        "reports": {},
    }


def indication_options() -> list[tuple[str, str]]:
    return [(key, INDICATIONS[key]["display"]) for key in INDICATION_ORDER]
