from pathlib import Path

import pytest

from ai_front_desk.clinical.clinical_evidence_drafts import (
    DEFAULT_DRAFTS_PATH,
    load_draft_cards,
    match_draft_cards,
)


def test_draft_catalog_loads_source_cited_review_cards():
    cards = load_draft_cards()
    assert len(cards) >= 3
    assert all(card["approval_status"] == "draft_for_dentist_review" for card in cards)
    assert all(card.get("sources") for card in cards)


def test_adult_dental_pain_phrase_finds_nonopioid_review_card():
    cards = match_draft_cards("Acute dental pain after tooth extraction", jurisdiction="US")
    assert any(card["id"] == "draft-us-acute-dental-pain-nonopioid" for card in cards)


def test_dental_abscess_phrase_finds_antibiotic_stewardship_card_not_a_prescription():
    cards = match_draft_cards("dental abscess and swelling", jurisdiction="US")
    stewardship = next(card for card in cards if card["id"] == "draft-us-pulpal-periapical-antibiotic-stewardship")
    assert stewardship["approval_status"] == "draft_for_dentist_review"
    assert "Amoxicillin" in [item["name"] for item in stewardship["candidate_options_for_review"]]
    assert "No dose" in " ".join(stewardship["not_approved_or_not_performed"])


def test_us_guidance_never_matches_egypt_jurisdiction():
    assert match_draft_cards("acute dental pain toothache", jurisdiction="EG") == []


def test_blank_query_returns_no_draft_cards():
    assert match_draft_cards("  ", " ", jurisdiction="US") == []


def test_draft_loader_rejects_non_draft_entries(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(
        '{"schema_version":"1.0","cards":[{"id":"oops","approval_status":"approved"}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="only draft_for_dentist_review"):
        load_draft_cards(bad)


def test_draft_file_is_the_checked_in_default_source():
    assert DEFAULT_DRAFTS_PATH.exists()
