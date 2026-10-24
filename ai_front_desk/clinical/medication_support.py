"""Evidence-retrieval foundation for Dr. Mia's clinician-facing workbench.

This module retrieves curator-approved evidence cards and surfaces review prompts.
It does not diagnose, prescribe, calculate doses, perform comprehensive interaction
checks, or conclude that a medicine is safe for a patient. Empty/unapproved
registries fail closed. Use synthetic cases until content is clinically reviewed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
import json
import re

ALLOWED_CONTENT_RIGHTS = {"open", "licensed", "publisher_api", "approved_summary"}
VALID_PATIENT_FACTORS = {
    "age", "allergies", "current_medications", "medical_history",
    "pregnancy_status", "renal_function", "hepatic_function", "weight",
}


@dataclass(frozen=True)
class EvidenceSource:
    source_id: str
    title: str
    publisher: str
    jurisdiction: str
    url: str
    content_rights: str = "unknown"
    approval_status: str = "draft"
    reviewer: str = ""
    reviewed_on: str = ""
    review_due_on: str = ""
    edition: str = ""
    version: str = ""
    published_on: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceSource":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: data[key] for key in allowed if key in data})


@dataclass(frozen=True)
class EvidenceCard:
    # Names a medicine/class mentioned in a source; it is not a recommendation.
    evidence_id: str
    source_id: str
    medicine_or_class: str
    evidence_summary: str
    assessment_terms: tuple[str, ...]
    section: str
    jurisdiction: str
    approval_status: str = "draft"
    reviewer: str = ""
    reviewed_on: str = ""
    review_due_on: str = ""
    required_patient_factors: tuple[str, ...] = ("allergies", "current_medications")
    caution_tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceCard":
        values = dict(data)
        for name in ("assessment_terms", "required_patient_factors", "caution_tags"):
            if name in values:
                if not isinstance(values[name], (list, tuple)):
                    raise ValueError("%s must be a list" % name)
                values[name] = tuple(str(value) for value in values[name])
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: values[key] for key in allowed if key in values})


@dataclass(frozen=True)
class ClinicianCase:
    # This is a non-identifying reference, not a patient name or chart number.
    case_id: str
    proposed_assessment: str
    symptoms: tuple[str, ...] = ()
    jurisdiction: str = "US"
    reviewed_factors: tuple[str, ...] = ()
    patient_risk_tags: tuple[str, ...] = ()
    reported_allergies: str = ""
    current_medications: str = ""
    relevant_medical_history: str = ""

    def __post_init__(self) -> None:
        for field_name in ("reported_allergies", "current_medications", "relevant_medical_history"):
            if len(getattr(self, field_name)) > 1200:
                raise ValueError("%s must be 1200 characters or fewer" % field_name)
        if not re.fullmatch(r"(?:case|synthetic|demo)[_-][A-Za-z0-9_-]{1,58}", self.case_id or "", re.IGNORECASE):
            raise ValueError("case_id must start with case_, synthetic_, or demo_ and contain no direct identifiers")
        if not self.jurisdiction.strip():
            raise ValueError("jurisdiction is required")
        invalid = sorted(set(self.reviewed_factors) - VALID_PATIENT_FACTORS)
        if invalid:
            raise ValueError("unsupported reviewed_factors: " + ", ".join(invalid))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClinicianCase":
        values = dict(data)
        for name in ("symptoms", "reviewed_factors", "patient_risk_tags"):
            if name in values:
                if not isinstance(values[name], (list, tuple)):
                    raise ValueError("%s must be a list" % name)
                values[name] = tuple(str(value) for value in values[name])
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: values[key] for key in allowed if key in values})


def _norm(value: str) -> str:
    return " ".join((value or "").casefold().split())


def _iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def _source_exclusion_reason(source: EvidenceSource, today: date) -> str | None:
    if source.approval_status != "approved":
        return "source_not_approved"
    if source.content_rights not in ALLOWED_CONTENT_RIGHTS:
        return "content_rights_not_cleared"
    if not all((source.source_id.strip(), source.title.strip(), source.publisher.strip(), source.jurisdiction.strip())):
        return "source_metadata_incomplete"
    parsed = urlparse(source.url or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "source_url_invalid"
    if not (source.edition.strip() or source.version.strip() or source.published_on.strip()):
        return "source_version_missing"
    reviewed, due = _iso_date(source.reviewed_on), _iso_date(source.review_due_on)
    if not source.reviewer.strip() or not reviewed or not due:
        return "source_review_metadata_missing"
    if reviewed > today:
        return "source_review_date_in_future"
    if due < today:
        return "source_review_overdue"
    return None


def _card_exclusion_reason(card: EvidenceCard, today: date) -> str | None:
    if card.approval_status != "approved":
        return "evidence_card_not_approved"
    required = (card.evidence_id, card.source_id, card.medicine_or_class,
                card.evidence_summary, card.section, card.jurisdiction)
    if not all(value.strip() for value in required):
        return "evidence_card_metadata_incomplete"
    if not card.assessment_terms or not any(term.strip() for term in card.assessment_terms):
        return "assessment_terms_missing"
    reviewed, due = _iso_date(card.reviewed_on), _iso_date(card.review_due_on)
    if not card.reviewer.strip() or not reviewed or not due:
        return "evidence_card_review_metadata_missing"
    if reviewed > today:
        return "evidence_card_review_date_in_future"
    if due < today:
        return "evidence_card_review_overdue"
    if set(card.required_patient_factors) - VALID_PATIENT_FACTORS:
        return "evidence_card_has_unsupported_patient_factors"
    return None


def load_registry(path: str | Path) -> tuple[list[EvidenceSource], list[EvidenceCard]]:
    """Load the versioned registry. Invalid shapes and duplicate IDs fail loudly."""
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise ValueError("unsupported evidence registry schema_version")
    raw_sources, raw_cards = raw.get("sources"), raw.get("evidence_cards")
    if not isinstance(raw_sources, list) or not isinstance(raw_cards, list):
        raise ValueError("registry sources and evidence_cards must be arrays")
    if not all(isinstance(item, dict) for item in raw_sources + raw_cards):
        raise ValueError("each source and evidence card must be an object")
    sources = [EvidenceSource.from_dict(item) for item in raw_sources]
    cards = [EvidenceCard.from_dict(item) for item in raw_cards]
    source_ids = [item.source_id for item in sources]
    evidence_ids = [item.evidence_id for item in cards]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source_id in evidence registry")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("duplicate evidence_id in evidence registry")
    return sources, cards


def _quality_checklist(case: ClinicianCase, matched_evidence_count: int) -> list[dict[str, str]]:
    """Show review completeness; never compute a clinical quality or safety score."""
    allergies_reviewed = "allergies" in case.reviewed_factors and bool(case.reported_allergies.strip())
    medications_reviewed = "current_medications" in case.reviewed_factors and bool(case.current_medications.strip())
    return [
        {
            "id": "clinician_assessment",
            "label": "Clinician-entered assessment",
            "state": "entered" if case.proposed_assessment.strip() else "missing",
            "detail": "Entered by clinician" if case.proposed_assessment.strip() else "Required before assessment-specific retrieval",
        },
        {
            "id": "symptoms",
            "label": "Symptoms",
            "state": "entered" if case.symptoms else "not_entered",
            "detail": "One or more symptoms entered" if case.symptoms else "Not entered in this synthetic case",
        },
        {
            "id": "allergies",
            "label": "Allergies and reactions",
            "state": "reviewed" if allergies_reviewed else "review_required",
            "detail": "Context entered and marked reviewed" if allergies_reviewed else "Enter context and confirm review, including 'none reported' or 'unknown' where appropriate",
        },
        {
            "id": "current_medications",
            "label": "Current medicines and supplements",
            "state": "reviewed" if medications_reviewed else "review_required",
            "detail": "Context entered and marked reviewed" if medications_reviewed else "Enter context and confirm review, including 'none reported' or 'unknown' where appropriate",
        },
        {
            "id": "medical_history",
            "label": "Relevant medical history",
            "state": "entered" if case.relevant_medical_history.strip() else "not_entered",
            "detail": "Context entered" if case.relevant_medical_history.strip() else "Not entered in this synthetic case",
        },
        {
            "id": "evidence",
            "label": "Approved evidence match",
            "state": "source_match" if matched_evidence_count else "no_verified_evidence",
            "detail": "A source match was retrieved; it is not a medication recommendation" if matched_evidence_count else "No approved evidence card matched; do not infer a medicine is appropriate or safe",
        },
        {
            "id": "supervising_review",
            "label": "Supervising dentist review",
            "state": "required",
            "detail": "Always required; this prototype does not record or approve a clinical decision",
        },
    ]


def _baseline_review_flags(case: ClinicianCase) -> list[dict[str, str]]:
    """Critical medication-context review prompts apply even when no card matches."""
    required_factors = {
        "allergies": (
            bool(case.reported_allergies.strip()),
            "Confirm reported allergies and reactions; record 'none reported' or 'unknown' when appropriate before interpreting medication evidence.",
        ),
        "current_medications": (
            bool(case.current_medications.strip()),
            "Confirm current medicines and supplements, or explicitly record 'none reported' or 'unknown', before interpreting medication evidence.",
        ),
    }
    return [
        {
            "code": "patient_factor_needs_review",
            "severity": "review_required",
            "factor": factor,
            "message": message,
        }
        for factor, (has_context, message) in required_factors.items()
        if factor not in case.reviewed_factors or not has_context
    ]


def build_evidence_review(
    case: ClinicianCase,
    sources: Iterable[EvidenceSource],
    cards: Iterable[EvidenceCard],
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Retrieve exact-phrase-matched evidence; never infer a prescription."""
    today = today or date.today()
    source_map = {source.source_id: source for source in sources}
    source_reasons = {key: _source_exclusion_reason(source, today) for key, source in source_map.items()}
    flags: list[dict[str, str]] = _baseline_review_flags(case)
    flagged_factors = {flag.get("factor") for flag in flags}

    if not case.proposed_assessment.strip():
        flags.insert(0, {
            "code": "missing_clinician_assessment",
            "severity": "review_required",
            "message": "Enter the clinician's working assessment before retrieving assessment-specific evidence.",
        })
        return _empty_review(case, flags, sum(reason is not None for reason in source_reasons.values()))

    query_text = _norm(" ".join([case.proposed_assessment] + list(case.symptoms)))
    case_jurisdiction = _norm(case.jurisdiction)
    matched: list[tuple[EvidenceCard, EvidenceSource, list[str]]] = []
    excluded_cards = 0

    for card in cards:
        reason = _card_exclusion_reason(card, today)
        source = source_map.get(card.source_id)
        if reason or source is None or source_reasons.get(card.source_id):
            excluded_cards += 1
            continue
        if _norm(card.jurisdiction) != case_jurisdiction or _norm(source.jurisdiction) != case_jurisdiction:
            excluded_cards += 1
            continue
        hits = [term for term in card.assessment_terms if _norm(term) and _norm(term) in query_text]
        if hits:
            matched.append((card, source, hits))

    evidence_items: list[dict[str, Any]] = []
    for card, source, hits in matched:
        for factor in card.required_patient_factors:
            if factor not in case.reviewed_factors and factor not in flagged_factors:
                flags.append({
                    "code": "patient_factor_needs_review",
                    "severity": "review_required",
                    "evidence_id": card.evidence_id,
                    "factor": factor,
                    "message": "Confirm patient factor '%s' before assessing whether this evidence applies." % factor,
                })
                flagged_factors.add(factor)
        risk_tags = {_norm(value) for value in case.patient_risk_tags}
        for tag in card.caution_tags:
            if _norm(tag) in risk_tags:
                flags.append({
                    "code": "configured_caution_tag_match",
                    "severity": "review_required",
                    "evidence_id": card.evidence_id,
                    "tag": tag,
                    "message": "A clinician-entered factor matches a reviewer-configured caution tag. Review the cited source and patient context.",
                })
        evidence_items.append({
            "evidence_id": card.evidence_id,
            "medicine_or_class_mentioned_in_source": card.medicine_or_class,
            "evidence_summary": card.evidence_summary,
            "matched_assessment_terms": hits,
            "source_reference": {
                "source_id": source.source_id,
                "title": source.title,
                "publisher": source.publisher,
                "edition": source.edition,
                "version": source.version,
                "published_on": source.published_on,
                "jurisdiction": source.jurisdiction,
                "url": source.url,
                "section_or_page": card.section,
                "source_reviewer": source.reviewer,
                "source_reviewed_on": source.reviewed_on,
                "evidence_reviewer": card.reviewer,
                "evidence_reviewed_on": card.reviewed_on,
                "review_due_on": card.review_due_on,
            },
            "required_patient_factors": list(card.required_patient_factors),
            "configured_caution_tags": list(card.caution_tags),
            "safety_assessment": "not_performed_by_this_module",
            "clinician_review_required": True,
        })

    return {
        "case_id": case.case_id,
        "status": "clinician_review_required" if evidence_items else "no_verified_evidence",
        "jurisdiction": case.jurisdiction,
        "clinician_assessment": case.proposed_assessment,
        "clinical_context_summary": {
            "reported_allergies": case.reported_allergies or "Not entered",
            "current_medications": case.current_medications or "Not entered",
            "relevant_medical_history": case.relevant_medical_history or "Not entered",
        },
        "matched_evidence": evidence_items,
        "quality_checklist": _quality_checklist(case, len(evidence_items)),
        "flags": flags,
        "flag_count": len(flags),
        "excluded_source_count": sum(reason is not None for reason in source_reasons.values()),
        "excluded_evidence_card_count": excluded_cards,
        "review_required": True,
        "autonomous_prescribing": False,
        "dose_calculation_performed": False,
        "comprehensive_interaction_check_performed": False,
        "safety_conclusion": "not_established",
        "message": (
            "Evidence retrieval only. A matching source is not a medication recommendation. "
            "This module does not diagnose, prescribe, calculate doses, or perform comprehensive "
            "interaction checks. The treating clinician must review the source and complete patient context."
            if evidence_items else
            "No approved, current, jurisdiction-matched evidence card matched this assessment. "
            "Do not infer that any medicine is appropriate or safe."
        ),
    }


def _empty_review(case: ClinicianCase, flags: list[dict[str, str]], source_count: int) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "status": "needs_clinician_input",
        "jurisdiction": case.jurisdiction,
        "clinician_assessment": case.proposed_assessment,
        "clinical_context_summary": {
            "reported_allergies": case.reported_allergies or "Not entered",
            "current_medications": case.current_medications or "Not entered",
            "relevant_medical_history": case.relevant_medical_history or "Not entered",
        },
        "matched_evidence": [],
        "quality_checklist": _quality_checklist(case, 0),
        "flags": flags,
        "flag_count": len(flags),
        "excluded_source_count": source_count,
        "excluded_evidence_card_count": 0,
        "review_required": True,
        "autonomous_prescribing": False,
        "dose_calculation_performed": False,
        "comprehensive_interaction_check_performed": False,
        "safety_conclusion": "not_established",
        "message": "No evidence was retrieved. Add clinician input and consult approved references.",
    }
