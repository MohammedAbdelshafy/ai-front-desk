"""Source-cited draft evidence candidates for clinician review.

This file only performs deterministic keyword matching over explicitly draft
cards. It is not a diagnosis engine, medicine recommender, or safety checker.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
DEFAULT_DRAFTS_PATH = BASE / "clinical_evidence_drafts.json"


def load_draft_cards(path: str | Path = DEFAULT_DRAFTS_PATH) -> list[dict[str, Any]]:
    """Load draft cards; validate their shape and keep the review-only state."""
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise ValueError("unsupported clinical evidence draft schema")
    cards = raw.get("cards")
    if not isinstance(cards, list) or not all(isinstance(card, dict) for card in cards):
        raise ValueError("clinical evidence drafts must contain a cards array")
    ids = [card.get("id") for card in cards]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("clinical evidence draft IDs must be unique non-empty strings")
    # Deliberately do not allow this review-only catalog to expose approved cards.
    if any(card.get("approval_status") != "draft_for_dentist_review" for card in cards):
        raise ValueError("draft catalog may contain only draft_for_dentist_review cards")
    return cards


def match_draft_cards(
    assessment: str,
    symptoms: str = "",
    jurisdiction: str = "US",
    *,
    path: str | Path = DEFAULT_DRAFTS_PATH,
) -> list[dict[str, Any]]:
    """Return scoped phrase matches; never interpret a match as clinical fit."""
    query = " ".join((assessment or "", symptoms or "")).casefold()
    query = " ".join(query.split())
    if not query:
        return []
    results: list[dict[str, Any]] = []
    for card in load_draft_cards(path):
        scope = card.get("scope", {})
        card_jurisdiction = str(scope.get("jurisdiction", "")).casefold()
        if card_jurisdiction != (jurisdiction or "").casefold():
            continue
        terms = card.get("match_terms", [])
        hits = [term for term in terms if isinstance(term, str) and term.casefold() in query]
        if hits:
            result = dict(card)
            result["matched_terms_for_display_only"] = hits
            results.append(result)
    return results
