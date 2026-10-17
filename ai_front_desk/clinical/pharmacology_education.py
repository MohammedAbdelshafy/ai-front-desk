"""Local search over short, source-linked pharmacology learning notes.

These notes are an educational retrieval layer grounded in open-license books
and public reference links. They are not a prescribing knowledge base, drug
monograph database, diagnostic system, or interaction checker.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

BASE = Path(__file__).resolve().parent
DEFAULT_PATH = BASE / "pharmacology_education_cards.json"


def load_learning_cards(path: str | Path = DEFAULT_PATH) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise ValueError("unsupported pharmacology education schema_version")
    cards = raw.get("cards")
    if not isinstance(cards, list) or not all(isinstance(card, dict) for card in cards):
        raise ValueError("pharmacology education cards must be an array of objects")
    seen: set[str] = set()
    for card in cards:
        card_id = card.get("id")
        if not isinstance(card_id, str) or not card_id or card_id in seen:
            raise ValueError("education cards need unique non-empty IDs")
        seen.add(card_id)
        if card.get("use_scope") not in {"education_only", "workflow_education_only"}:
            raise ValueError("education card has a disallowed use_scope: %s" % card_id)
        if not card.get("source_refs") or not all(
            isinstance(source, dict) and source.get("url") and source.get("title")
            for source in card.get("source_refs", [])
        ):
            raise ValueError("education card must preserve source references: %s" % card_id)
    return cards


def _terms(text: str) -> set[str]:
    return {item for item in re.findall(r"[a-z0-9]+", text.casefold()) if len(item) > 1}


def search_pharmacology_education(
    query: str,
    *,
    path: str | Path = DEFAULT_PATH,
    limit: int = 5,
) -> dict[str, Any]:
    """Return keyword-relevant educational notes with provenance, not patient advice."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Enter a pharmacology learning topic.")
    if len(query) > 180:
        raise ValueError("Learning topic must be 180 characters or fewer.")
    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    query_terms = _terms(query)
    cards = load_learning_cards(path)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for card in cards:
        searchable = " ".join([
            str(card.get("title", "")), str(card.get("topic", "")),
            " ".join(card.get("keywords", [])), str(card.get("summary", "")),
        ])
        card_terms = _terms(searchable)
        overlap = query_terms.intersection(card_terms)
        score = len(overlap)
        if query.casefold().strip() in str(card.get("title", "")).casefold():
            score += 3
        if query.casefold().strip() in str(card.get("topic", "")).casefold():
            score += 2
        if score:
            ranked.append((score, card))
    ranked.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    results = []
    for score, card in ranked[:limit]:
        results.append({
            **card,
            "match_score": score,
            "is_prescribing_recommendation": False,
            "is_drug_interaction_result": False,
        })
    return {
        "query": query.strip(),
        "status": "found" if results else "no_learning_match",
        "results": results,
        "result_count": len(results),
        "use_scope": "educational_retrieval_only",
        "message": (
            "Found source-linked pharmacology learning notes. They provide foundational education, "
            "not patient-specific medicine selection, dosing, diagnosis, interaction screening, or a safety conclusion."
            if results else
            "No matching education note was found. This is not a clinical answer; consult appropriate current references and a qualified clinician."
        ),
    }
