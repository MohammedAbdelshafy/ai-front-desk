"""Local, license-gated search over manually imported educational source text.

This module performs offline retrieval only. It does not diagnose, prescribe,
calculate doses, or turn textbook passages into approved clinical evidence.
Raw source files and the generated index stay outside the repository by default.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable

BASE = Path(__file__).resolve().parent
DEFAULT_MANIFEST_PATH = BASE / "pharmacology_learning_library.json"
DEFAULT_INDEX_PATH = Path(
    os.environ.get(
        "MIA_KNOWLEDGE_INDEX",
        str(Path.home() / ".mia-dental-os" / "knowledge-library.jsonl"),
    )
).expanduser()
MAX_SOURCE_CHARS = 25_000_000
MAX_QUERY_CHARS = 240
MAX_CHUNK_CHARS = 1800
CHUNK_OVERLAP_CHARS = 180
_ALLOWED_INGESTION_STATUSES = {"approved_for_educational_content_only"}


def load_source_catalog(path: str | Path = DEFAULT_MANIFEST_PATH) -> list[dict[str, Any]]:
    """Load the existing source catalog; it is the rights allow-list for imports."""
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise ValueError("unsupported pharmacology learning source catalog")
    sources = raw.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise ValueError("learning source catalog must contain a sources array")
    ids = [item.get("id") for item in sources]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("learning source IDs must be unique non-empty strings")
    return sources


def _get_ingestable_source(
    source_id: str,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    confirm_rights_review: bool = False,
) -> dict[str, Any]:
    sources = load_source_catalog(manifest_path)
    source = next((item for item in sources if item.get("id") == source_id), None)
    if source is None:
        raise ValueError("source_id is not in the approved source catalog")
    if source.get("commercial_reuse_permitted") is not True:
        raise PermissionError("source is not approved for commercial reuse; link-only or permission review required")
    license_id = str(source.get("license_id", "")).upper()
    if any(token in license_id for token in ("CC-BY-NC", "CC-BY-ND", "NONCOMMERCIAL", "NO-DERIVATIVES", "UNKNOWN")):
        raise PermissionError("noncommercial, no-derivatives, or unknown license cannot be imported")
    if source.get("ingestion_status") != "approved_for_educational_content_only":
        raise PermissionError("source is not explicitly cleared for educational text ingestion")
    limits = " ".join(str(item) for item in source.get("limits", [])).casefold()
    needs_review = any(term in limits for term in ("chapter-level", "third-party content", "third-party elements", "embedded third-party"))
    if needs_review and not confirm_rights_review:
        raise PermissionError(
            "this source has chapter/third-party rights caveats; verify the exact text selection, "
            "then re-run with --confirm-rights-review"
        )
    required = ("title", "url", "license_id", "license_url")
    if any(not source.get(key) for key in required):
        raise ValueError("source catalog entry is missing required provenance metadata")
    return source

def _words(text: str) -> list[str]:
    return [term for term in re.findall(r"[a-z0-9]+", text.casefold()) if len(term) >= 2]


def _is_heading(line: str) -> bool:
    value = line.strip()
    if not value or len(value) > 140:
        return False
    if re.match(r"^#{1,6}\s+\S", value):
        return True
    if re.match(r"^(chapter|appendix|unit|module|section)\s+[\wIVXivx.-]+", value, re.I):
        return True
    letters = [char for char in value if char.isalpha()]
    return bool(letters) and len(letters) <= 90 and all(char.isupper() for char in letters)


def _sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    heading = "Full text"
    body: list[str] = []
    for line in text.splitlines():
        if _is_heading(line):
            if "\n".join(body).strip():
                sections.append((heading, body))
            heading = re.sub(r"^#{1,6}\s+", "", line.strip())
            body = []
        else:
            body.append(line)
    if "\n".join(body).strip():
        sections.append((heading, body))
    return [(name, "\n".join(lines).strip()) for name, lines in sections if "\n".join(lines).strip()]


def _chunk_section(section: str, text: str) -> Iterable[str]:
    """Chunk near paragraph boundaries, splitting oversize paragraphs with overlap."""
    paragraphs = [re.sub(r"\s+", " ", item).strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    carry = ""
    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHUNK_CHARS:
            if carry:
                yield carry
                carry = ""
            start = 0
            while start < len(paragraph):
                end = min(len(paragraph), start + MAX_CHUNK_CHARS)
                if end < len(paragraph):
                    pivot = paragraph.rfind(" ", start + MAX_CHUNK_CHARS // 2, end)
                    if pivot > start:
                        end = pivot
                piece = paragraph[start:end].strip()
                if piece:
                    yield piece
                if end >= len(paragraph):
                    break
                start = max(start + 1, end - CHUNK_OVERLAP_CHARS)
            continue
        candidate = paragraph if not carry else carry + "\n\n" + paragraph
        if len(candidate) <= MAX_CHUNK_CHARS:
            carry = candidate
        else:
            if carry:
                yield carry
            carry = paragraph
    if carry:
        yield carry


def check_source_updates(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    previous_status_path: str | Path | None = None,
    save_status: bool = False,
) -> dict[str, Any]:
    """Check source URLs for HTTP version signals only; never auto-approves content."""
    import urllib.error
    import urllib.request

    sources = load_source_catalog(manifest_path)
    previous: dict[str, Any] = {}
    status_path = Path(previous_status_path).expanduser() if previous_status_path else None
    if status_path and status_path.exists():
        try:
            loaded = json.loads(status_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                previous = loaded
        except (OSError, json.JSONDecodeError):
            previous = {}

    records = []
    for source in sources:
        source_id = str(source.get("id", ""))
        url = str(source.get("url", ""))
        if not url.startswith(("https://", "http://")):
            records.append({"source_id": source_id, "status": "invalid_source_url", "url": url})
            continue
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "MiaKnowledgeLibrarySourceCheck/1.0"},
            method="HEAD",
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                modified = response.headers.get("Last-Modified")
                etag = response.headers.get("ETag")
                status_code = getattr(response, "status", 200)
            old = previous.get(source_id, {})
            changed = bool(
                isinstance(old, dict)
                and ((modified and old.get("last_modified") and modified != old.get("last_modified"))
                     or (etag and old.get("etag") and etag != old.get("etag")))
            )
            records.append({
                "source_id": source_id,
                "title": source.get("title"),
                "url": url,
                "status": "version_signal_changed" if changed else (
                    "reachable_metadata_found" if modified or etag else "reachable_version_signal_missing"
                ),
                "http_status": status_code,
                "last_modified": modified,
                "etag": etag,
                "previous_last_modified": old.get("last_modified") if isinstance(old, dict) else None,
                "previous_etag": old.get("etag") if isinstance(old, dict) else None,
                "checked_at": date.today().isoformat(),
                "license_status": source.get("ingestion_status"),
                "note": "Header changes trigger human re-review; they do not prove a clinical update.",
            })
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            records.append({
                "source_id": source_id,
                "title": source.get("title"),
                "url": url,
                "status": "check_unavailable",
                "error_type": type(exc).__name__,
                "license_status": source.get("ingestion_status"),
                "note": "No currentness claim can be made from this check.",
            })
    report = {
        "checked_at": date.today().isoformat(),
        "check_type": "source_header_update_discovery_only",
        "source_count": len(records),
        "records": records,
        "message": "Header checks detect possible updates only. They do not download, index, license, or approve content.",
    }
    if save_status and status_path:
        status_path.parent.mkdir(parents=True, exist_ok=True)
        compact = {}
        for record in records:
            if record.get("status") in {"reachable_metadata_found", "reachable_version_signal_missing", "version_signal_changed"}:
                compact[str(record.get("source_id"))] = {
                    "last_modified": record.get("last_modified"),
                    "etag": record.get("etag"),
                    "checked_at": record.get("checked_at"),
                }
            elif record.get("source_id") in previous:
                compact[str(record.get("source_id"))] = previous[str(record.get("source_id"))]
        temp_fd, temp_path = tempfile.mkstemp(prefix="mia-source-status-", suffix=".json", dir=str(status_path.parent))
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
                json.dump(compact, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
            os.replace(temp_path, status_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        report["status_saved_to"] = str(status_path)
    return report


def _read_index(path: str | Path) -> list[dict[str, Any]]:
    index_path = Path(path)
    if not index_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with index_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError("invalid corpus index JSONL at line %d" % line_number) from exc
            if isinstance(row, dict) and isinstance(row.get("text"), str) and row.get("chunk_id"):
                rows.append(row)
            else:
                raise ValueError("invalid corpus index row at line %d" % line_number)
    return rows


def index_text_file(
    source_id: str,
    source_text_path: str | Path,
    *,
    corpus_path: str | Path = DEFAULT_INDEX_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    confirm_rights_review: bool = False,
) -> dict[str, Any]:
    """Index UTF-8 text explicitly supplied by the operator from an allowed source.

    The importer does not crawl, download, or scrape books. It deliberately
    requires a local text file so the operator can verify its origin and rights.
    Re-indexing a source replaces that source's prior local chunks.
    """
    source = _get_ingestable_source(
        source_id,
        manifest_path=manifest_path,
        confirm_rights_review=confirm_rights_review,
    )
    source_path = Path(source_text_path).expanduser()
    if not source_path.is_file():
        raise FileNotFoundError("source text file was not found")
    raw_bytes = source_path.read_bytes()
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("source input must be UTF-8 plain text; convert only a rights-cleared text selection first") from exc
    if not text.strip():
        raise ValueError("source text file is empty")
    if len(text) > MAX_SOURCE_CHARS:
        raise ValueError("source text exceeds the local import limit of 25 million characters")
    source_hash = hashlib.sha256(raw_bytes).hexdigest()
    edition_bits = [
        str(source.get("published_year", "")).strip(),
        str(source.get("edition", "")).strip(),
    ]
    edition = " ".join(bit for bit in edition_bits if bit) or "edition/version not recorded"
    authors = source.get("authors", [])
    attribution = "%s. %s. %s. License: %s." % (
        ", ".join(str(item) for item in authors) if authors else source.get("publisher", "Source publisher"),
        source.get("title", ""),
        source.get("published_year", ""),
        source.get("license_id", ""),
    )
    new_rows: list[dict[str, Any]] = []
    ordinal = 0
    for section, section_text in _sections(text):
        for chunk in _chunk_section(section, section_text):
            ordinal += 1
            stable = "%s|%s|%s|%s" % (source_id, source_hash, ordinal, chunk)
            new_rows.append({
                "chunk_id": hashlib.sha256(stable.encode("utf-8")).hexdigest(),
                "source_id": source_id,
                "source_title": str(source["title"]),
                "source_url": str(source["url"]),
                "license_id": str(source["license_id"]),
                "license_url": str(source["license_url"]),
                "attribution": attribution,
                "edition_or_version": edition,
                "published_year": source.get("published_year"),
                "section": section,
                "text": chunk,
                "source_sha256": source_hash,
                "indexed_on": date.today().isoformat(),
                "content_role": "foundational_education",
                "clinical_review_status": "not_clinically_approved",
                "commercial_reuse_permitted": True,
                "use_scope": "education_only",
                "is_prescribing_recommendation": False,
                "is_drug_interaction_result": False,
            })
    if not new_rows:
        raise ValueError("no text chunks could be created from the source file")
    index_path = Path(corpus_path).expanduser()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_index(index_path)
    # Replace the source's previous version rather than leaving stale duplicate passages.
    retained = [row for row in existing if row.get("source_id") != source_id]
    fd, temporary = tempfile.mkstemp(prefix="mia-library-", suffix=".jsonl", dir=str(index_path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in retained + new_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temporary, index_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {
        "status": "indexed",
        "source_id": source_id,
        "source_title": source["title"],
        "source_sha256": source_hash,
        "chunk_count": len(new_rows),
        "corpus_path": str(index_path),
        "content_role": "foundational_education",
        "clinical_review_status": "not_clinically_approved",
        "message": "Indexed for local education-only search. These passages are not approved prescribing evidence.",
    }


def search_knowledge_library(
    query: str,
    *,
    corpus_path: str | Path = DEFAULT_INDEX_PATH,
    limit: int = 5,
    mode: str = "education",
) -> dict[str, Any]:
    """Search local chunks with BM25-style lexical ranking and return citations."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Enter a knowledge-library search topic.")
    if len(query) > MAX_QUERY_CHARS:
        raise ValueError("Knowledge-library query must be %d characters or fewer." % MAX_QUERY_CHARS)
    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    if mode not in {"education", "clinical_evidence"}:
        raise ValueError("mode must be education or clinical_evidence")
    rows = _read_index(corpus_path)
    if not rows:
        return {
            "query": query.strip(),
            "status": "corpus_empty",
            "results": [],
            "result_count": 0,
            "mode": mode,
            "no_external_calls": True,
            "message": (
                "No full-text source has been indexed locally yet. Import only a source whose commercial "
                "reuse rights are verified. The small curated learning-note shelf is separate."
            ),
        }
    if mode == "clinical_evidence":
        rows = [
            row for row in rows
            if row.get("content_role") == "approved_clinical_evidence"
            and row.get("clinical_review_status") == "approved"
            and row.get("commercial_reuse_permitted") is True
            and row.get("qualified_reviewer")
            and row.get("clinical_approval_id")
        ]
        if not rows:
            return {
                "query": query.strip(),
                "status": "no_approved_clinical_evidence",
                "results": [],
                "result_count": 0,
                "mode": mode,
                "no_external_calls": True,
                "message": "No source chunks meet the approved clinical-evidence gate. Textbook passages cannot satisfy this gate.",
            }
    query_terms = _words(query)
    if not query_terms:
        return {
            "query": query.strip(), "status": "no_match", "results": [],
            "result_count": 0, "mode": mode, "no_external_calls": True,
            "message": "No searchable terms were found.",
        }
    tokenized = [_words(str(row.get("text", ""))) for row in rows]
    count = len(rows)
    doc_freq: Counter[str] = Counter()
    for tokens in tokenized:
        doc_freq.update(set(tokens))
    average_length = max(1.0, sum(len(tokens) for tokens in tokenized) / count)
    k1 = 1.5
    b = 0.75
    ranked: list[tuple[float, dict[str, Any]]] = []
    for row, tokens in zip(rows, tokenized):
        frequencies = Counter(tokens)
        length = max(1, len(tokens))
        score = 0.0
        for term in query_terms:
            tf = frequencies.get(term, 0)
            if not tf:
                continue
            idf = math.log(1.0 + (count - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            denominator = tf + k1 * (1.0 - b + b * length / average_length)
            score += idf * (tf * (k1 + 1.0) / denominator)
        if score > 0:
            ranked.append((score, row))
    ranked.sort(key=lambda item: (-item[0], item[1].get("source_title", ""), item[1].get("section", "")))
    results = []
    for score, row in ranked[:limit]:
        results.append({
            "chunk_id": row["chunk_id"],
            "text": row["text"],
            "score": round(score, 4),
            "source_id": row["source_id"],
            "source_title": row["source_title"],
            "source_url": row["source_url"],
            "license_id": row["license_id"],
            "license_url": row["license_url"],
            "attribution": row["attribution"],
            "edition_or_version": row["edition_or_version"],
            "published_year": row.get("published_year"),
            "section": row["section"],
            "source_sha256": row["source_sha256"],
            "indexed_on": row["indexed_on"],
            "use_scope": row["use_scope"],
            "clinical_review_status": row["clinical_review_status"],
            "is_prescribing_recommendation": False,
            "is_drug_interaction_result": False,
        })
    return {
        "query": query.strip(),
        "status": "found" if results else "no_match",
        "results": results,
        "result_count": len(results),
        "mode": mode,
        "no_external_calls": True,
        "message": (
            "Retrieved locally indexed source passages with edition, section, and license provenance. "
            "This is education-only retrieval, not a medication recommendation or patient-specific safety check."
            if results else "No matching passage was found in the local full-text index."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Index a rights-cleared, UTF-8 text file from the Dr. Mia source allow-list for offline educational search."
    )
    parser.add_argument("--source-id", help="Source ID from pharmacology_learning_library.json")
    parser.add_argument("--file", help="Local UTF-8 .txt file from the verified source selection")
    parser.add_argument("--corpus-path", default=str(DEFAULT_INDEX_PATH), help="Local JSONL index path (default is outside the repo)")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH), help="Source allow-list JSON path")
    parser.add_argument("--list-sources", action="store_true", help="List catalog sources and their ingest eligibility")
    parser.add_argument("--check-updates", action="store_true", help="Check source URL HTTP headers for possible updates")
    parser.add_argument("--status-path", default=str(Path.home() / ".mia-dental-os" / "source-update-status.json"), help="Local update-check state path")
    parser.add_argument("--save-update-status", action="store_true", help="Save Last-Modified/ETag signals locally for comparison on the next run")
    parser.add_argument("--search", help="Search the local index without importing a new source")
    parser.add_argument("--mode", choices=("education", "clinical_evidence"), default="education", help="Clinical evidence mode returns only explicitly approved evidence chunks")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of local passages to return (1-10)")
    parser.add_argument(
        "--confirm-rights-review", action="store_true",
        help="Confirm that chapter-level/third-party content in the selected text was checked and excluded if not reusable",
    )
    args = parser.parse_args()
    if args.list_sources:
        sources = load_source_catalog(args.manifest_path)
        print(json.dumps([{
            "id": item.get("id"),
            "title": item.get("title"),
            "license_id": item.get("license_id"),
            "commercial_reuse_permitted": item.get("commercial_reuse_permitted"),
            "ingestion_status": item.get("ingestion_status"),
            "url": item.get("url"),
        } for item in sources], indent=2, ensure_ascii=False))
        return 0
    if args.check_updates:
        result = check_source_updates(
            manifest_path=args.manifest_path,
            previous_status_path=args.status_path,
            save_status=args.save_update_status,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.search:
        try:
            result = search_knowledge_library(
                args.search,
                corpus_path=args.corpus_path,
                limit=args.limit,
                mode=args.mode,
            )
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
            return 2
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if not args.source_id or not args.file:
        parser.error("--source-id and --file are required unless --list-sources, --check-updates, or --search is used")
    try:
        result = index_text_file(
            args.source_id, args.file,
            corpus_path=args.corpus_path,
            manifest_path=args.manifest_path,
            confirm_rights_review=args.confirm_rights_review,
        )
    except (OSError, ValueError, PermissionError) as exc:
        parser.error(str(exc))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
