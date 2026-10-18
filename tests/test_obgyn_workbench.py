import json
from pathlib import Path

import pytest

from ai_front_desk.clinical.obgyn_workbench import (
    ALLOWED_JURISDICTIONS,
    DEFAULT_CATALOG_PATH,
    CARE_STAGES,
    load_sources,
    render_page,
    source_matches,
    urgent_prompts,
    validate_case_reference,
)


def test_obgyn_reference_catalog_has_unique_https_sources_and_versions():
    sources = load_sources()
    assert len(sources) >= 20
    assert len({source["id"] for source in sources}) == len(sources)
    assert all(source["url"].startswith("https://") for source in sources)
    ids = {source["id"] for source in sources}
    assert "who-pph-guideline-2025" in ids
    assert "ncbi-lactmed" in ids
    assert "uktis-bumps" in ids
    assert "eda-drug-register" in ids
    assert "eda-pharmaceutical-information-center" in ids


def test_synthetic_case_references_reject_patient_like_identifiers():
    assert validate_case_reference("synthetic-obgyn-001") == "synthetic-obgyn-001"
    for bad in ["Dr Shafy", "12345", "patient-0001", "synthetic-case-001", ""]:
        with pytest.raises(ValueError, match="synthetic case reference"):
            validate_case_reference(bad)


def test_jurisdiction_scope_does_not_mix_us_sources_into_egypt_results():
    assert ALLOWED_JURISDICTIONS == {"EG", "US", "UK", "GLOBAL"}
    eg_sources = source_matches("preeclampsia hypertension pregnancy", "antenatal", "EG")
    ids = {source["id"] for source in eg_sources}
    assert "acog-preeclampsia-practice-bulletin" not in ids
    assert all("EG" in source.get("jurisdiction", []) or "GLOBAL" in source.get("jurisdiction", []) or "GLOBAL_REFERENCE" in source.get("jurisdiction", []) for source in eg_sources)


def test_lactation_search_surfaces_lactmed_and_mothertobaby_as_references():
    sources = source_matches("breastfeeding medication exposure", "medication_pregnancy_lactation", "US")
    ids = {source["id"] for source in sources}
    assert "ncbi-lactmed" in ids
    assert "mother-to-baby" in ids
    assert all("not a" not in source.get("clinical_role", "").lower() for source in sources)


def test_urgent_prompts_escalate_without_suggesting_treatment():
    flags = urgent_prompts({"urgent_heavy_bleeding": "1", "urgent_seizure": "on"})
    assert len(flags) == 2
    assert all("Activate" in item["action"] or "emergency" in item["action"].lower() for item in flags)
    assert all("dose" not in item["action"].lower() and "prescribe" not in item["action"].lower() for item in flags)


def test_rendered_obgyn_page_has_avatar_and_specialty_reference_workflow():
    page = render_page()
    assert "<title>Dr. Mia · OB-GYN Clinical Reference Workbench</title>" in page
    assert "Personalize your OB-GYN Mia" in page
    assert "Clinical jurisdiction" in page
    assert "Gestational week" in page
    assert "Potential urgent escalation prompts" in page
    assert "SYNTHETIC CASES ONLY" in page
    assert "does not diagnose or choose a medicine" in page
    assert "data-mia-avatar-upload" in page


def test_rendered_page_escapes_clinical_question_and_does_not_store_it():
    page = render_page({
        "case_id": "synthetic-obgyn-002",
        "jurisdiction": "EG",
        "care_stage": "gynaecology",
        "clinical_question": "<script>alert('x')</script>",
    })
    assert "<script>alert('x')</script>" not in page
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in page


def test_care_stage_catalog_covers_obstetrics_and_gynaecology():
    assert "antenatal" in CARE_STAGES
    assert "intrapartum" in CARE_STAGES
    assert "postpartum" in CARE_STAGES
    assert "gynaecology" in CARE_STAGES
    assert "contraception" in CARE_STAGES
    assert "fertility" in CARE_STAGES
    assert "medication_pregnancy_lactation" in CARE_STAGES
