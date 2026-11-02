"""Prescribing-safety check engine — assistive only.

Given a patient record and an intended prescription, returns a verdict
(GREEN / YELLOW / RED / CANNOT_VERIFY) plus a list of flags. Every flag
cites its source: the patient record or the reference dataset. No silent
inference is ever presented as fact.

Verdict rules:
- Any RED flag -> RED.
- Else any YELLOW flag -> YELLOW.
- Else, if the drug is known and allergy history is recorded -> GREEN.
- Allergy history unknown, or drug not in reference -> CANNOT_VERIFY.
  The app never returns GREEN on missing data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .reference_data import (
    DRUGS,
    RULES,
    COUNSEL_FLAGS,
    REFERENCE_VERSION,
    REFERENCE_DATE,
    lookup_drug,
    med_class,
)

REFERENCE_TAG = f"{REFERENCE_VERSION} ({REFERENCE_DATE})"


@dataclass
class Flag:
    severity: str  # "red" | "yellow" | "info"
    reason: str
    source: str  # e.g. "patient record — allergy" or "reference v2 (2026-10-11) — ..."
    rule_id: str | None = None  # reference rule id, when the flag comes from RULES


@dataclass
class CheckResult:
    verdict: str  # "GREEN" | "YELLOW" | "RED" | "CANNOT_VERIFY"
    flags: list[Flag] = field(default_factory=list)
    drug_key: str | None = None
    drug_display: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "drug_key": self.drug_key,
            "drug_display": self.drug_display,
            "flags": [
                {
                    "severity": f.severity,
                    "reason": f.reason,
                    "source": f.source,
                    "rule_id": f.rule_id,
                }
                for f in self.flags
            ],
        }


def _norm(text: str) -> str:
    return text.strip().lower()


def _patient_allergies(patient: dict) -> list[dict]:
    return patient.get("allergies") or []


def _patient_conditions(patient: dict) -> list[str]:
    return [_norm(c) for c in (patient.get("conditions") or [])]


def _patient_meds(patient: dict) -> list[dict]:
    return patient.get("current_meds") or []


def allergy_status(patient: dict) -> str:
    """'recorded' | 'none_reported' | 'unknown'.

    'recorded'  — at least one allergy entry exists.
    'none_reported' — the record explicitly states no known allergies.
    'unknown' — nothing recorded; checks cannot be GREEN.
    """
    if _patient_allergies(patient):
        return "recorded"
    if patient.get("no_known_allergies"):
        return "none_reported"
    return "unknown"


def _allergy_flags(drug_key: str, entry: dict, patient: dict) -> list[Flag]:
    flags: list[Flag] = []
    for allergy in _patient_allergies(patient):
        substance = _norm(allergy.get("substance", ""))
        if not substance:
            continue
        recorded = allergy.get("recorded_at") or "date not recorded"
        # Exact substance match against the drug name or its aliases.
        names = {_norm(drug_key), _norm(entry["display"])} | {
            _norm(a) for a in entry["aliases"]
        }
        if substance in names:
            flags.append(
                Flag(
                    "red",
                    f"Recorded allergy to {allergy.get('substance')} "
                    f"({allergy.get('reaction', 'reaction not recorded')}) — "
                    f"recorded {recorded}.",
                    "patient record — allergy",
                )
            )
            continue
        # Penicillin allergy vs penicillin-class drugs.
        if substance == "penicillin" and "penicillin" in entry["classes"]:
            flags.append(
                Flag(
                    "red",
                    f"Recorded penicillin allergy ({allergy.get('reaction', 'reaction not recorded')}) "
                    f"— {entry['display']} is a penicillin. Recorded {recorded}.",
                    "patient record — allergy",
                )
            )
    return flags


def _rule_matches(rule: dict, drug_key: str, entry: dict, patient: dict) -> Flag | None:
    match = rule["match"]
    against = rule["against"]

    # --- does the intended drug match the rule trigger? ---
    if "drug" in match and match["drug"] != drug_key:
        return None
    if "drug_class" in match and match["drug_class"] not in entry["classes"]:
        return None

    # --- does the patient match the "against" side? ---
    hit_detail = ""
    if "med" in against:
        for med in _patient_meds(patient):
            if _norm(med.get("name", "")) == _norm(against["med"]):
                hit_detail = f"current medication: {med.get('name')}"
                break
        else:
            return None
    elif "med_class" in against:
        for med in _patient_meds(patient):
            if med_class(med.get("name", "")) == against["med_class"]:
                hit_detail = f"current medication: {med.get('name')} ({against['med_class']})"
                break
        else:
            return None
    elif "condition" in against:
        if _norm(against["condition"]) not in _patient_conditions(patient):
            return None
        hit_detail = f"recorded condition: {against['condition']}"
    elif "reports" in against:
        reports = patient.get("reports") or {}
        if not reports.get(against["reports"]):
            return None
        hit_detail = f"patient-reported: {against['reports'].replace('_', ' ')}"
    elif "allergy" in against:
        for allergy in _patient_allergies(patient):
            if _norm(allergy.get("substance", "")) == _norm(against["allergy"]):
                hit_detail = f"recorded allergy: {allergy.get('substance')}"
                break
        else:
            return None
    else:
        return None

    return Flag(
        rule["severity"],
        f"{rule['reason']} (patient: {hit_detail}).",
        f"{REFERENCE_TAG} — {rule['source'].split('—', 1)[-1].strip()}"
        if "—" in rule["source"]
        else f"{REFERENCE_TAG} — {rule['source']}",
        rule_id=rule["id"],
    )


def check_prescription(patient: dict, intended: dict) -> CheckResult:
    """Run the safety check.

    intended: {"drug_name": str, "strength_mg": float|None,
               "times_per_day": float|None, "duration": str|None, "reason": str|None}
    """
    drug_name = (intended.get("drug_name") or "").strip()
    drug_key, entry = lookup_drug(drug_name)
    result = CheckResult(verdict="CANNOT_VERIFY", drug_key=drug_key)

    if entry is None:
        result.flags.append(
            Flag(
                "info",
                f"'{drug_name}' is not in {REFERENCE_VERSION} — cannot verify safety. "
                "Ask the dentist to check a full reference.",
                f"{REFERENCE_TAG} — coverage",
            )
        )
        return result
    result.drug_display = entry["display"]

    # Allergy data must exist before anything can be GREEN.
    status = allergy_status(patient)
    if status == "unknown":
        result.flags.append(
            Flag(
                "info",
                "Allergy history is not recorded for this patient — "
                "cannot verify safety. Record allergies (or confirm none) first.",
                "patient record — missing data",
            )
        )
        # Still surface any flags we can compute from meds/conditions.
        for flag in _allergy_flags(drug_key, entry, patient):
            result.flags.append(flag)
        for rule in RULES:
            flag = _rule_matches(rule, drug_key, entry, patient)
            if flag:
                result.flags.append(flag)
        _apply_dose_check(result, entry, intended)
        _apply_counsel(result, drug_key)
        result.verdict = _verdict(result.flags, allow_green=False)
        return result

    # Full check.
    result.flags.extend(_allergy_flags(drug_key, entry, patient))
    for rule in RULES:
        flag = _rule_matches(rule, drug_key, entry, patient)
        if flag:
            result.flags.append(flag)
    _apply_dose_check(result, entry, intended)
    _apply_counsel(result, drug_key)
    result.verdict = _verdict(result.flags, allow_green=True)
    return result


def _apply_dose_check(result: CheckResult, entry: dict, intended: dict) -> None:
    try:
        strength = float(intended.get("strength_mg") or 0)
        times = float(intended.get("times_per_day") or 0)
    except (TypeError, ValueError):
        return
    if strength <= 0 or times <= 0:
        return
    daily = strength * times
    max_daily = entry.get("max_daily_mg")
    if max_daily and daily > max_daily:
        result.flags.append(
            Flag(
                "red",
                f"Intended {daily:g} mg/day exceeds the reference maximum of "
                f"{max_daily:g} mg/day for {entry['display']}.",
                f"{REFERENCE_TAG} — dosing",
            )
        )


def _apply_counsel(result: CheckResult, drug_key: str) -> None:
    note = COUNSEL_FLAGS.get(drug_key)
    if note:
        result.flags.append(Flag("info", note, f"{REFERENCE_TAG} — counselling"))


def _verdict(flags: list[Flag], allow_green: bool) -> str:
    if any(f.severity == "red" for f in flags):
        return "RED"
    if any(f.severity == "yellow" for f in flags):
        return "YELLOW"
    if not allow_green:
        return "CANNOT_VERIFY"
    return "GREEN"
