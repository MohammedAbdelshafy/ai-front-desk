"""Local clinician-facing demo for Dr. Mia's evidence-review foundation.

Synthetic data only. This is not an EHR or a clinical decision support service.
The server binds to loopback and does not persist case submissions. It makes
no external calls unless the user explicitly opts into the standalone medicine-name
lookup; only that name is sent to public NLM/FDA metadata APIs. A matching evidence
card is not a medication recommendation.
"""
from __future__ import annotations

from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs
import argparse
import html
import json

from .medication_support import ClinicianCase, build_evidence_review, load_registry
from .public_drug_data import lookup_public_drug_metadata
from .pharmacology_education import search_pharmacology_education
from .knowledge_library import search_knowledge_library

BASE = Path(__file__).resolve().parent
REGISTRY_PATH = BASE / "medication_evidence_registry.json"
INFORMATION_CENTERS_PATH = BASE / "clinical_information_centers.json"
MAX_BODY = 16 * 1024
ALLOWED_JURISDICTIONS = {"US"}
FACTOR_LABELS = {
    "age": "Age and age-relevant factors reviewed",
    "allergies": "Reported allergies and reactions reviewed",
    "current_medications": "Current medicines and supplements reviewed",
    "medical_history": "Relevant medical history reviewed",
    "pregnancy_status": "Pregnancy status where relevant reviewed",
    "renal_function": "Renal function where relevant reviewed",
    "hepatic_function": "Hepatic function where relevant reviewed",
    "weight": "Weight where relevant reviewed",
}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _one(form: Mapping[str, Any], key: str, default: str = "") -> str:
    raw = form.get(key, default)
    if isinstance(raw, list):
        raw = raw[0] if raw else default
    if not isinstance(raw, str):
        return default
    return raw.strip()


def _split_values(value: str, limit: int = 12) -> tuple[str, ...]:
    items = []
    for raw in value.replace("\r", "\n").replace(",", "\n").split("\n"):
        item = raw.strip()
        if item and item not in items:
            items.append(item[:120])
        if len(items) >= limit:
            break
    return tuple(items)


def case_from_form(form: Mapping[str, Any]) -> ClinicianCase:
    case_id = _one(form, "case_id", "synthetic-case-001")[:64]
    assessment = _one(form, "proposed_assessment")[:800]
    symptoms = _split_values(_one(form, "symptoms"), limit=10)
    jurisdiction = _one(form, "jurisdiction", "US")
    if jurisdiction not in ALLOWED_JURISDICTIONS:
        raise ValueError("This demo is limited to the US jurisdiction.")
    reported_allergies = _one(form, "reported_allergies")[:1200]
    current_medications = _one(form, "current_medications")[:1200]
    relevant_medical_history = _one(form, "relevant_medical_history")[:1200]
    checked_factors = {
        name for name in FACTOR_LABELS
        if _one(form, "reviewed_" + name).lower() in {"1", "true", "on", "yes"}
    }
    # A checked box cannot stand in for recording the relevant synthetic fact.
    if not reported_allergies:
        checked_factors.discard("allergies")
    if not current_medications:
        checked_factors.discard("current_medications")
    reviewed = tuple(name for name in FACTOR_LABELS if name in checked_factors)
    risk_tags = _split_values(_one(form, "patient_risk_tags"), limit=12)
    return ClinicianCase(
        case_id=case_id,
        proposed_assessment=assessment,
        symptoms=symptoms,
        jurisdiction=jurisdiction,
        reviewed_factors=reviewed,
        patient_risk_tags=risk_tags,
        reported_allergies=reported_allergies,
        current_medications=current_medications,
        relevant_medical_history=relevant_medical_history,
    )


def run_review(form: Mapping[str, Any]) -> tuple[dict[str, Any], ClinicianCase]:
    case = case_from_form(form)
    sources, cards = load_registry(REGISTRY_PATH)
    return build_evidence_review(case, sources, cards), case


def _checked(value: bool) -> str:
    return " checked" if value else ""


def _render_flags(review: dict[str, Any]) -> str:
    flags = review.get("flags", [])
    if not flags:
        return "<p class='muted'>No automated review prompts were generated. This does not establish clinical safety.</p>"
    out = ["<div class='flags'><h3>Review prompts</h3>"]
    for flag in flags:
        out.append(
            "<article class='flag'><strong>%s</strong><p>%s</p></article>"
            % (esc(flag.get("code", "review_required")), esc(flag.get("message", "")))
        )
    out.append("</div>")
    return "".join(out)


def _render_quality_checklist(review: dict[str, Any]) -> str:
    checks = review.get("quality_checklist", [])
    if not checks:
        return ""
    out = [
        "<section class='quality-checklist'><h3>Clinical quality checklist</h3>"
        "<p class='muted'>Completeness prompts only. This is not a clinical quality score or a safety determination.</p>"
        "<ul class='quality-grid'>"
    ]
    attention = {"missing", "not_entered", "review_required", "no_verified_evidence", "required"}
    for item in checks:
        state = str(item.get("state", "review_required"))
        css = "attention" if state in attention else "recorded"
        out.append(
            "<li class='quality-item'><div class='quality-item-top'><strong>%s</strong>"
            "<span class='quality-state %s'>%s</span></div><p>%s</p></li>"
            % (
                esc(item.get("label", "")),
                css,
                esc(state.replace("_", " ")),
                esc(item.get("detail", "")),
            )
        )
    out.append("</ul></section>")
    return "".join(out)


def _render_public_lookup(lookup: dict[str, Any] | None) -> str:
    if lookup is None:
        return ""
    rxnorm = lookup.get("rxnorm", {})
    labels = lookup.get("openfda_labels", {})
    out = [
        "<section class='public-lookup'><div class='eyebrow'>Public source lookup</div>"
        "<h2>Medication identity &amp; label metadata</h2>"
        "<p class='muted'>Metadata discovery only. This is not a prescribing recommendation, a drug-interaction check, or a safety conclusion.</p>"
        "<p><strong>Lookup:</strong> %s · <strong>Status:</strong> %s</p>"
        % (esc(lookup.get("lookup_term", "")), esc(str(lookup.get("status", "unknown")).replace("_", " ")))
    ]
    out.append("<h3>RxNorm medication identity</h3>")
    rx_items = rxnorm.get("items", [])
    if rxnorm.get("status") == "unavailable":
        out.append("<p>RxNorm is temporarily unavailable. No identity result was returned.</p>")
    elif not rx_items:
        out.append("<p>No RxNorm identity match was returned for this term.</p>")
    else:
        out.append("<ul>")
        for item in rx_items:
            out.append("<li><strong>%s</strong> · RxCUI %s · %s</li>" % (
                esc(item.get("name", "")), esc(item.get("rxcui", "")), esc(item.get("term_type", ""))
            ))
        out.append("</ul>")
    out.append("<h3>openFDA label-record metadata</h3>")
    label_items = labels.get("items", [])
    if labels.get("status") == "unavailable":
        out.append("<p>openFDA is temporarily unavailable. No label metadata was returned.</p>")
    elif not label_items:
        out.append("<p>No openFDA label metadata match was returned. Try the generic ingredient or brand name separately.</p>")
    else:
        for item in label_items:
            out.append(
                "<article class='evidence-card'><h3>%s</h3>"
                "<p><strong>Generic name:</strong> %s</p><p><strong>Manufacturer:</strong> %s</p>"
                "<p><strong>Product type:</strong> %s · <strong>Route:</strong> %s · <strong>Dosage form:</strong> %s</p>"
                "<p><strong>Label effective time:</strong> %s</p>"
                "<p><a href='%s' target='_blank' rel='noopener noreferrer'>Open corresponding DailyMed label/search</a></p>"
                "<p class='muted'>Metadata record only. Confirm the current product-specific label; submitted labeling can differ from currently distributed or approved labeling.</p></article>"
                % (
                    esc(item.get("brand_name") or item.get("generic_name") or "Drug label record"),
                    esc(item.get("generic_name", "")), esc(item.get("manufacturer", "")),
                    esc(item.get("product_type", "")), esc(item.get("route", "")),
                    esc(item.get("dosage_form", "")), esc(item.get("effective_time", "")),
                    esc(item.get("dailymed_url", "")),
                )
            )
    out.append(
        "<p class='muted'>This lookup sent only the standalone medicine name to RxNorm/openFDA. "
        "The clinical case, symptoms, allergies, current medicines, medical history, and patient identifiers were not sent.</p>"
        "<p class='muted'>NLM attribution: This product uses publicly available data from the U.S. National Library of Medicine (NLM), "
        "National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.</p>"
        "</section>"
    )
    return "".join(out)


def _render_education_search(result: dict[str, Any] | None) -> str:
    if result is None:
        return ""
    out = [
        "<section class='education-search'><div class='eyebrow'>Open-license learning shelf</div>"
        "<h2>Pharmacology foundations</h2>"
        "<p class='muted'>Local, source-linked education notes. These do not recommend or prescribe medicines.</p>"
        "<p><strong>Topic:</strong> %s · <strong>Result:</strong> %s</p>"
        % (esc(result.get("query", "")), esc(str(result.get("status", "unknown")).replace("_", " ")))
    ]
    items = result.get("results", [])
    if not items:
        out.append("<p>No matching learning note was found. This is not a clinical answer.</p>")
    for item in items:
        out.append(
            "<article class='education-card'><h3>%s</h3><p>%s</p><ul>%s</ul>"
            "<p class='muted'><strong>Scope:</strong> %s</p><p class='muted'><strong>Cannot support:</strong> %s</p>"
            "<div class='education-sources'><strong>Source references and licenses</strong>"
            % (
                esc(item.get("title", "")),
                esc(item.get("summary", "")),
                "".join("<li>%s</li>" % esc(point) for point in item.get("learning_points", [])),
                esc(item.get("use_scope", "education_only")),
                esc(", ".join(item.get("cannot_support", []))),
            )
        )
        for source in item.get("source_refs", []):
            out.append(
                "<p><a href='%s' target='_blank' rel='noopener noreferrer'>%s</a><br>"
                "<span class='muted'>%s · <a href='%s' target='_blank' rel='noopener noreferrer'>License/source terms</a></span><br>"
                "<span class='muted'>%s</span></p>"
                % (
                    esc(source.get("url", "")), esc(source.get("title", "")),
                    esc(source.get("license_id", "")), esc(source.get("license_url", "")),
                    esc(source.get("attribution", "")),
                )
            )
        out.append("</div></article>")
    out.append(
        "<p class='muted'>These are concise learning summaries grounded in the cited materials. "
        "The shelf is not a current medication monograph library, dental prescribing guideline, interaction checker, or patient-specific clinical decision.</p></section>"
    )
    return "".join(out)


def _render_knowledge_library(result: dict[str, Any] | None) -> str:
    if result is None:
        return ""
    out = [
        "<section class='education-search fulltext-search'><div class='eyebrow'>Local full-text book library</div>"
        "<h2>Searchable source passages</h2>"
        "<p class='muted'>Offline search across rights-cleared text imported to this machine. Every result retains source, license, edition, and section provenance.</p>"
        "<p><strong>Topic:</strong> %s · <strong>Status:</strong> %s</p>"
        % (esc(result.get("query", "")), esc(str(result.get("status", "unknown")).replace("_", " ")))
    ]
    items = result.get("results", [])
    if not items:
        out.append("<p>%s</p>" % esc(result.get("message", "No indexed source passage was found.")))
    for item in items:
        out.append(
            "<article class='education-card'><h3>%s</h3>"
            "<p><strong>Section:</strong> %s · <strong>Edition/version:</strong> %s</p>"
            "<p class='corpus-excerpt'>%s</p>"
            "<p class='muted'><strong>License:</strong> %s · <strong>Indexed:</strong> %s</p>"
            "<p><a href='%s' target='_blank' rel='noopener noreferrer'>Open original source</a></p>"
            "<p class='muted'>Attribution: %s</p>"
            "<p class='muted'>Education only. This passage is not an approved clinical recommendation.</p></article>"
            % (
                esc(item.get("source_title", "")),
                esc(item.get("section", "Section not captured")),
                esc(item.get("edition_or_version", "Version not captured")),
                esc(item.get("text", "")),
                esc(item.get("license_id", "")),
                esc(item.get("indexed_on", "")),
                esc(item.get("source_url", "")),
                esc(item.get("attribution", "")),
            )
        )
    out.append(
        "<p class='muted'>Book passages are retrieved locally and are not sent to an external service. "
        "A textbook passage cannot qualify as approved clinical evidence, a drug-interaction result, or a patient-specific prescribing recommendation.</p></section>"
    )
    return "".join(out)


def _render_evidence(review: dict[str, Any]) -> str:
    items = review.get("matched_evidence", [])
    if not items:
        return (
            "<section class='empty-evidence'><h3>No verified evidence found</h3>"
            "<p>The registry contains no currently approved evidence cards for this demo. "
            "Do not infer that a medicine is appropriate or safe. Check approved clinical references "
            "and consult a supervising clinician.</p></section>"
        )
    out = [
        "<div class='notice'><strong>Evidence retrieval only.</strong> "
        "A source match is not a medication recommendation or a safety conclusion.</div>"
    ]
    for item in items:
        ref = item.get("source_reference", {})
        link = esc(ref.get("url", ""))
        out.append(
            "<article class='evidence-card'><div class='eyebrow'>Source-mentioned medicine/class</div>"
            "<h3>%s</h3><p>%s</p><p><strong>Reference:</strong> %s · %s</p>"
            "<p><strong>Section/page:</strong> %s</p>"
            "<p><strong>Edition/version:</strong> %s %s</p>"
            "<p><strong>Review:</strong> %s · due %s</p>"
            "<p><a href='%s' target='_blank' rel='noopener noreferrer'>Open cited reference</a></p>"
            "<p class='muted'>Patient-specific medication safety assessment was not performed by this module.</p></article>"
            % (
                esc(item.get("medicine_or_class_mentioned_in_source", "")),
                esc(item.get("evidence_summary", "")),
                esc(ref.get("title", "")), esc(ref.get("publisher", "")),
                esc(ref.get("section_or_page", "")),
                esc(ref.get("edition", "")), esc(ref.get("version", "")),
                esc(ref.get("evidence_reviewed_on", "")), esc(ref.get("review_due_on", "")),
                link,
            )
        )
    return "".join(out)


def _render_information_centers(jurisdiction: str = "US") -> str:
    """Render official reference links without treating them as approved evidence."""
    try:
        with INFORMATION_CENTERS_PATH.open("r", encoding="utf-8") as handle:
            catalog = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return (
            "<section class='source-directory'><div class='eyebrow'>Clinical information centers</div>"
            "<p>The source directory could not be loaded. No recommendation has been generated from it.</p></section>"
        )
    sources = catalog.get("sources", []) if isinstance(catalog, dict) else []
    matched = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        jurisdictions = source.get("jurisdictions", [])
        if jurisdiction not in jurisdictions and "global_evidence_discovery" not in jurisdictions:
            continue
        url = str(source.get("url", ""))
        if not url.startswith(("https://", "http://")):
            continue
        matched.append(source)
    out = [
        "<section class='source-directory'><div class='eyebrow'>Official reference links</div>"
        "<h2>%s information centers</h2>"
        "<p class='muted'>Open primary sources for clinician review. These links are not approved evidence cards and do not generate or validate a medication recommendation.</p>"
        % esc("US" if jurisdiction == "US" else jurisdiction)
    ]
    if not matched:
        out.append("<p>No source links are cataloged for this jurisdiction. Do not borrow another country's guidance.</p>")
    for source in matched:
        roles = source.get("roles", [])
        role_text = ", ".join(str(item).replace("_", " ") for item in roles[:3])
        status = str(source.get("clinical_status", source.get("integration_status", "reference only")))
        out.append(
            "<article class='source-link'><a href='%s' target='_blank' rel='noopener noreferrer'>%s</a>"
            "<p>%s</p><p>Role: %s</p><p class='source-status'>Status: %s</p></article>"
            % (
                esc(source.get("url", "")),
                esc(source.get("name", source.get("title", "Reference source"))),
                esc(source.get("publisher", "")),
                esc(role_text or "General reference"),
                esc(status.replace("_", " ")),
            )
        )
    out.append(
        "<p class='muted'>Source pages may change and may carry reuse restrictions. Mia does not scrape these pages or turn them into recommendations automatically. Only current, jurisdiction-matched, rights-cleared, clinician-approved evidence cards can support clinical retrieval. The DDI provider is not currently integrated.</p></section>"
    )
    return "".join(out)


def render_page(
    form: Mapping[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    error: str = "",
    public_lookup: dict[str, Any] | None = None,
    education_result: dict[str, Any] | None = None,
    knowledge_result: dict[str, Any] | None = None,
) -> str:
    form = form or {}
    value = lambda name, default="": esc(_one(form, name, default))
    checked = lambda name: _checked(_one(form, "reviewed_" + name).lower() in {"1", "true", "on", "yes"})
    factors = "".join(
        "<label class='check'><input type='checkbox' name='reviewed_%s' value='1'%s> %s</label>"
        % (esc(key), checked(key), esc(label))
        for key, label in FACTOR_LABELS.items()
    )
    result_html = ""
    if review is not None:
        evidence_state = review.get("status", "needs_clinician_input")
        result_html = (
            "<section class='results' aria-live='polite'><div class='result-head'><div>"
            "<div class='eyebrow'>Workbench result</div><h2>%s</h2></div>"
            "<span class='pill'>Human review required</span></div>"
            "<p>%s</p><div class='context-grid'>"
            "<article><h3>Reported allergies</h3><p>%s</p></article>"
            "<article><h3>Current medicines</h3><p>%s</p></article>"
            "<article><h3>Relevant history</h3><p>%s</p></article></div>"
            "%s%s%s%s%s%s<p class='disclaimer'>This demo does not diagnose, prescribe, calculate doses, "
            "or perform comprehensive interaction checks. Submitted cases are not saved. External APIs are queried only when you explicitly check the public lookup box, and only the standalone medicine name is sent. The learning notes and full-text book library are local-only.</p></section>"
            % (
                esc(evidence_state.replace("_", " ").title()),
                esc(review.get("message", "")),
                esc(review.get("clinical_context_summary", {}).get("reported_allergies", "Not entered")),
                esc(review.get("clinical_context_summary", {}).get("current_medications", "Not entered")),
                esc(review.get("clinical_context_summary", {}).get("relevant_medical_history", "Not entered")),
                _render_quality_checklist(review),
                _render_flags(review),
                _render_evidence(review),
                _render_public_lookup(public_lookup),
                _render_education_search(education_result),
                _render_knowledge_library(knowledge_result),
            )
        )
    error_html = "<div class='error'>%s</div>" % esc(error) if error else ""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>Dr. Mia · Clinical Evidence Workbench</title>
<style>
:root{color-scheme:light;--ink:#12313d;--muted:#60747d;--teal:#087f8c;--line:#d7e5e7;--wash:#f2f8f8;--white:#fff;--amber:#fff4d7}
*{box-sizing:border-box}body{margin:0;background:#f7faf9;color:var(--ink);font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:1050px;margin:0 auto;padding:20px}.banner{padding:10px 16px;background:#fff1c2;border-bottom:1px solid #e5d08d;color:#634a00;font-size:13px;font-weight:650}
header{display:flex;align-items:center;gap:16px;padding:22px 0 18px}.avatar{width:70px;height:70px;object-fit:cover;object-position:top center;border-radius:18px;border:1px solid var(--line);background:#d8eeee}
h1{font-size:clamp(26px,4vw,36px);line-height:1.1;letter-spacing:-.04em;margin:0 0 7px}h2{font-size:22px;margin:0}h3{font-size:15px;margin:0 0 8px}.sub{margin:0;color:var(--muted);max-width:720px}.eyebrow{text-transform:uppercase;letter-spacing:.1em;font-size:11px;font-weight:800;color:var(--teal)}
.layout{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(270px,.85fr);gap:18px;align-items:start}.panel,.results{background:var(--white);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 6px 18px rgba(13,53,61,.04)}
label{display:block;font-weight:650;font-size:13px;margin:14px 0 6px}input[type=text],textarea,select{width:100%%;padding:11px 12px;border:1px solid #bed1d5;border-radius:10px;font:inherit;color:var(--ink);background:#fff}
textarea{min-height:74px;resize:vertical}.hint,.muted{font-size:12px;color:var(--muted)}.hint{margin:5px 0 0}
.factor-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:9px}.check{display:flex;align-items:flex-start;gap:7px;margin:0;padding:9px;background:var(--wash);border:1px solid #e0ebec;border-radius:9px;font-weight:500;font-size:12px}.check input{margin-top:4px}
button{margin-top:18px;background:var(--teal);color:#fff;border:0;padding:12px 17px;border-radius:10px;font-weight:750;font-size:14px;cursor:pointer}button:hover{background:#056c76}
.note{background:#eff8f7;border:1px solid #d0e9e5;padding:12px 14px;border-radius:12px;font-size:13px}.note strong{display:block;margin-bottom:4px}.error{margin:12px 0;padding:12px;background:#ffe8e8;border:1px solid #f4bcbc;border-radius:10px;color:#8c2020}
.public-query-panel{margin-top:22px;border:1px dashed #9cc7cc;padding:14px;border-radius:12px;background:#f8fcfc}.public-query-panel .check{margin-top:9px}.public-lookup{margin-top:18px;border:1px solid var(--line);border-radius:14px;padding:16px;background:#fff}.public-lookup h2{font-size:20px;margin:5px 0 12px}.public-lookup h3{margin-top:18px}.public-lookup li{font-size:13px;margin:8px 0;overflow-wrap:anywhere}.public-lookup a{color:#086e7b;font-weight:700}
.education-query-panel{margin-top:16px;border:1px solid #c6d6f4;padding:14px;border-radius:12px;background:#f4f7ff}.education-query-panel .check{margin-top:9px}.education-search{margin-top:18px;border:1px solid #d5e1f6;border-radius:14px;padding:16px;background:#fcfdff}.education-search h2{font-size:20px;margin:5px 0 12px}.education-card{border:1px solid #d5e1f6;border-radius:12px;background:#fff;padding:14px;margin:12px 0}.education-card h3{margin-top:0}.education-card li{font-size:13px;margin:5px 0}.education-sources{border-top:1px solid #e4eaf7;padding-top:10px;margin-top:10px}.education-sources p{font-size:12px;overflow-wrap:anywhere}.education-sources a{color:#3557b7;font-weight:700}
.results{margin-top:18px}.result-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.pill{font-size:11px;font-weight:750;border-radius:30px;background:#e5f4ef;color:#13644e;padding:7px 10px}.context-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0}.context-grid article{padding:12px;border:1px solid var(--line);background:#fbfdfd;border-radius:12px;overflow-wrap:anywhere}.context-grid p{margin:0;white-space:pre-wrap;font-size:13px}
.flags{margin:20px 0}.flag{border-left:3px solid #bd7d00;background:var(--amber);padding:10px 12px;margin:8px 0;border-radius:6px}.flag p{margin:4px 0 0;font-size:13px}
.quality-checklist{margin:20px 0}.quality-grid{list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:12px 0}.quality-item{border:1px solid var(--line);border-radius:10px;padding:11px;background:#fbfdfd;min-width:0}.quality-item-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}.quality-item strong{font-size:12px}.quality-item p{font-size:12px;color:var(--muted);margin:6px 0 0}.quality-state{font-size:10px;text-transform:uppercase;letter-spacing:.05em;font-weight:800;padding:4px 6px;border-radius:20px;background:#e1f4eb;color:#146049;white-space:nowrap}.quality-state.attention{background:#fff0c9;color:#815100}
.source-directory{margin-top:18px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 6px 18px rgba(13,53,61,.04)}.source-directory h2{font-size:18px;margin:5px 0 8px}.source-directory .source-link{padding:10px 0;border-top:1px solid #e2ecee}.source-directory .source-link a{font-size:13px;color:#086e7b;font-weight:750;overflow-wrap:anywhere}.source-directory .source-link p{font-size:11px;color:var(--muted);margin:4px 0 0}.source-directory .source-status{font-weight:750;text-transform:capitalize}
.empty-evidence{background:#f2f7f8;border:1px dashed #aac4c9;border-radius:12px;padding:15px;margin-top:14px}.empty-evidence h3{color:#7a5200}.empty-evidence p{font-size:13px;margin-bottom:0}
.notice{background:#e8f5f2;border:1px solid #c5e7dd;padding:12px;border-radius:10px;margin-top:12px;font-size:13px}.evidence-card{border:1px solid var(--line);border-radius:12px;padding:14px;margin-top:12px;overflow-wrap:anywhere}.evidence-card p{font-size:13px;margin:8px 0}.evidence-card a{color:#086e7b;font-weight:700}
.disclaimer{border-top:1px solid var(--line);padding-top:12px;color:var(--muted);font-size:12px;margin-top:18px}
footer{margin:25px 0 10px;color:var(--muted);font-size:12px}
@media(max-width:780px){.layout{grid-template-columns:1fr}.context-grid{grid-template-columns:1fr}.factor-grid{grid-template-columns:1fr}.quality-grid{grid-template-columns:1fr}header{align-items:flex-start}.avatar{width:58px;height:58px;flex-basis:58px}.wrap{padding:14px}}
</style></head><body>
<div class="banner">LOCAL DEMO ONLY · USE SYNTHETIC CASES · DO NOT ENTER REAL PATIENT IDENTIFIERS OR HEALTH INFORMATION</div>
<main class="wrap">
<header><img class="avatar" src="/assets/mia-stand-hi.webp" alt="Mia, AI clinical assistant"><div>
<div class="eyebrow">Dentistry · evidence workbench prototype</div><h1>Dr. Mia</h1>
<p class="sub">Clinical quality &amp; prescribing copilot. Evidence retrieval and review prompts for a clinician, not an automated prescriber.</p>
</div></header>
<div class="layout"><section class="panel"><div class="eyebrow">Clinician workspace</div><h2 style="margin-top:5px">Review a synthetic case</h2>
<p class="hint">The current evidence registry is intentionally unpopulated until sources receive rights review and qualified clinical approval.</p>
%s
<form action="/" method="post" autocomplete="off">
<label for="case_id">Non-identifying demo case reference</label><input id="case_id" name="case_id" maxlength="64" value="%s" required>
<p class="hint">Use a reference such as synthetic-case-001, never a patient name, date of birth, or chart number.</p>
<label for="proposed_assessment">Clinician-entered working assessment</label><textarea id="proposed_assessment" name="proposed_assessment" maxlength="800" placeholder="Enter a synthetic scenario for source retrieval, not a real patient case." required>%s</textarea>
<label for="symptoms">Symptoms (synthetic)</label><textarea id="symptoms" name="symptoms" maxlength="1200" placeholder="Separate sample symptoms with commas or new lines">%s</textarea>
<label for="reported_allergies">Reported allergies / reactions (synthetic)</label><textarea id="reported_allergies" name="reported_allergies" maxlength="1200" placeholder="Demo-only context, e.g. fictional allergy note">%s</textarea><p class="hint">Record a synthetic answer such as “none reported” or “unknown” when relevant; do not mark this factor reviewed while the field is blank.</p>
<label for="current_medications">Current medicines / supplements (synthetic)</label><textarea id="current_medications" name="current_medications" maxlength="1200" placeholder="Demo-only context">%s</textarea><p class="hint">Record “none reported” or “unknown” when applicable; do not mark this factor reviewed while the field is blank.</p>
<label for="relevant_medical_history">Relevant medical history (synthetic)</label><textarea id="relevant_medical_history" name="relevant_medical_history" maxlength="1200" placeholder="Demo-only context">%s</textarea>
<label for="patient_risk_tags">Reviewer-configured caution tags (demo only)</label><input type="text" id="patient_risk_tags" name="patient_risk_tags" maxlength="800" value="%s" placeholder="comma-separated reviewer tags">
<div class="public-query-panel">
<div class="eyebrow">Optional free public data lookup</div>
<label for="drug_lookup_name">One medicine name or active ingredient</label>
<input type="text" id="drug_lookup_name" name="drug_lookup_name" maxlength="120" value="%s" placeholder="e.g. a generic ingredient or brand name">
<label class="check"><input type="checkbox" name="lookup_public_sources" value="1"%s> Look up medication identity and label metadata</label>
<p class="hint">Only use this for one standalone medicine name. When checked, only that name is sent to NLM RxNorm and openFDA. Never place a patient name, symptoms, allergies, medical history, or case details here. This is not an interaction checker.</p>
</div>
<div class="education-query-panel">
<div class="eyebrow">Local searchable book library + learning shelf</div>
<label for="learning_topic">Learning topic</label>
<input type="text" id="learning_topic" name="learning_topic" maxlength="180" value="%s" placeholder="e.g. pharmacokinetics, adverse effects, antimicrobials">
<label class="check"><input type="checkbox" name="search_learning_library" value="1"%s> Search source-linked notes and locally indexed book text</label>
<p class="hint">This lookup is local-only and makes no external calls. It searches the short study notes and, when you import rights-cleared textbook text, the local full-text library. Results are educational, not patient-specific prescribing advice.</p>
</div>
<label>Patient factors confirmed/reviewed in this synthetic case</label><div class="factor-grid">%s</div>
<label for="jurisdiction">Reference jurisdiction</label><select id="jurisdiction" name="jurisdiction"><option value="US" selected>United States (US)</option></select>
<div class="note" style="margin-top:16px"><strong>What this tool does not do</strong>
It does not diagnose, prescribe, calculate doses, or perform comprehensive drug-interaction checks. A source match is not a safety conclusion. Always consult approved current references and a supervising clinician.</div>
<button type="submit">Retrieve approved evidence</button>
</form></section>
<aside><section class="panel"><div class="eyebrow">Mia's operating rules</div><h2 style="margin-top:5px">Evidence before confidence</h2>
<p>Dr. Mia should be friendly and direct, but never confident without a source.</p>
<ul><li>Every evidence card must identify its source and section.</li><li>Expired, unapproved, unlicensed, or wrong-jurisdiction entries are excluded.</li><li>Missing patient factors create review prompts, not automatic clinical conclusions.</li><li>No evidence match means no recommendation.</li><li>All final clinical decisions remain with the treating dentist.</li></ul>
<div class="note"><strong>Current prototype status</strong>The source registry contains no approved medication entries, so a search should return “No verified evidence found.” That is an intentional safety behavior, not a failure.</div>
</section>%s</aside></div>
%s
<footer>Dr. Mia · Local prototype · No case persistence · No external API calls · Not for real patient use</footer>
</main></body></html>
""" % (
        error_html,
        value("case_id", "synthetic-case-001"),
        value("proposed_assessment"),
        value("symptoms"),
        value("reported_allergies"),
        value("current_medications"),
        value("relevant_medical_history"),
        value("patient_risk_tags"),
        value("drug_lookup_name"),
        _checked(_one(form, "lookup_public_sources").lower() in {"1", "true", "on", "yes"}),
        value("learning_topic"),
        _checked(_one(form, "search_learning_library").lower() in {"1", "true", "on", "yes"}),
        factors,
        _render_information_centers(_one(form, "jurisdiction", "US")),
        result_html,
    )


class WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "DrMiaWorkbench/0.1"

    def _send_html(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/":
            self._send_html(200, render_page())
            return
        if self.path == "/assets/mia-stand-hi.webp":
            asset = BASE / "static" / "mia-stand-hi.webp"
            try:
                data = asset.read_bytes()
            except OSError:
                self.send_error(404, "Mia artwork not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/webp")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            self._send_html(400, render_page(error="Invalid form body."))
            return
        if length <= 0 or length > MAX_BODY:
            self._send_html(413 if length > MAX_BODY else 400, render_page(error="Request body is empty or exceeds the demo limit."))
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/x-www-form-urlencoded":
            self._send_html(415, render_page(error="Expected a URL-encoded demo form."))
            return
        try:
            body = self.rfile.read(length).decode("utf-8", errors="strict")
            form = parse_qs(body, max_num_fields=40, keep_blank_values=True)
            if any(len(values[0]) > 1500 for values in form.values() if values):
                raise ValueError("One or more fields are too long.")
            review, case = run_review(form)
            public_lookup = None
            lookup_requested = _one(form, "lookup_public_sources").lower() in {"1", "true", "on", "yes"}
            drug_lookup_name = _one(form, "drug_lookup_name")
            if lookup_requested:
                if not drug_lookup_name:
                    raise ValueError("Enter one medicine name or active ingredient before enabling the public lookup.")
                # Only a single medicine name is sent. Clinical case details are
                # deliberately not passed to either external source.
                public_lookup = lookup_public_drug_metadata(drug_lookup_name)
            education_result = None
            knowledge_result = None
            education_requested = _one(form, "search_learning_library").lower() in {"1", "true", "on", "yes"}
            learning_topic = _one(form, "learning_topic")
            if education_requested:
                if not learning_topic:
                    raise ValueError("Enter a pharmacology learning topic before searching the learning shelf.")
                education_result = search_pharmacology_education(learning_topic)
                knowledge_result = search_knowledge_library(learning_topic)
            self._send_html(200, render_page(
                form, review, public_lookup=public_lookup,
                education_result=education_result, knowledge_result=knowledge_result,
            ))
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            self._send_html(400, render_page(error=str(exc)))
        except (OSError, KeyError) as exc:
            # Registry errors do not make a clinical claim; fail closed visibly.
            self._send_html(500, render_page(error="The evidence registry could not be loaded. No evidence was returned."))

    def log_message(self, format: str, *args: Any) -> None:
        # Avoid logging case data. Only print the route and status, never request bodies.
        super().log_message(format, *args)


def run(port: int = 8767) -> None:
    server = HTTPServer(("127.0.0.1", port), WorkbenchHandler)
    print("Dr. Mia Evidence Workbench at http://127.0.0.1:%d (synthetic data only)" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local synthetic-data Dr. Mia evidence workbench")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    run(args.port)


if __name__ == "__main__":
    main()
