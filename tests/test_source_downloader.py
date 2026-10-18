import hashlib
import json
from io import BytesIO
from pathlib import Path

import pytest

from ai_front_desk.clinical.source_downloader import (
    SourceDownloadError,
    download_source,
    list_downloadable_sources,
)


def catalog_file(tmp_path: Path) -> Path:
    path = tmp_path / "centers.json"
    path.write_text(json.dumps({
        "schema_version": "1.0",
        "sources": [
            {
                "id": "openrn-nursing-pharmacology-2e",
                "name": "Open RN Nursing Pharmacology 2e",
                "publisher": "Test publisher",
                "url": "https://example.org/book",
                "download_url": "https://example.org/book.pdf",
                "license_id": "CC-BY-4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "commercial_reuse_permitted": True,
                "clinical_status": "education_only_not_a_drug_reference",
                "attribution": "Test attribution",
            },
            {
                "id": "restricted-guideline",
                "name": "Restricted guideline",
                "url": "https://example.org/guideline",
                "download_url": "https://example.org/guideline.pdf",
                "license_id": "CC-BY-NC-ND-4.0",
                "commercial_reuse_permitted": False,
                "clinical_status": "candidate_for_dentist_review",
            },
        ]
    }), encoding="utf-8")
    return path


def test_source_downloader_lists_only_license_cleared_education_files(tmp_path):
    catalog = catalog_file(tmp_path)
    listed = list_downloadable_sources(catalog)
    assert [item["id"] for item in listed] == ["openrn-nursing-pharmacology-2e"]
    assert listed[0]["license_id"] == "CC-BY-4.0"


def test_download_refuses_without_explicit_rights_confirmation(tmp_path):
    catalog = catalog_file(tmp_path)
    with pytest.raises(PermissionError, match="confirming attribution"):
        download_source("openrn-nursing-pharmacology-2e", directory=tmp_path / "downloads", catalog_path=catalog)


def test_download_refuses_noncommercial_or_unknown_rights(tmp_path):
    catalog = catalog_file(tmp_path)
    with pytest.raises(PermissionError, match="not approved for automatic download"):
        download_source(
            "restricted-guideline",
            directory=tmp_path / "downloads",
            catalog_path=catalog,
            confirm_rights_review=True,
        )


def test_download_saves_source_and_sha256_provenance_sidecar(tmp_path):
    catalog = catalog_file(tmp_path)
    payload = b"%PDF-1.7 synthetic testing content"

    class FakeResponse(BytesIO):
        status = 200
        headers = {"Content-Type": "application/pdf", "Content-Length": str(len(payload))}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.close()

    result = download_source(
        "openrn-nursing-pharmacology-2e",
        directory=tmp_path / "downloads",
        catalog_path=catalog,
        confirm_rights_review=True,
        opener=lambda request, timeout=45: FakeResponse(payload),
    )
    saved = Path(result["path"])
    sidecar = saved.with_suffix(saved.suffix + ".source.json")
    assert saved.read_bytes() == payload
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert json.loads(sidecar.read_text(encoding="utf-8"))["clinical_evidence_approved"] is False
    assert "not a medication monograph" in json.loads(sidecar.read_text(encoding="utf-8"))["notice"]


def test_download_refuses_empty_source_response(tmp_path):
    catalog = catalog_file(tmp_path)

    class FakeResponse(BytesIO):
        status = 200
        headers = {"Content-Type": "application/pdf", "Content-Length": "0"}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.close()

    with pytest.raises(SourceDownloadError, match="empty file"):
        download_source(
            "openrn-nursing-pharmacology-2e",
            directory=tmp_path / "downloads",
            catalog_path=catalog,
            confirm_rights_review=True,
            opener=lambda request, timeout=45: FakeResponse(b""),
        )



def test_repository_catalog_exposes_only_the_two_cc_by_education_downloads():
    from ai_front_desk.clinical.source_downloader import list_downloadable_sources as list_repo_sources

    sources = list_repo_sources()
    ids = {item["id"] for item in sources}
    assert "openrn-nursing-pharmacology-2e" in ids
    assert "public-health-pharmacy-practice-casebook-2e" in ids
    assert all(item["license_id"] == "CC-BY-4.0" for item in sources)
    assert not any("ada-" in item["id"] or "cdc-" in item["id"] for item in sources)
