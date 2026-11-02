"""Citation integrity tests for the prescribing reference dataset.

Every reference entry must carry a verifiable public source:
name, exact URL, access date, and what it supports. No citation means
the entry must not exist — this test suite enforces that.
"""
from urllib.parse import urlparse

from ai_front_desk.clinical.prescribe.reference_data import (
    DRUGS,
    SOURCES,
    GENERAL_SOURCES,
    RULES,
    INDICATIONS,
    REFERENCE_VERSION,
    REFERENCE_DATE,
    ACCESS_DATE,
)


def _assert_source_shape(src: dict, where: str):
    for field in ("name", "url", "accessed", "supports"):
        assert field in src, f"{where}: source missing '{field}'"
        assert isinstance(src[field], str) and src[field].strip(), (
            f"{where}: source field '{field}' is empty"
        )
    parsed = urlparse(src["url"])
    assert parsed.scheme in ("http", "https") and parsed.netloc, (
        f"{where}: source url is not a valid http(s) URL: {src['url']!r}"
    )
    assert src["url"].startswith("http"), f"{where}: url must be absolute"


def test_every_drug_has_at_least_one_source():
    for key in DRUGS:
        assert key in SOURCES, f"drug '{key}' has no cited sources"
        assert len(SOURCES[key]) >= 1, f"drug '{key}' has an empty source list"


def test_all_drug_sources_cited():
    for key, srcs in SOURCES.items():
        assert key in DRUGS, f"SOURCES has unknown drug '{key}'"
        for src in srcs:
            _assert_source_shape(src, f"drug '{key}'")


def test_general_sources_cited():
    assert len(GENERAL_SOURCES) >= 1
    for src in GENERAL_SOURCES:
        _assert_source_shape(src, "GENERAL_SOURCES")


def test_no_orphan_sources():
    assert set(SOURCES) == set(DRUGS), "SOURCES keys must match DRUGS exactly"


def test_rule_sources_reference_current_version():
    for rule in RULES:
        assert rule["source"].startswith(REFERENCE_VERSION + " —"), (
            f"rule {rule['id']}: source {rule['source']!r} does not cite {REFERENCE_VERSION}"
        )


def test_dataset_version_bumped():
    assert REFERENCE_VERSION == "reference v2"
    assert REFERENCE_DATE == ACCESS_DATE == "2026-10-11"


def test_clindamycin_prophylaxis_removed_per_aha():
    """2021 AHA statement (via ADA): clindamycin is no longer a prophylaxis
    alternative for penicillin-allergic patients."""
    alt_drugs = [a["drug"] for a in INDICATIONS["prophylaxis"]["alternatives"]]
    assert "clindamycin" not in alt_drugs
    cautions = " ".join(INDICATIONS["prophylaxis"]["cautions"])
    assert "clindamycin" in cautions.lower()
    assert "2021 AHA" in cautions
