"""Local clinician-facing demo for Dr. Mia's evidence-review foundation.

Synthetic data only. This is not an EHR or a clinical decision support service.
The server binds to loopback, does not persist case submissions, and makes no
external calls. A matching evidence card is not a medication recommendation.
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

BASE = Path(__file__).resolve().parent
REGISTRY_PATH = BASE / "medication_evidence_registry.json"
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
    reviewed = tuple(
        name for name in FACTOR_LABELS
        if _one(form, "reviewed_" + name).lower() in {"1", "true", "on", "yes"}
    )
    risk_tags = _split_values(_one(form, "patient_risk_tags"), limit=12)
    return ClinicianCase(
        case_id=case_id,
        proposed_assessment=assessment,
        symptoms=symptoms,
        jurisdiction=jurisdiction,
        reviewed_factors=reviewed,
        patient_risk_tags=risk_tags,
        reported_allergies=_one(form, "reported_allergies")[:1200],
        current_medications=_one(form, "current_medications")[:1200],
        relevant_medical_history=_one(form, "relevant_medical_history")[:1200],
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


def render_page(
    form: Mapping[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    error: str = "",
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
            "%s%s<p class='disclaimer'>This demo does not diagnose, prescribe, calculate doses, "
            "or perform comprehensive interaction checks. No information is saved or sent to an external service.</p></section>"
            % (
                esc(evidence_state.replace("_", " ").title()),
                esc(review.get("message", "")),
                esc(review.get("clinical_context_summary", {}).get("reported_allergies", "Not entered")),
                esc(review.get("clinical_context_summary", {}).get("current_medications", "Not entered")),
                esc(review.get("clinical_context_summary", {}).get("relevant_medical_history", "Not entered")),
                _render_flags(review),
                _render_evidence(review),
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
.results{margin-top:18px}.result-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.pill{font-size:11px;font-weight:750;border-radius:30px;background:#e5f4ef;color:#13644e;padding:7px 10px}.context-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0}.context-grid article{padding:12px;border:1px solid var(--line);background:#fbfdfd;border-radius:12px;overflow-wrap:anywhere}.context-grid p{margin:0;white-space:pre-wrap;font-size:13px}
.flags{margin:20px 0}.flag{border-left:3px solid #bd7d00;background:var(--amber);padding:10px 12px;margin:8px 0;border-radius:6px}.flag p{margin:4px 0 0;font-size:13px}
.empty-evidence{background:#f2f7f8;border:1px dashed #aac4c9;border-radius:12px;padding:15px;margin-top:14px}.empty-evidence h3{color:#7a5200}.empty-evidence p{font-size:13px;margin-bottom:0}
.notice{background:#e8f5f2;border:1px solid #c5e7dd;padding:12px;border-radius:10px;margin-top:12px;font-size:13px}.evidence-card{border:1px solid var(--line);border-radius:12px;padding:14px;margin-top:12px;overflow-wrap:anywhere}.evidence-card p{font-size:13px;margin:8px 0}.evidence-card a{color:#086e7b;font-weight:700}
.disclaimer{border-top:1px solid var(--line);padding-top:12px;color:var(--muted);font-size:12px;margin-top:18px}
footer{margin:25px 0 10px;color:var(--muted);font-size:12px}
@media(max-width:780px){.layout{grid-template-columns:1fr}.context-grid{grid-template-columns:1fr}.factor-grid{grid-template-columns:1fr}header{align-items:flex-start}.avatar{width:58px;height:58px;flex-basis:58px}.wrap{padding:14px}}
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
<label for="reported_allergies">Reported allergies / reactions (synthetic)</label><textarea id="reported_allergies" name="reported_allergies" maxlength="1200" placeholder="Demo-only context, e.g. fictional allergy note">%s</textarea>
<label for="current_medications">Current medicines / supplements (synthetic)</label><textarea id="current_medications" name="current_medications" maxlength="1200" placeholder="Demo-only context">%s</textarea>
<label for="relevant_medical_history">Relevant medical history (synthetic)</label><textarea id="relevant_medical_history" name="relevant_medical_history" maxlength="1200" placeholder="Demo-only context">%s</textarea>
<label for="patient_risk_tags">Reviewer-configured caution tags (demo only)</label><input type="text" id="patient_risk_tags" name="patient_risk_tags" maxlength="800" value="%s" placeholder="comma-separated reviewer tags">
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
</section></aside></div>
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
        factors,
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
            self._send_html(200, render_page(form, review))
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
