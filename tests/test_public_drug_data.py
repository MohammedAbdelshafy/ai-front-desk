from urllib.parse import parse_qs, urlparse

import pytest

from ai_front_desk.clinical import public_drug_data as drugdata


def test_medicine_query_is_validated_as_a_single_name():
    assert drugdata.validate_medicine_name("Amoxicillin") == "Amoxicillin"
    assert drugdata.validate_medicine_name("Tylenol 500 mg") == "Tylenol 500 mg"
    for invalid in ("", "  ", "Jane Doe is allergic", 'medicine" OR *:*', "<script>alert(1)</script>", "A" * 121):
        with pytest.raises(ValueError):
            drugdata.validate_medicine_name(invalid)


def test_rxnorm_normalization_returns_only_identity_metadata():
    def fake_fetch(url, timeout=4):
        assert url.startswith(drugdata.RXNORM_BASE + "/drugs.json?")
        assert parse_qs(urlparse(url).query)["name"] == ["amoxicillin"]
        return {
            "drugGroup": {
                "conceptGroup": [
                    {"tty": "SCD", "conceptProperties": [
                        {"rxcui": "723", "name": "amoxicillin 500 MG Oral Capsule", "tty": "SCD", "suppress": "N"}
                    ]}
                ]
            }
        }
    result = drugdata.search_rxnorm("amoxicillin", fetch_json=fake_fetch)
    assert result["status"] == "found"
    assert result["items"][0]["rxcui"] == "723"
    assert set(result["items"][0]) == {"rxcui", "name", "term_type"}


def test_openfda_query_returns_metadata_and_daily_med_link_only():
    def fake_fetch(url, timeout=4):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert "search" in params
        assert params["limit"] == ["5"]
        return {
            "results": [{
                "set_id": "12345678-1234-1234-1234-123456789abc",
                "effective_time": "20260101",
                "openfda": {
                    "brand_name": ["Synthetic brand"],
                    "generic_name": ["synthetic ingredient"],
                    "manufacturer_name": ["Synthetic manufacturer"],
                    "product_type": ["HUMAN PRESCRIPTION DRUG"],
                    "route": ["ORAL"],
                    "dosage_form": ["CAPSULE"],
                    "rxcui": ["12345"]
                },
                "indications_and_usage": ["This label text should never be returned."]
            }]
        }
    result = drugdata.search_openfda_label_metadata("synthetic ingredient", fetch_json=fake_fetch)
    assert result["status"] == "found"
    item = result["items"][0]
    assert item["generic_name"] == "synthetic ingredient"
    assert item["effective_time"] == "20260101"
    assert item["dailymed_url"].endswith("12345678-1234-1234-1234-123456789abc")
    assert "indications_and_usage" not in item
    assert "label text" not in str(result).lower()


def test_openfda_query_falls_back_to_brand_name_if_generic_no_match():
    calls = []
    def fake_fetch(url, timeout=4):
        calls.append(parse_qs(urlparse(url).query)["search"][0])
        if len(calls) == 1:
            raise drugdata.PublicDrugDataNotFound("none")
        return {"results": [{
            "set_id": "abcdef12-1234-1234-1234-123456789abc",
            "effective_time": "20260101",
            "openfda": {"brand_name": ["Synthetic brand"], "generic_name": ["synthetic ingredient"]}
        }]}
    result = drugdata.search_openfda_label_metadata("Synthetic brand", fetch_json=fake_fetch)
    assert result["status"] == "found"
    assert len(calls) == 2
    assert "openfda.generic_name" in calls[0]
    assert "openfda.brand_name" in calls[1]


def test_lookup_sends_only_standalone_name_to_both_sources():
    seen = []
    def fake_fetch(url, timeout=4):
        seen.append(url)
        if url.startswith(drugdata.RXNORM_BASE):
            return {"drugGroup": {"conceptGroup": []}}
        raise drugdata.PublicDrugDataNotFound("none")
    result = drugdata.lookup_public_drug_metadata("Synthetic medicine", fetch_json=fake_fetch)
    assert result["external_query_scope"] == "standalone_medicine_name_only"
    assert result["patient_context_sent"] is False
    assert result["clinical_recommendation_provided"] is False
    assert result["interaction_check_performed"] is False
    assert len(seen) >= 3
    assert all("symptoms" not in url and "allergies" not in url for url in seen)


def test_provider_failures_are_nonfatal_statuses():
    def fail(url, timeout=4):
        raise drugdata.PublicDrugDataError("offline")
    assert drugdata.search_rxnorm("amoxicillin", fetch_json=fail)["status"] == "unavailable"
    assert drugdata.search_openfda_label_metadata("amoxicillin", fetch_json=fail)["status"] == "unavailable"


def test_lookup_does_not_echo_or_persist_case_details():
    def fake_fetch(url, timeout=4):
        if url.startswith(drugdata.RXNORM_BASE):
            return {"drugGroup": {"conceptGroup": []}}
        raise drugdata.PublicDrugDataNotFound("none")
    result = drugdata.lookup_public_drug_metadata("Synthetic drug", fetch_json=fake_fetch)
    assert "patient" in result["source_notice"].lower()
    assert "allergies" not in result
    assert "medical_history" not in result

import json
from pathlib import Path


def test_open_knowledge_catalogs_declare_reuse_rights_and_limits():
    base = Path(__file__).resolve().parents[1] / "ai_front_desk" / "clinical"
    learning = json.loads((base / "pharmacology_learning_library.json").read_text(encoding="utf-8"))
    drug_data = json.loads((base / "drug_data_sources.json").read_text(encoding="utf-8"))

    books = {item["id"]: item for item in learning["sources"]}
    assert books["openrn-nursing-pharmacology-2e"]["license_id"] == "CC-BY-4.0"
    assert books["openrn-nursing-pharmacology-2e"]["commercial_reuse_permitted"] is True
    assert books["openstax-pharmacology-for-nurses"]["commercial_reuse_permitted"] is False

    providers = {item["id"]: item for item in drug_data["sources"]}
    assert providers["rxnorm-api"]["access_cost"] == "free_of_charge"
    assert "normalization" in " ".join(providers["rxnorm-api"]["roles"])
    assert providers["rxnav-discontinued-ddi"]["ingestion_status"] == "retired_do_not_integrate"
