import json
from pathlib import Path

import pytest

from ai_front_desk.clinical.pharmacology_education import (
    load_learning_cards, search_pharmacology_education
)


def test_learning_cards_are_source_linked_and_educational_only():
    cards = load_learning_cards()
    assert len(cards) >= 5
    assert all(card["source_refs"] for card in cards)
    assert all(card["use_scope"] in {"education_only", "workflow_education_only"} for card in cards)
    assert all("diagnosis" in card["cannot_support"] or "medicine_selection" in card["cannot_support"] or "patient_specific_medicine_selection" in card["cannot_support"] for card in cards)


def test_search_returns_pharmacology_book_backed_notes():
    result = search_pharmacology_education("pharmacokinetics ADME")
    assert result["status"] == "found"
    assert result["results"][0]["id"] == "pharmacokinetics-adme"
    assert result["results"][0]["is_prescribing_recommendation"] is False
    assert result["results"][0]["source_refs"][0]["license_id"] == "CC-BY-4.0"


def test_search_uses_no_external_calls_and_has_source_provenance():
    result = search_pharmacology_education("antimicrobials")
    assert result["status"] == "found"
    serialized = json.dumps(result)
    assert "www.ncbi.nlm.nih.gov/books/NBK594998" in serialized
    assert "is_drug_interaction_result" in serialized


def test_search_rejects_empty_long_and_invalid_limit():
    with pytest.raises(ValueError):
        search_pharmacology_education(" ")
    with pytest.raises(ValueError):
        search_pharmacology_education("x" * 181)
    with pytest.raises(ValueError):
        search_pharmacology_education("pharmacology", limit=0)
