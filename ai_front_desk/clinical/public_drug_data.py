"""Name-only lookups against free public drug metadata APIs.

This adapter is opt-in and never sends the clinical case, symptoms, allergies,
current medicines, medical history, or any patient identifiers. It retrieves
only medication-name identity metadata and public label-record metadata. It is
not an interaction checker and does not recommend, prescribe, dose, or diagnose.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re

RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"
OPENFDA_BASE = "https://api.fda.gov/drug/label.json"
DAILYMED_SEARCH = "https://dailymed.nlm.nih.gov/dailymed/search.cfm"
TIMEOUT_SECONDS = 4
MAX_RESULTS = 5
MAX_LABEL_REFERENCE_RESULTS = 3
LABEL_REFERENCE_QUERY_LIMIT = 3
MAX_LABEL_SECTION_CHARS = 1800
MAX_QUERY_LENGTH = 120
LABEL_REFERENCE_SECTIONS = {
    "indications_and_usage": "Indications and usage",
    "dosage_and_administration": "Dosage and administration",
    "contraindications": "Contraindications",
    "boxed_warning": "Boxed warning",
    "warnings_and_cautions": "Warnings and cautions",
    "drug_interactions": "Drug interactions",
    "use_in_specific_populations": "Use in specific populations",
    "adverse_reactions": "Adverse reactions",
}
MEDICINE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 +().,'/-]{0,119}$")
# Block common clinical narrative terms so obvious case descriptions are not
# sent as a "medicine name". This cannot reliably detect every person's name;
# the UI must still tell users to enter only one known medicine/ingredient.
BLOCKED_QUERY_TERMS = {
    "patient", "patients", "allergy", "allergies", "allergic", "symptom", "symptoms",
    "history", "medical", "diagnosed", "diagnosis", "prescribed", "taking",
    "takes", "has", "have", "had", "is", "are", "was", "were", "he", "she",
    "they", "their", "dob", "birth", "age", "pain", "feels", "reports",
    "complains", "case", "chart",
}


class PublicDrugDataError(RuntimeError):
    """A public drug-data source was unavailable or returned an invalid response."""


class PublicDrugDataNotFound(PublicDrugDataError):
    """No matching public drug data record was found."""


def validate_medicine_name(value: str) -> str:
    """Accept a standalone medicine name/ingredient, never a patient case."""
    if not isinstance(value, str):
        raise ValueError("Enter one medicine name or active ingredient.")
    term = value.strip()
    tokens = set(re.findall(r"[a-z]+", term.casefold()))
    if (
        not term
        or len(term) > MAX_QUERY_LENGTH
        or not MEDICINE_NAME_RE.fullmatch(term)
        or tokens.intersection(BLOCKED_QUERY_TERMS)
        or len(term.split()) > 5
    ):
        raise ValueError("Enter one medicine name or active ingredient only; do not enter patient or clinical case details.")
    return term


def _fetch_json(url: str, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "DrMia-PublicDrugMetadata-Prototype/0.1",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(2_000_000)
    except HTTPError as exc:
        if exc.code == 404:
            raise PublicDrugDataNotFound("No matching public record was found.") from exc
        raise PublicDrugDataError("Public source returned HTTP %s." % exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise PublicDrugDataError("Public source is temporarily unavailable.") from exc

    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicDrugDataError("Public source returned invalid JSON.") from exc
    if not isinstance(parsed, dict):
        raise PublicDrugDataError("Public source returned an unexpected response shape.")
    if "error" in parsed and "results" not in parsed:
        raise PublicDrugDataNotFound("No matching public record was found.")
    return parsed


def _invoke_fetch(fetch_json: Callable[..., dict[str, Any]], url: str) -> dict[str, Any]:
    # Keeps all HTTP response handling in one helper and allows deterministic tests.
    try:
        return fetch_json(url, timeout=TIMEOUT_SECONDS)
    except TypeError:
        # Helpful for test adapters/callables that only accept URL.
        return fetch_json(url)


def search_rxnorm(
    medicine_name: str,
    *,
    fetch_json: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize a standalone term to RxNorm names/identifiers; not clinical advice."""
    term = validate_medicine_name(medicine_name)
    fetch = fetch_json or _fetch_json
    url = RXNORM_BASE + "/drugs.json?" + urlencode({"name": term})
    try:
        data = _invoke_fetch(fetch, url)
    except PublicDrugDataNotFound:
        return {"status": "not_found", "query": term, "items": [], "source_url": url}
    except PublicDrugDataError:
        return {"status": "unavailable", "query": term, "items": [], "source_url": url}

    group = data.get("drugGroup", {})
    groups = group.get("conceptGroup", []) if isinstance(group, dict) else []
    items: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for concept_group in groups if isinstance(groups, list) else []:
        if not isinstance(concept_group, dict):
            continue
        props = concept_group.get("conceptProperties", [])
        for item in props if isinstance(props, list) else []:
            if not isinstance(item, dict):
                continue
            rxcui = str(item.get("rxcui", "")).strip()
            name = str(item.get("name", "")).strip()
            tty = str(item.get("tty", concept_group.get("tty", ""))).strip()
            if not rxcui or not name:
                continue
            key = (rxcui, name.casefold())
            if key in seen:
                continue
            seen.add(key)
            items.append({"rxcui": rxcui, "name": name, "term_type": tty})
            if len(items) >= MAX_RESULTS:
                break
        if len(items) >= MAX_RESULTS:
            break

    return {
        "status": "found" if items else "not_found",
        "query": term,
        "items": items,
        "source_url": url,
    }


def _label_metadata(record: dict[str, Any], query_term: str) -> dict[str, Any] | None:
    openfda = record.get("openfda", {})
    if not isinstance(openfda, dict):
        openfda = {}

    def first(name: str) -> str:
        value = openfda.get(name, [])
        if isinstance(value, list):
            value = value[0] if value else ""
        return str(value).strip() if value is not None else ""

    set_id = str(record.get("set_id", "")).strip()
    effective_time = str(record.get("effective_time", "")).strip()
    brand = first("brand_name")
    generic = first("generic_name")
    manufacturer = first("manufacturer_name")
    product_type = first("product_type")
    route = first("route")
    dosage_form = first("dosage_form")
    if not any((set_id, effective_time, brand, generic)):
        return None

    if set_id and re.fullmatch(r"[A-Fa-f0-9-]{8,80}", set_id):
        label_url = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=" + set_id
    else:
        label_url = DAILYMED_SEARCH + "?" + urlencode({"query": query_term})

    return {
        "brand_name": brand,
        "generic_name": generic,
        "manufacturer": manufacturer,
        "product_type": product_type,
        "route": route,
        "dosage_form": dosage_form,
        "effective_time": effective_time,
        "label_set_id": set_id,
        "dailymed_url": label_url,
        "metadata_only": True,
    }


def search_openfda_label_metadata(
    medicine_name: str,
    *,
    fetch_json: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Retrieve at most five label metadata records; never copy label text."""
    term = validate_medicine_name(medicine_name)
    fetch = fetch_json or _fetch_json
    records: list[dict[str, Any]] = []
    query_used = ""

    # Search separately to keep each query simple and prevent user input from
    # being interpreted as openFDA field/operator syntax.
    for field in ("openfda.generic_name", "openfda.brand_name"):
        search = '%s:"%s"' % (field, term.replace("\\", "\\\\").replace('"', '\\"'))
        url = OPENFDA_BASE + "?" + urlencode({"search": search, "limit": str(MAX_RESULTS)})
        try:
            data = _invoke_fetch(fetch, url)
        except PublicDrugDataNotFound:
            continue
        except PublicDrugDataError:
            if not records:
                return {
                    "status": "unavailable",
                    "query": term,
                    "items": [],
                    "source_url": url,
                }
            break

        query_used = url
        results = data.get("results", [])
        if not isinstance(results, list):
            continue
        for record in results:
            if not isinstance(record, dict):
                continue
            item = _label_metadata(record, term)
            if item:
                records.append(item)
            if len(records) >= MAX_RESULTS:
                break
        if records:
            break

    # Remove duplicates by manufacturer/name/set-id.
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in records:
        key = (
            str(item.get("label_set_id", "")),
            str(item.get("generic_name", "")).casefold(),
            str(item.get("brand_name", "")).casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= MAX_RESULTS:
            break

    return {
        "status": "found" if deduped else "not_found",
        "query": term,
        "items": deduped,
        "source_url": query_used or (
            DAILYMED_SEARCH + "?" + urlencode({"query": term})
        ),
    }




def search_openfda_label_sections(
    medicine_name: str,
    *,
    fetch_json: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Retrieve short source-linked label sections for human reference only.

    Only a standalone medicine name is sent. This is not an indication match,
    interaction check, safety conclusion, or recommendation engine.
    """
    term = validate_medicine_name(medicine_name)
    fetch = fetch_json or _fetch_json
    records: list[dict[str, Any]] = []
    source_url = ""

    for field in ("openfda.generic_name", "openfda.brand_name"):
        search = '%s:"%s"' % (field, term.replace("\\", "\\\\").replace('"', '\\"'))
        # openFDA label searches support search/limit. Do not rely on an
        # undocumented field-selection parameter; the documented API returns
        # whole label records, which are bounded here by a small result limit.
        params = {
            "search": search,
            "limit": str(LABEL_REFERENCE_QUERY_LIMIT),
        }
        url = OPENFDA_BASE + "?" + urlencode(params)
        source_url = url
        try:
            data = _invoke_fetch(fetch, url)
        except PublicDrugDataNotFound:
            continue
        except PublicDrugDataError:
            if not records:
                return {
                    "status": "unavailable",
                    "query": term,
                    "items": [],
                    "source_url": url,
                    "reference_only": True,
                }
            break

        results = data.get("results", [])
        if not isinstance(results, list):
            continue
        for record in results:
            if not isinstance(record, dict):
                continue
            metadata = _label_metadata(record, term)
            if not metadata:
                continue
            sections = []
            for field_name, heading in LABEL_REFERENCE_SECTIONS.items():
                raw = record.get(field_name, [])
                if isinstance(raw, list):
                    raw = raw[0] if raw else ""
                text = str(raw).strip() if raw is not None else ""
                if not text:
                    continue
                sections.append({
                    "field": field_name,
                    "heading": heading,
                    "excerpt": text[:MAX_LABEL_SECTION_CHARS],
                    "truncated": len(text) > MAX_LABEL_SECTION_CHARS,
                })
            records.append({
                **metadata,
                "sections": sections,
                "reference_only": True,
                "full_label_link": metadata.get("dailymed_url"),
            })
            if len(records) >= MAX_LABEL_REFERENCE_RESULTS:
                break
        if records:
            break

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in records:
        key = str(item.get("label_set_id", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= MAX_LABEL_REFERENCE_RESULTS:
            break

    return {
        "status": "found" if deduped else "not_found",
        "query": term,
        "items": deduped,
        "source_url": source_url or (DAILYMED_SEARCH + "?" + urlencode({"query": term})),
        "reference_only": True,
        "patient_context_sent": False,
        "interaction_check_performed": False,
        "note": (
            "Short excerpts from FDA-submitted label records for clinician reference only. "
            "openFDA says not to rely on its data alone for medical-care decisions. "
            "The excerpt may be incomplete, the product may not match the locally available product, "
            "and no patient-specific indication, contraindication, dose or interaction assessment was performed."
        ),
    }


def lookup_public_drug_metadata(
    medicine_name: str,
    *,
    fetch_json: Callable[..., dict[str, Any]] | None = None,
    include_label_sections: bool = False,
) -> dict[str, Any]:
    """Lookup medicine-name metadata; optionally add label excerpts for human reference.

    Do not pass patient-specific case data. Label excerpts are not a clinical
    recommendation or an interaction check.
    """
    term = validate_medicine_name(medicine_name)
    fetch = fetch_json or _fetch_json
    rxnorm = search_rxnorm(term, fetch_json=fetch)
    labels = search_openfda_label_metadata(term, fetch_json=fetch)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = {
        "status": "found" if rxnorm["status"] == "found" or labels["status"] == "found" else (
            "unavailable" if rxnorm["status"] == "unavailable" or labels["status"] == "unavailable" else "not_found"
        ),
        "lookup_term": term,
        "retrieved_at_utc": now,
        "external_query_scope": "standalone_medicine_name_only",
        "patient_context_sent": False,
        "clinical_recommendation_provided": False,
        "interaction_check_performed": False,
        "source_notice": (
            "Metadata discovery only. This lookup does not recommend, prescribe, dose, "
            "diagnose, or check drug interactions. Patient-specific case context is not sent. "
            "Confirm the current product label and "
            "evaluate the actual clinical question using appropriate clinical guidance."
        ),
        "rxnorm": rxnorm,
        "openfda_labels": labels,
    }
    if include_label_sections:
        result["label_reference"] = search_openfda_label_sections(term, fetch_json=fetch)
    return result
