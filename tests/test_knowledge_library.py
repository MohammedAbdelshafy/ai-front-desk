import json
from pathlib import Path

import pytest

from ai_front_desk.clinical.knowledge_library import (
    index_text_file,
    search_knowledge_library,
)


def test_indexes_and_retrieves_rights_cleared_text_with_provenance(tmp_path: Path):
    source_text = tmp_path / "openrn_excerpt.txt"
    source_text.write_text(
        "CHAPTER 1 PHARMACOKINETICS\n\n"
        "Pharmacokinetics describes absorption, distribution, metabolism, and excretion. "
        "These processes affect the concentration of a medicine over time.\n\n"
        "CHAPTER 2 PHARMACODYNAMICS\n\n"
        "Pharmacodynamics describes the effects a medicine has on the body.\n",
        encoding="utf-8",
    )
    index_path = tmp_path / "index.jsonl"

    indexed = index_text_file(
        "openrn-nursing-pharmacology-2e",
        source_text,
        corpus_path=index_path,
    )
    assert indexed["status"] == "indexed"
    assert indexed["chunk_count"] >= 2
    assert index_path.exists()

    result = search_knowledge_library(
        "pharmacokinetics absorption metabolism", corpus_path=index_path
    )
    assert result["status"] == "found"
    assert result["no_external_calls"] is True
    best = result["results"][0]
    assert "absorption" in best["text"].lower()
    assert best["source_id"] == "openrn-nursing-pharmacology-2e"
    assert best["license_id"] == "CC-BY-4.0"
    assert "NBK595000" in best["source_url"]
    assert best["section"].upper().startswith("CHAPTER 1")
    assert best["clinical_review_status"] == "not_clinically_approved"
    assert best["is_prescribing_recommendation"] is False


def test_noncommercial_book_is_rejected_from_commercial_index(tmp_path: Path):
    source_text = tmp_path / "noncommercial.txt"
    source_text.write_text("A harmless test excerpt.", encoding="utf-8")
    with pytest.raises(PermissionError, match="not approved for commercial reuse"):
        index_text_file(
            "openstax-pharmacology-for-nurses",
            source_text,
            corpus_path=tmp_path / "index.jsonl",
        )


def test_source_with_chapter_rights_caveat_requires_explicit_confirmation(tmp_path: Path):
    source_text = tmp_path / "uic_excerpt.txt"
    source_text.write_text("PHARMACOLOGY\n\nAbsorption and metabolism.", encoding="utf-8")
    with pytest.raises(PermissionError, match="chapter/third-party rights caveats"):
        index_text_file(
            "uic-essentials-of-pharmacology",
            source_text,
            corpus_path=tmp_path / "index.jsonl",
        )


def test_textbook_chunks_never_qualify_as_approved_clinical_evidence(tmp_path: Path):
    source_text = tmp_path / "text.txt"
    source_text.write_text(
        "CHAPTER 1 PHARMACOLOGY\n\nMedicine names and mechanisms.",
        encoding="utf-8",
    )
    index_path = tmp_path / "index.jsonl"
    index_text_file("openrn-nursing-pharmacology-2e", source_text, corpus_path=index_path)

    result = search_knowledge_library(
        "medicine mechanisms", corpus_path=index_path, mode="clinical_evidence"
    )
    assert result["status"] == "no_approved_clinical_evidence"
    assert result["results"] == []


def test_empty_index_and_invalid_search_inputs_fail_closed(tmp_path: Path):
    result = search_knowledge_library("antimicrobial stewardship", corpus_path=tmp_path / "missing.jsonl")
    assert result["status"] == "corpus_empty"
    assert result["results"] == []

    with pytest.raises(ValueError):
        search_knowledge_library(" ")
    with pytest.raises(ValueError):
        search_knowledge_library("x" * 241)
    with pytest.raises(ValueError):
        search_knowledge_library("pharmacology", limit=0)


def test_reindex_replaces_previous_chunks_for_same_source(tmp_path: Path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("CHAPTER 1 OLD VERSION\n\nOld source-only passage.", encoding="utf-8")
    second.write_text("CHAPTER 1 NEW VERSION\n\nNew source-only passage.", encoding="utf-8")
    index_path = tmp_path / "index.jsonl"

    index_text_file("openrn-nursing-pharmacology-2e", first, corpus_path=index_path)
    index_text_file("openrn-nursing-pharmacology-2e", second, corpus_path=index_path)
    rows = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines()]

    assert rows
    assert len({row["source_id"] for row in rows}) == 1
    assert all("New source-only" in row["text"] or "CHAPTER 1 NEW" in row["section"] for row in rows)
    assert not any("Old source-only" in row["text"] for row in rows)


def test_noncommercial_flag_token_does_not_reject_plain_cc_by_licenses(tmp_path: Path):
    source_text = tmp_path / "openrn.txt"
    source_text.write_text("CHAPTER 1 OPEN\n\nAbsorption and metabolism.", encoding="utf-8")
    result = index_text_file(
        "openrn-nursing-pharmacology-2e",
        source_text,
        corpus_path=tmp_path / "index.jsonl",
    )
    assert result["status"] == "indexed"


def test_license_catalogs_for_link_only_sources_are_rejected(tmp_path: Path):
    source_text = tmp_path / "merck.txt"
    source_text.write_text("Text that must not be ingested.", encoding="utf-8")
    with pytest.raises(PermissionError, match="not approved for commercial reuse"):
        index_text_file(
            "merck-manual-professional",
            source_text,
            corpus_path=tmp_path / "index.jsonl",
        )


def test_unknown_or_pending_review_source_is_rejected(tmp_path: Path):
    source_text = tmp_path / "who.txt"
    source_text.write_text("Text awaiting permission.", encoding="utf-8")
    with pytest.raises(PermissionError, match="not approved for commercial reuse"):
        index_text_file(
            "who-model-list-essential-medicines-2025",
            source_text,
            corpus_path=tmp_path / "index.jsonl",
        )
