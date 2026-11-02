"""Generate the dentist review packet FROM reference_data.py.

The review packet (docs/review/REFERENCE_REVIEW_PACK.md) is a readable
export of every reference entry: drugs, indications, safety rules, counseling
flags, and full citations. It is GENERATED, never hand-edited, so it cannot
drift from the code the app actually uses.

Regenerate:
    cd <repo-root> && python -m ai_front_desk.clinical.prescribe.export_review_pack

A regression test (tests/test_review_pack_current.py) regenerates into a
temp dir and diffs against the committed file, so CI fails if the packet
is stale.
"""
from __future__ import annotations

import difflib
from pathlib import Path

from . import reference_data as rd

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_PATH = REPO_ROOT / "docs" / "review" / "REFERENCE_REVIEW_PACK.md"


def _esc(text: str) -> str:
    return text.replace("|", "\\|")


def _drug_section(key: str, entry: dict) -> list[str]:
    lines = [f"### {entry['display']}", ""]
    lines.append(f"- **Aliases:** {', '.join(entry['aliases']) or '—'}")
    lines.append(f"- **Classes:** {', '.join(entry['classes'])}")
    lines.append(f"- **Standard adult dosing:** {entry['standard_adult']}")
    lines.append(f"- **Max daily:** {entry['max_daily_mg']} mg")
    lines.append(f"- **Notes:** {entry['notes']}")
    lines.append("- **Cited sources:**")
    for i, src in enumerate(rd.SOURCES[key], 1):
        lines.append(f"  {i}. **{src['name']}**")
        lines.append(f"     - URL: {src['url']}")
        lines.append(f"     - Accessed: {src['accessed']}")
        lines.append(f"     - Supports: {src['supports']}")
    lines.append("")
    return lines


def _match_text(rule: dict) -> str:
    m = rule["match"]
    if "drug" in m:
        return f"drug = {rd.DRUGS[m['drug']]['display']}"
    return f"drug class = {m['drug_class']}"


def _against_text(rule: dict) -> str:
    a = rule["against"]
    if "med" in a:
        return f"current medication = {a['med']}"
    if "med_class" in a:
        return f"current medication class = {a['med_class']}"
    if "condition" in a:
        return f"patient condition = {a['condition']}"
    if "allergy" in a:
        return f"patient allergy = {a['allergy']}"
    if "reports" in a:
        return f"patient-reported = {a['reports']}"
    return "?"


def generate() -> str:
    v, d = rd.REFERENCE_VERSION, rd.REFERENCE_DATE
    lines = [
        "# Mia Dental OS — Clinical Reference Review Pack",
        "",
        f"**Dataset:** {v} ({d})",
        f"**Generated:** from `ai_front_desk/clinical/prescribe/reference_data.py` — "
        "do not hand-edit this file; regenerate with "
        "`python -m ai_front_desk.clinical.prescribe.export_review_pack`.",
        "",
        "> **For the reviewing dentist:** you are reviewing the *accuracy of the "
        "reference content* below against current guidance. This is not an "
        "endorsement of the software, a clinical validation of outcomes, or a "
        "regulatory clearance. See `REVIEW_CHECKLIST.md` for instructions.",
        "",
        "## Contents",
        "",
        "1. Drug reference entries (by category)",
        "2. Indication guidance",
        "3. Safety rules (interactions / contraindications)",
        "4. Counseling flags",
        "5. Guidance-level sources",
        "",
        "---",
        "",
        "## 1. Drug reference entries",
        "",
        "Standard **adult** dental references. Every entry below is reference "
        "information, not a prescribing recommendation.",
        "",
    ]

    by_category: dict[str, list[str]] = {}
    for key, entry in rd.DRUGS.items():
        by_category.setdefault(entry["category"], []).append(key)
    for category in sorted(by_category):
        lines.append(f"## {category}")
        lines.append("")
        for key in by_category[category]:
            lines.extend(_drug_section(key, rd.DRUGS[key]))

    lines += [
        "---",
        "",
        "## 2. Indication guidance",
        "",
        "Indication panels shown to the dentist to *educate* the choice. "
        "The dentist always selects and decides.",
        "",
    ]
    for ind_key in rd.INDICATION_ORDER:
        ind = rd.INDICATIONS[ind_key]
        lines.append(f"### {ind['display']}")
        lines.append("")
        if ind["first_line"]:
            lines.append("**First-line:**")
            for item in ind["first_line"]:
                drug = rd.DRUGS[item["drug"]]["display"]
                lines.append(f"- {drug} — {item['dosing']}")
                lines.append(f"  - {item['note']}")
        if ind["alternatives"]:
            lines.append("**Alternatives:**")
            for item in ind["alternatives"]:
                drug = rd.DRUGS[item["drug"]]["display"]
                lines.append(f"- {drug} — {item['dosing']}")
                lines.append(f"  - When: {item['when']}")
        if ind["cautions"]:
            lines.append("**Cautions:**")
            for c in ind["cautions"]:
                lines.append(f"- {c}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 3. Safety rules",
        "",
        "Each rule fires a flag when a dentist's intended prescription matches. "
        "Severity: **RED** = do not proceed as entered; **YELLOW** = caution / counsel.",
        "",
        "| ID | Severity | Trigger | Reason | Source |",
        "|----|----------|---------|--------|--------|",
    ]
    for rule in rd.RULES:
        trigger = f"{_match_text(rule)} + {_against_text(rule)}"
        lines.append(
            f"| `{rule['id']}` | {rule['severity'].upper()} | "
            f"{_esc(trigger)} | {_esc(rule['reason'])} | {_esc(rule['source'])} |"
        )
    lines.append("")

    lines += [
        "---",
        "",
        "## 4. Counseling flags",
        "",
        "Informational flags attached whenever these drugs are prescribed:",
        "",
    ]
    for key, text in rd.COUNSEL_FLAGS.items():
        lines.append(f"- **{rd.DRUGS[key]['display']}:** {text}")
    lines.append("")

    lines += [
        "---",
        "",
        "## 5. Guidance-level sources",
        "",
        "Cited by indication panels and cautions above:",
        "",
    ]
    for i, src in enumerate(rd.GENERAL_SOURCES, 1):
        lines.append(f"{i}. **{src['name']}**")
        lines.append(f"   - URL: {src['url']}")
        lines.append(f"   - Accessed: {src['accessed']}")
        lines.append(f"   - Supports: {src['supports']}")
    lines.append("")

    n_sources = sum(len(v) for v in rd.SOURCES.values())
    lines += [
        "---",
        "",
        "## Packet statistics",
        "",
        f"- Drug entries: {len(rd.DRUGS)}",
        f"- Per-drug cited sources: {n_sources}",
        f"- Guidance-level sources: {len(rd.GENERAL_SOURCES)}",
        f"- Indication panels: {len(rd.INDICATIONS)}",
        f"- Safety rules: {len(rd.RULES)}",
        f"- Counseling flags: {len(rd.COUNSEL_FLAGS)}",
        "",
        "_End of review pack._",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = generate()
    OUT_PATH.write_text(text, encoding="utf-8")
    n_sources = sum(len(v) for v in rd.SOURCES.values())
    print(f"Wrote {OUT_PATH}")
    print(
        f"drugs={len(rd.DRUGS)} sources={n_sources} "
        f"indications={len(rd.INDICATIONS)} rules={len(rd.RULES)} "
        f"counsel={len(rd.COUNSEL_FLAGS)}"
    )


def diff_against_committed() -> str:
    """Unified diff between committed packet and a fresh generation."""
    committed = OUT_PATH.read_text(encoding="utf-8").splitlines()
    fresh = generate().splitlines()
    return "\n".join(
        difflib.unified_diff(
            committed, fresh, "committed", "generated", lineterm=""
        )
    )


if __name__ == "__main__":
    main()
