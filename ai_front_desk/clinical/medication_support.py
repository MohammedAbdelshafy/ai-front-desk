"""Source-backed medication review for clinician decision support.

This module does not diagnose, prescribe, rank a single "best" medicine, or
transmit orders. It only exposes candidate teaching cards from an explicitly
approved catalogue when the clinician's diagnosis and required patient facts
match exactly. The default catalogue is empty and not approved.
"""
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SUPPORTED_SPECIALTIES = frozenset({"dentistry", "gynecology"})
UNKNOWN_VALUES = frozenset({"", "unknown", "not known", "not_known", "unsure", "i don't know"})
TEACHING_FIELDS = (
    "why_consider",
    "mechanism",
    "common_adverse_effects",
    "serious_warnings",
    "monitoring",
    "counseling",
    "dose_summary",
)
SOURCE_FIELDS = (
    "title",
    "url",
    "version",
    "effective_date",
    "reviewer",
    "reviewed_at",
    "review_due",
    "review_status",
)
DEFAULT_CATALOG_PATH = Path(__file__).with_name("medication_catalog_v1.json")


def load_medication_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    """Load the curated catalogue without turning a draft into live knowledge.

    The whole catalogue must be approved AND each entry must independently
    pass source and rule validation. An absent/invalid file fails closed.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"catalog_id": "mia-medication-catalog", "version": "unknown",
                "status": "unavailable", "entries": []}
    if not isinstance(raw, dict):
        return {"catalog_id": "mia-medication-catalog", "version": "unknown",
                "status": "unavailable", "entries": []}
    entries = raw.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    if raw.get("status") != "approved":
        entries = []
    return {
        "catalog_id": str(raw.get("catalog_id", "mia-medication-catalog")),
        "version": str(raw.get("version", "unknown")),
        "status": str(raw.get("status", "unavailable")),
        "entries": entries,
    }


def review_medication_options(
    request: dict[str, Any],
    catalog_entries: list[dict[str, Any]] | dict[str, Any] | None,
    *,
    today: str | date | None = None,
) -> dict[str, Any]:
    """Return source-linked options for a clinician to independently review.

    Diagnosis matching is exact. The function is deterministic and does not
    call an LLM, infer a diagnosis, calculate a dose, or issue a prescription.
    """
    result: dict[str, Any] = {
        "status": "no_approved_options",
        "specialty": None,
        "diagnosis_code": None,
        "candidate_options": [],
        "withheld_options": [],
        "missing_context": [],
        "catalog_exclusions": 0,
        "ranking": "none",
        "prescribe_or_order_action": False,
        "clinician_confirmation_required": True,
        "notice": (
            "Clinician decision support only. Review the cited source and the "
            "patient-specific facts independently. This output is not a diagnosis, "
            "prescription, or medication order."
        ),
    }

    if not isinstance(request, dict):
        result["status"] = "blocked_invalid_request"
        return result

    specialty = request.get("specialty")
    if not isinstance(specialty, str) or specialty.strip().casefold() not in SUPPORTED_SPECIALTIES:
        result["status"] = "blocked_invalid_request"
        result["error"] = "specialty must be exactly 'dentistry' or 'gynecology'"
        return result
    specialty = specialty.strip().casefold()
    result["specialty"] = specialty

    diagnosis_code = request.get("diagnosis_code")
    if not isinstance(diagnosis_code, str) or not diagnosis_code.strip():
        result["status"] = "blocked_incomplete_context"
        result["missing_context"] = ["diagnosis_code"]
        return result
    diagnosis_code = diagnosis_code.strip().upper()
    result["diagnosis_code"] = diagnosis_code

    facts = request.get("patient_facts")
    if not isinstance(facts, dict):
        facts = {}

    missing_context: list[str] = []
    age = facts.get("age_years")
    try:
        age_value = float(age) if not isinstance(age, bool) else math.nan
    except (TypeError, ValueError, OverflowError):
        age_value = math.nan
    if not math.isfinite(age_value) or age_value < 0:
        missing_context.append("age_years")
    if facts.get("allergies_reviewed") is not True:
        missing_context.append("allergies_reviewed")
    allergies = facts.get("allergies")
    if not isinstance(allergies, list) or any(not isinstance(x, str) for x in allergies):
        missing_context.append("allergies")
    if specialty == "gynecology":
        for key in ("pregnancy_status", "lactation_status"):
            value = facts.get(key)
            if not isinstance(value, str) or value.strip().casefold() not in {"yes", "no", "not_applicable"}:
                missing_context.append(key)
    if facts.get("current_medications_reviewed") is not True:
        missing_context.append("current_medications_reviewed")
    current_meds = facts.get("current_medications")
    if not isinstance(current_meds, list) or any(not isinstance(x, str) for x in current_meds):
        missing_context.append("current_medications")

    if missing_context:
        result["status"] = "blocked_incomplete_context"
        result["missing_context"] = sorted(set(missing_context))
        return result

    if isinstance(today, date):
        today_date = today
    elif isinstance(today, str):
        try:
            today_date = date.fromisoformat(today)
        except ValueError:
            result["status"] = "blocked_invalid_request"
            result["error"] = "today must be an ISO date (YYYY-MM-DD)"
            return result
    else:
        today_date = date.today()

    if isinstance(catalog_entries, dict):
        if catalog_entries.get("status") != "approved":
            entries: list[Any] = []
            result["catalog_exclusions"] = len(catalog_entries.get("entries", [])) if isinstance(
                catalog_entries.get("entries", []), list
            ) else 0
        else:
            entries = catalog_entries.get("entries", [])
            if not isinstance(entries, list):
                entries = []
    elif isinstance(catalog_entries, list):
        entries = catalog_entries
    else:
        entries = []

    for entry in entries:
        if not isinstance(entry, dict):
            result["catalog_exclusions"] += 1
            continue
        specialties = entry.get("specialties", [])
        diagnoses = entry.get("diagnosis_codes", [])
        if not isinstance(specialties, list) or not isinstance(diagnoses, list):
            result["catalog_exclusions"] += 1
            continue
        if specialty not in [str(s).strip().casefold() for s in specialties]:
            continue
        if diagnosis_code not in [str(d).strip().upper() for d in diagnoses]:
            continue

        source = entry.get("source")
        if not _valid_source(source, today_date):
            result["catalog_exclusions"] += 1
            continue
        teaching = entry.get("teaching")
        if not _valid_teaching(teaching):
            result["catalog_exclusions"] += 1
            continue

        entry_id = str(entry.get("id", "")).strip()
        generic_name = str(entry.get("generic_name", "")).strip()
        required_facts = entry.get("required_facts", [])
        contraindications = entry.get("contraindications", [])
        interactions = entry.get("interactions", [])
        if (
            not entry_id
            or not generic_name
            or not isinstance(required_facts, list)
            or any(not isinstance(x, str) or not x.strip() for x in required_facts)
            or not isinstance(contraindications, list)
            or not isinstance(interactions, list)
        ):
            result["catalog_exclusions"] += 1
            continue

        missing_facts = sorted({
            key for key in required_facts if _is_unknown(facts.get(key))
        })
        if missing_facts:
            result["withheld_options"].append({
                "id": entry_id,
                "display_name": generic_name,
                "reason_code": "missing_required_fact",
                "missing_facts": missing_facts,
                "message": "Required patient information is unknown or missing; do not use this option until resolved.",
            })
            continue

        bad_rule = False
        contra_match = None
        contraindication_missing: set[str] = set()
        for rule in contraindications:
            if not isinstance(rule, dict) or not isinstance(rule.get("fact"), str) or "equals" not in rule:
                bad_rule = True
                break
            fact_key = rule["fact"]
            actual = facts.get(fact_key)
            if _is_unknown(actual):
                contraindication_missing.add(fact_key)
            elif actual == rule["equals"]:
                contra_match = rule
                break
        if bad_rule:
            result["catalog_exclusions"] += 1
            continue
        if contraindication_missing:
            result["withheld_options"].append({
                "id": entry_id,
                "display_name": generic_name,
                "reason_code": "missing_required_fact",
                "missing_facts": sorted(contraindication_missing),
                "message": "A fact needed to screen a contraindication is missing; do not use this option until resolved.",
            })
            continue
        if contra_match is not None:
            result["withheld_options"].append({
                "id": entry_id,
                "display_name": generic_name,
                "reason_code": "contraindication",
                "message": str(contra_match.get("reason") or "A catalogue contraindication rule matched."),
            })
            continue

        allergy_terms = entry.get("allergy_terms", [])
        if not isinstance(allergy_terms, list) or any(not isinstance(x, str) or not x.strip() for x in allergy_terms):
            result["catalog_exclusions"] += 1
            continue
        reported_allergies = {_normalise_medication(x) for x in allergies if x.strip()}
        matched_allergy = next((term for term in allergy_terms if _normalise_medication(term) in reported_allergies), None)
        if matched_allergy is not None:
            result["withheld_options"].append({
                "id": entry_id,
                "display_name": generic_name,
                "reason_code": "contraindication",
                "message": "A documented allergy matches this entry's reviewed allergy terms; clinician reconciliation is required.",
            })
            continue

        current_med_names = {_normalise_medication(x) for x in current_meds}
        matched_interaction = None
        for rule in interactions:
            if (
                not isinstance(rule, dict)
                or not isinstance(rule.get("medication"), str)
                or not rule["medication"].strip()
            ):
                bad_rule = True
                break
            if _normalise_medication(rule["medication"]) in current_med_names:
                matched_interaction = rule
                break
        if bad_rule:
            result["catalog_exclusions"] += 1
            continue
        if matched_interaction is not None:
            result["withheld_options"].append({
                "id": entry_id,
                "display_name": generic_name,
                "reason_code": "interaction_requires_resolution",
                "severity": str(matched_interaction.get("severity", "unspecified")),
                "message": str(matched_interaction.get("reason") or "A catalogue interaction rule matched."),
            })
            continue

        result["candidate_options"].append({
            "id": entry_id,
            "display_name": generic_name,
            "reasoning_status": "source_backed_option_not_a_final_decision",
            "teaching": {key: str(teaching[key]).strip() for key in TEACHING_FIELDS},
            "source": {key: str(source[key]).strip() for key in SOURCE_FIELDS},
        })

    if result["candidate_options"]:
        result["status"] = "options_for_clinician_review"
    return result


def _is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().casefold() in UNKNOWN_VALUES
    return False


def _normalise_medication(value: str) -> str:
    return " ".join(value.casefold().split())


def _valid_teaching(teaching: Any) -> bool:
    return isinstance(teaching, dict) and all(
        isinstance(teaching.get(key), str) and teaching[key].strip()
        for key in TEACHING_FIELDS
    )


def _valid_source(source: Any, today: date) -> bool:
    if not isinstance(source, dict):
        return False
    if any(not isinstance(source.get(key), str) or not source[key].strip()
           for key in SOURCE_FIELDS):
        return False
    if source.get("review_status") != "approved":
        return False
    parsed_url = urlparse(source["url"])
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        return False
    try:
        effective = date.fromisoformat(source["effective_date"])
        reviewed = date.fromisoformat(source["reviewed_at"])
        due = date.fromisoformat(source["review_due"])
    except ValueError:
        return False
    return effective <= reviewed <= today and due >= today
