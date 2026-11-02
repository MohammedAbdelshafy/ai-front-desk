"""The dentist review packet must never drift from the reference code.

Regenerates REFERENCE_REVIEW_PACK.md from reference_data.py and diffs it
against the committed file. If they differ, someone changed the reference
data without regenerating the packet — CI fails until they do.
"""
from ai_front_desk.clinical.prescribe import export_review_pack as exp
from ai_front_desk.clinical.prescribe import reference_data as rd


def test_review_pack_is_current():
    diff = exp.diff_against_committed()
    assert diff == "", (
        "docs/review/REFERENCE_REVIEW_PACK.md is stale.\n"
        "Regenerate with: python -m "
        "ai_front_desk.clinical.prescribe.export_review_pack\n"
        + diff[:2000]
    )


def test_review_pack_covers_every_drug_and_source():
    pack = exp.OUT_PATH.read_text(encoding="utf-8")
    for key, entry in rd.DRUGS.items():
        assert entry["display"] in pack, key
        assert entry["standard_adult"] in pack, key
        for src in rd.SOURCES[key]:
            assert src["url"] in pack, (key, src["name"])
    for src in rd.GENERAL_SOURCES:
        assert src["url"] in pack, src["name"]
    for rule in rd.RULES:
        assert rule["id"] in pack and rule["reason"] in pack, rule["id"]
    for key in rd.COUNSEL_FLAGS:
        assert rd.DRUGS[key]["display"] in pack, key
