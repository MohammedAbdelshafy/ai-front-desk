"""Download explicitly reusable clinical education source files.

This downloader is deliberately conservative:
- only sources carrying an explicit commercial reuse permission and a known,
  approved license in clinical_information_centers.json are eligible;
- it does not download ADA/CDC/EDA/WHO material marked link-only or pending rights;
- it stores the downloaded file and a provenance sidecar outside the repository;
- it does not ingest the content into the clinical recommendation registry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
DEFAULT_CATALOG_PATH = BASE / "clinical_information_centers.json"
DEFAULT_DOWNLOAD_DIR = Path.home() / ".mia-dental-os" / "source-files"
MAX_DOWNLOAD_BYTES = 250_000_000
CHUNK_SIZE = 1024 * 1024
ALLOWED_LICENSES = {"CC-BY-4.0", "CC BY 4.0", "CC-BY-4"}
USER_AGENT = "MiaClinicalSourceDownloader/1.0"


class SourceDownloadError(RuntimeError):
    """A source could not be safely downloaded."""


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise ValueError("unsupported clinical information center catalog")
    sources = raw.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise ValueError("clinical information center catalog requires a sources array")
    ids = [source.get("id") for source in sources]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("source IDs must be unique non-empty strings")
    return sources


def _is_download_eligible(source: dict[str, Any]) -> bool:
    return (
        source.get("commercial_reuse_permitted") is True
        and str(source.get("license_id", "")).strip() in ALLOWED_LICENSES
        and str(source.get("download_url", "")).startswith("https://")
        and source.get("clinical_status") == "education_only_not_a_drug_reference"
    )


def list_downloadable_sources(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, str]]:
    out = []
    for source in load_catalog(path):
        if not _is_download_eligible(source):
            continue
        out.append({
            "id": str(source["id"]),
            "name": str(source.get("name", "")),
            "url": str(source["download_url"]),
            "license_id": str(source["license_id"]),
            "license_url": str(source.get("license_url", "")),
        })
    return out


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    if not safe:
        raise ValueError("source ID does not contain safe filename characters")
    return safe[:120]


def _extension(url: str, content_type: str) -> str:
    lower_url = url.lower()
    lower_type = content_type.split(";", 1)[0].strip().lower()
    if lower_url.endswith(".tar.gz") or "application/gzip" == lower_type or "application/x-gzip" == lower_type:
        return ".tar.gz"
    if lower_type == "application/pdf" or "/pdf/" in lower_url or "-pdf/" in lower_url or lower_url.endswith(".pdf"):
        return ".pdf"
    ext = mimetypes.guess_extension(lower_type) if lower_type else None
    if ext in {".pdf", ".txt", ".gz", ".zip", ".epub"}:
        return ext
    raise SourceDownloadError("Unrecognized source file type; refusing to save as a knowledge source.")


def download_source(
    source_id: str,
    *,
    directory: str | Path = DEFAULT_DOWNLOAD_DIR,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    confirm_rights_review: bool = False,
    opener: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Download one allow-listed source, record metadata, and return provenance."""
    if not confirm_rights_review:
        raise PermissionError(
            "Run again with --confirm-rights-review after confirming attribution and reuse terms."
        )
    source = next((item for item in load_catalog(catalog_path) if item.get("id") == source_id), None)
    if source is None:
        raise ValueError("source ID not found in clinical information center catalog")
    if not _is_download_eligible(source):
        raise PermissionError(
            "Source is not approved for automatic download: commercial reuse permission and a known CC BY 4.0 license are required."
        )

    url = str(source["download_url"])
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf, application/gzip, application/octet-stream"})
    fetch = opener or urlopen
    try:
        response = fetch(request, timeout=45)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceDownloadError("Official source could not be fetched: %s" % type(exc).__name__) from exc

    with response:
        status = getattr(response, "status", 200)
        if not 200 <= int(status) < 300:
            raise SourceDownloadError("Official source returned HTTP %s." % status)
        content_type = str(response.headers.get("Content-Type", ""))
        ext = _extension(url, content_type)
        raw_length = response.headers.get("Content-Length")
        if raw_length:
            try:
                if int(raw_length) > MAX_DOWNLOAD_BYTES:
                    raise SourceDownloadError("Source exceeds the configured 250 MB download limit.")
            except ValueError:
                pass

        out_dir = Path(directory).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        basename = _safe_id(source_id) + ext
        final_path = out_dir / basename
        fd, temp_name = tempfile.mkstemp(prefix=".mia-download-", suffix=".tmp", dir=str(out_dir))
        digest = hashlib.sha256()
        total = 0
        try:
            with os.fdopen(fd, "wb") as target:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise SourceDownloadError("Source exceeded the configured 250 MB download limit.")
                    target.write(chunk)
                    digest.update(chunk)
                target.flush()
                os.fsync(target.fileno())
            if total == 0:
                raise SourceDownloadError("Official source returned an empty file.")
            os.replace(temp_name, final_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    source_date = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    metadata = {
        "source_id": source_id,
        "title": source.get("name", ""),
        "publisher": source.get("publisher", ""),
        "source_url": source.get("url", ""),
        "download_url": url,
        "license_id": source.get("license_id", ""),
        "license_url": source.get("license_url", ""),
        "attribution": source.get("attribution", ""),
        "downloaded_at_utc": source_date,
        "http_content_type": content_type,
        "file_size_bytes": total,
        "sha256": digest.hexdigest(),
        "path": str(final_path),
        "clinical_use_status": "education_only_not_a_drug_reference",
        "clinical_evidence_approved": False,
        "notice": "Downloaded education material is not a medication monograph or prescribing authority. Do not add textbook passages to the clinical evidence registry.",
    }
    sidecar_path = final_path.with_suffix(final_path.suffix + ".source.json")
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Download only approved, CC BY 4.0 clinical education sources")
    parser.add_argument("--list", action="store_true", help="List source files eligible for automated download")
    parser.add_argument("--source-id", help="Source ID to download")
    parser.add_argument("--all-eligible", action="store_true", help="Download every catalog entry explicitly approved for commercial educational reuse")
    parser.add_argument("--directory", default=str(DEFAULT_DOWNLOAD_DIR), help="Destination folder")
    parser.add_argument("--confirm-rights-review", action="store_true", help="Confirm you reviewed source rights and attribution obligations")
    args = parser.parse_args()

    if args.list:
        print(json.dumps(list_downloadable_sources(), ensure_ascii=False, indent=2))
        return
    if args.all_eligible:
        if not args.confirm_rights_review:
            parser.error("--all-eligible requires --confirm-rights-review after checking license and attribution terms")
        results = []
        failures = []
        for source in list_downloadable_sources():
            try:
                results.append({
                    "source_id": source["id"],
                    "status": "downloaded",
                    "result": download_source(
                        source["id"],
                        directory=args.directory,
                        confirm_rights_review=True,
                    ),
                })
            except (PermissionError, ValueError, SourceDownloadError) as exc:
                failures.append({"source_id": source["id"], "status": "failed", "error": str(exc)})
        print(json.dumps({"results": results, "failures": failures}, ensure_ascii=False, indent=2))
        if failures:
            parser.exit(status=1, message="One or more source downloads failed; check the JSON results above.\n")
        return
    if not args.source_id:
        parser.error("provide --list, --source-id, or --all-eligible")
    try:
        result = download_source(
            args.source_id,
            directory=args.directory,
            confirm_rights_review=args.confirm_rights_review,
        )
    except (PermissionError, ValueError, SourceDownloadError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
