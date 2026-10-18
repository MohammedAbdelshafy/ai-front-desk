"""Local, source-routing workbench for hospital Obstetrics & Gynaecology review.

Synthetic data only. This is not an autonomous clinical decision support system.
The v1 workbench links official reference centers and surfaces explicit emergency
escalation prompts selected by the clinician. It does not diagnose, prescribe,
calculate doses, or provide patient-specific treatment protocols. No form values
are persisted and no external calls are made.
"""
from __future__ import annotations

import argparse
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from urllib.parse import parse_qs
from .avatar_customizer import AVATAR_ASSETS, render_avatar_customizer

BASE = Path(__file__).resolve().parent
DEFAULT_CATALOG_PATH = BASE / "obgyn_reference_centers.json"
MAX_BODY = 16 * 1024
ALLOWED_JURISDICTIONS = {"EG", "US", "UK", "GLOBAL"}

CARE_STAGES = {
    "preconception": "Preconception",
    "antenatal": "Pregnancy / antenatal care",
    "intrapartum": "Labour and birth",
    "postpartum": "Postpartum care",
    "gynaecology": "General gynaecology",
    "contraception": "Contraception and family planning",
    "fertility": "Fertility and reproductive endocrinology",
    "medication_pregnancy_lactation": "Medication during pregnancy or lactation",
    "gyn_oncology": "Gynaecologic oncology",
    "general": "General OB-GYN question",
}

STAGE_TERMS = {
    "preconception": ["preconception", "fertility", "pregnancy"],
    "antenatal": ["pregnancy", "antenatal", "preeclampsia", "hypertension pregnancy", "maternal health", "medications in pregnancy"],
    "intrapartum": ["labour", "intrapartum", "childbirth", "fetal monitoring", "postpartum haemorrhage", "maternal emergency"],
    "postpartum": ["postpartum", "breastfeeding", "lactation", "postpartum haemorrhage", "maternal emergency"],
    "gynaecology": ["gynaecology", "gynaecological", "ectopic pregnancy", "miscarriage", "gynecologic oncology", "maternal medicine"],
    "contraception": ["contraception", "contraceptive eligibility", "family planning", "postpartum contraception"],
    "fertility": ["fertility", "complications of fertility treatment", "gynaecology"],
    "medication_pregnancy_lactation": ["medications in pregnancy", "lactation", "breastfeeding", "pregnancy", "medicine label", "drug safety alerts"],
    "gyn_oncology": ["gynecologic oncology", "gynaecology", "systematic review", "clinical trials"],
    "general": [],
}

URGENT_PROMPTS = {
    "heavy_bleeding": ("Heavy bleeding / possible major blood loss", "Activate the hospital's emergency obstetric response and local haemorrhage protocol now."),
    "seizure": ("Seizure or loss of consciousness", "Activate the hospital emergency response immediately; follow local maternal emergency protocol."),
    "collapse": ("Collapse / shock / rapidly deteriorating condition", "Activate the hospital emergency response immediately."),
    "severe_breathlessness": ("Severe breathlessness or cyanosis", "Activate the hospital emergency response immediately."),
    "chest_pain": ("Chest pain or suspected thromboembolic emergency", "Activate the hospital emergency response immediately."),
    "severe_headache_visual": ("Severe headache, visual change, or other acute neurological concern in pregnancy/postpartum", "Urgent senior obstetric assessment and local emergency protocol are required."),
    "severe_abdominal_pain": ("Severe abdominal/pelvic pain, especially with pregnancy possibility or bleeding", "Urgent senior assessment; use the hospital's acute abdomen / early-pregnancy pathway."),
    "fever_sepsis": ("Fever with systemic illness, confusion, or suspected sepsis", "Activate the hospital's sepsis / maternal sepsis pathway immediately."),
    "reduced_fetal_movement": ("Reduced or absent fetal movement when movement is expected", "Urgent maternity assessment through the hospital's fetal-wellbeing pathway."),
    "postpartum_deterioration": ("Postpartum deterioration, severe pain, or new alarming symptoms", "Urgent senior review; use the hospital's postpartum emergency pathway."),
}

STAGE_EMERGENCY_TERMS = ["emergency", "haemorrhage", "hemorrhage", "preeclampsia", "eclampsia", "sepsis", "ectopic", "seizure", "collapse"]


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _one(form: Mapping[str, Any], key: str, default: str = "") -> str:
    raw = form.get(key, default)
    if isinstance(raw, list):
        raw = raw[0] if raw else default
    if not isinstance(raw, str):
        return default
    return raw.strip()


def _checked(form: Mapping[str, Any], key: str) -> bool:
    return _one(form, key).lower() in {"1", "true", "on", "yes"}


def load_sources(path: str | Path = DEFAULT_CATALOG_PATH) -> List[Dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise ValueError("unsupported OB-GYN source catalog schema")
    sources = raw.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise ValueError("OB-GYN source catalog must contain a sources array")
    ids = [item.get("id") for item in sources]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("OB-GYN source IDs must be unique non-empty strings")
    for item in sources:
        url = str(item.get("url", ""))
        if not url.startswith("https://"):
            raise ValueError("source %s has a non-HTTPS URL" % item.get("id"))
    return sources


def validate_case_reference(value: str) -> str:
    case_id = (value or "").strip()
    if not re.fullmatch(r"synthetic-obgyn-\d{3,6}", case_id):
        raise ValueError("Use a synthetic case reference only, e.g. synthetic-obgyn-001. Do not enter a patient name or record number.")
    return case_id


def source_matches(
    query: str,
    care_stage: str,
    jurisdiction: str,
    *,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Return relevant source links only; never rank medicines or clinical actions."""
    sources = load_sources(catalog_path)
    jurisdiction = (jurisdiction or "EG").upper()
    if jurisdiction not in ALLOWED_JURISDICTIONS:
        raise ValueError("Choose Egypt, US, UK, or Global reference mode.")
    query_text = " ".join((query or "").casefold().split())
    terms = set(re.findall(r"[a-z0-9]+", query_text))
    stage_terms = STAGE_TERMS.get(care_stage, [])
    for phrase in stage_terms:
        terms.update(re.findall(r"[a-z0-9]+", phrase.casefold()))

    ranked = []
    for source in sources:
        scopes = [str(value).upper() for value in source.get("jurisdiction", [])]
        allowed = jurisdiction in scopes or "GLOBAL" in scopes or "GLOBAL_REFERENCE" in scopes
        if not allowed:
            continue
        topic_text = " ".join([
            str(source.get("title", "")),
            str(source.get("publisher", "")),
            " ".join(str(v) for v in source.get("topics", [])),
            str(source.get("clinical_role", "")),
        ]).casefold()
        source_words = set(re.findall(r"[a-z0-9]+", topic_text))
        hits = sorted(terms.intersection(source_words))
        exact_hits = [topic for topic in source.get("topics", []) if len(topic) > 2 and topic.casefold() in query_text]
        score = len(hits) + 3 * len(exact_hits)
        if care_stage != "general" and any(
            term in topic_text for term in stage_terms
        ):
            score += 2
        result = dict(source)
        result["match_terms_for_display_only"] = exact_hits[:6] if exact_hits else hits[:8]
        result["relevance_score_internal"] = score
        ranked.append(result)

    # A source-link directory is useful even when the words are unfamiliar.
    # For a non-empty query, sort matching sources first; score is never a clinical ranking.
    ranked.sort(key=lambda item: (item["relevance_score_internal"] > 0, item["relevance_score_internal"]), reverse=True)
    selected = ranked[: max(1, min(limit, 15))]
    for item in selected:
        item.pop("relevance_score_internal", None)
    return selected


def urgent_prompts(form: Mapping[str, Any]) -> List[Dict[str, str]]:
    return [
        {"key": key, "label": label, "action": action}
        for key, (label, action) in URGENT_PROMPTS.items()
        if _checked(form, "urgent_" + key)
    ]


def _sources_html(sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "<p>No sources are cataloged for this query and jurisdiction. Do not borrow another jurisdiction's pathway; ask a senior clinician or pharmacist.</p>"
    out = [
        "<p class='muted'>These are reference links, not approved protocols. Relevance is based on matching words/topics, not clinical applicability or source quality.</p>"
    ]
    for source in sources:
        url = str(source.get("url", ""))
        if not url.startswith("https://"):
            continue
        topics = ", ".join(str(v) for v in source.get("topics", [])[:5])
        notes = source.get("notes", [])
        out.append(
            "<article class='source-card'><div class='kicker'>%s · %s</div>"
            "<h3><a href='%s' target='_blank' rel='noopener noreferrer'>%s</a></h3>"
            "<p><strong>Publisher:</strong> %s</p><p><strong>Version / date:</strong> %s</p>"
            "<p><strong>Scope:</strong> %s</p><p><strong>Access:</strong> %s</p>"
            "<p><strong>Rights:</strong> %s</p><p class='muted'>Clinical role: %s</p>"
            % (
                esc(source.get("id", "")),
                esc(", ".join(str(v) for v in source.get("jurisdiction", []))),
                esc(url),
                esc(source.get("title", "Source reference")),
                esc(source.get("publisher", "")),
                esc(source.get("version", source.get("published_on", "version not captured"))),
                esc(topics),
                esc(source.get("access", "")),
                esc(source.get("reuse_rights", "")),
                esc(source.get("clinical_role", "")),
            )
        )
        if notes:
            out.append("<ul>" + "".join("<li>%s</li>" % esc(note) for note in notes[:3]) + "</ul>")
        if source.get("secondary_url", "").startswith("https://"):
            out.append("<p><a href='%s' target='_blank' rel='noopener noreferrer'>Open secondary source center</a></p>" % esc(source["secondary_url"]))
        out.append("</article>")
    return "".join(out)


def render_page(form: Optional[Mapping[str, Any]] = None, review: Optional[Dict[str, Any]] = None, *, catalog_path: str | Path = DEFAULT_CATALOG_PATH) -> str:
    form = form or {}
    jurisdiction = _one(form, "jurisdiction", "EG").upper()
    if jurisdiction not in ALLOWED_JURISDICTIONS:
        jurisdiction = "EG"
    care_stage = _one(form, "care_stage", "general")
    if care_stage not in CARE_STAGES:
        care_stage = "general"
    case_id = _one(form, "case_id", "synthetic-obgyn-001")
    query = _one(form, "clinical_question", "")
    flags = urgent_prompts(form)
    sources: List[Dict[str, Any]] = []
    error = None
    if review is not None:
        sources = review.get("sources", [])
        error = review.get("error")

    stage_options = "".join(
        "<option value='%s'%s>%s</option>" % (esc(key), " selected" if key == care_stage else "", esc(label))
        for key, label in CARE_STAGES.items()
    )
    jurisdiction_options = "".join(
        "<option value='%s'%s>%s</option>" % (esc(code), " selected" if code == jurisdiction else "", esc(label))
        for code, label in [
            ("EG", "Egypt · EG"),
            ("GLOBAL", "Global evidence · WHO / international"),
            ("US", "United States · US"),
            ("UK", "United Kingdom · UK"),
        ]
    )
    urgent_checks = "".join(
        "<label class='urgent-option'><input type='checkbox' name='urgent_%s' value='1'%s> %s</label>"
        % (esc(key), " checked" if _checked(form, "urgent_" + key) else "", esc(label))
        for key, (label, _action) in URGENT_PROMPTS.items()
    )

    if flags:
        flag_html = "<section class='critical'><h2>⚠ Emergency escalation prompts selected</h2><p>These selections are not a diagnosis and do not establish severity. Follow the hospital's local emergency pathway and activate senior/emergency response as appropriate now.</p><ul>"
        flag_html += "".join("<li><strong>%s</strong><br>%s</li>" % (esc(flag["label"]), esc(flag["action"])) for flag in flags)
        flag_html += "</ul></section>"
    else:
        flag_html = "<section class='note'><strong>Urgent review prompts:</strong> If any red flag is present in the actual patient, activate the hospital's local emergency pathway. A blank checklist is not evidence that an emergency is absent.</section>"

    result_html = ""
    if review is not None:
        if error:
            result_html = "<section class='note'><h2>Reference lookup not completed</h2><p>%s</p></section>" % esc(error)
        else:
            result_html = (
                "<section class='results'><div class='kicker'>Source routing only</div><h2>Reference centers for clinician review</h2>"
                "<p>Query: <strong>%s</strong> · Jurisdiction: <strong>%s</strong> · Care stage: <strong>%s</strong></p>%s</section>"
                % (esc(query or "general reference search"), esc(jurisdiction), esc(CARE_STAGES[care_stage]), _sources_html(sources))
            )

    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; form-action 'self'; base-uri 'none'; frame-ancestors 'none'">
<title>Dr. Mia · OB-GYN Clinical Reference Workbench</title>
<style>
:root{--ink:#203238;--muted:#617477;--teal:#0d6972;--line:#d7e3e3;--bg:#edf4f4;--gold:#e5bd65;--red:#9e2b24}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
header{background:#103b43;color:#fff;padding:26px max(20px,calc((100vw - 1120px)/2)) 22px}
.kicker{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#67868a;font-weight:800;overflow-wrap:anywhere}
header .kicker{color:#b7dedf}h1{font-size:clamp(26px,4vw,40px);line-height:1.1;margin:7px 0}header p{max-width:780px;color:#e4f0ef;margin:10px 0 0}
main{max-width:1120px;margin:22px auto 50px;padding:0 18px}.banner{padding:13px 15px;background:#fff3cf;border:1px solid #e8d291;border-radius:12px;font-weight:750;margin-bottom:16px}
.layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.72fr);gap:18px}.panel,.results{background:#fff;border:1px solid var(--line);border-radius:16px;padding:19px;box-shadow:0 5px 18px #163d4410}
h2{margin:4px 0 10px;font-size:21px}h3{margin:8px 0;font-size:17px}p{margin:7px 0 11px}.muted{font-size:12px;color:var(--muted)}label{display:block;font-weight:700;font-size:13px;margin:12px 0 5px}
input[type=text],input[type=number],textarea,select{width:100%%;border:1px solid #b9cdcf;border-radius:9px;background:#fff;padding:10px 11px;font:inherit;color:var(--ink)}
textarea{min-height:112px;resize:vertical}button{background:var(--teal);color:#fff;border:0;border-radius:10px;padding:12px 16px;font:inherit;font-weight:800;cursor:pointer;margin-top:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}.checks{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;margin-top:9px}.checks label,.urgent-option{display:flex;gap:8px;align-items:flex-start;font-weight:550;margin:4px 0;font-size:13px}.checks input,.urgent-option input{margin-top:4px;flex-shrink:0}
.critical{border:2px solid #d66a61;background:#fff0ef;border-radius:12px;padding:14px;margin-bottom:15px}.critical h2{color:#8c211c}.critical li{margin:7px 0}.note{border:1px solid #d5c58f;background:#fff8df;border-radius:11px;padding:12px;margin:0 0 15px}
.source-card{border-top:1px solid var(--line);padding:13px 0}.source-card a{color:#086773;text-decoration-thickness:1.5px;overflow-wrap:anywhere}.source-card li{margin:4px 0;font-size:12px}
.results{margin-top:18px}.disclaimer{margin-top:17px;font-size:12px;color:#536a6d}.small{font-size:12px;color:var(--muted)}
@media(max-width:800px){.layout{grid-template-columns:1fr}.grid2,.checks{grid-template-columns:1fr}}
</style></head>
<body>
<header><div class="kicker">Hospital clinician reference · Prototype</div><h1>Dr. Mia · OB-GYN</h1>
<p>Clinical information routing for obstetrics and gynaecology. Search WHO, specialist guidance, medication-in-pregnancy/lactation resources, product labels, and Egypt-specific regulatory references.</p>
%s</header>
<main>
<div class="banner">SYNTHETIC CASES ONLY · NO PATIENT IDENTIFIERS · SOURCE LINKS, NOT TREATMENT ORDERS</div>
""" + flag_html + """
<div class="layout">
<section class="panel"><div class="kicker">Clinical review workspace</div><h2>Find the right reference center</h2>
<p class="muted">Enter a synthetic scenario or clinical question. Mia routes to information centers by topic and jurisdiction. It does not diagnose or choose a medicine.</p>
<form method="post" action="/">
<div class="grid2"><div><label for="case_id">Synthetic case reference</label><input id="case_id" name="case_id" type="text" value="%s" required></div>
<div><label for="jurisdiction">Clinical jurisdiction</label><select id="jurisdiction" name="jurisdiction">%s</select></div></div>
<div class="grid2"><div><label for="care_stage">Care stage / service</label><select id="care_stage" name="care_stage">%s</select></div>
<div><label for="gestational_week">Gestational week (if relevant)</label><input id="gestational_week" name="gestational_week" type="number" min="0" max="45" value="%s"></div></div>
<div class="grid2"><div><label for="postpartum_day">Postpartum day (if relevant)</label><input id="postpartum_day" name="postpartum_day" type="number" min="0" max="365" value="%s"></div>
<div><label for="medication_context">Medicine/topic name (optional, no patient details)</label><input id="medication_context" name="medication_context" type="text" maxlength="120" value="%s" placeholder="e.g. lactation medicine review"></div></div>
<label for="clinical_question">Clinical question or clinician-entered assessment</label>
<textarea id="clinical_question" name="clinical_question" maxlength="1600" required placeholder="Synthetic example: postpartum haemorrhage guideline version; medication reference during breastfeeding">%s</textarea>
<label>Potential urgent escalation prompts</label><div class="checks">%s</div>
<p class="muted">Select only if the scenario contains the listed trigger. This checklist is not validated triage, does not replace observations or hospital policy, and cannot rule out an emergency.</p>
<button type="submit">Find source references</button></form>
</section>
<aside class="panel"><div class="kicker">Safety & governance</div><h2>What Mia will and won't do</h2>
<ul>
<li>Show authoritative sources and their stated version/rights status.</li>
<li>Keep Egypt, US, UK and global reference scope visible.</li>
<li>Display locally approved emergency escalation prompts when selected.</li>
<li>Never infer a dose, regimen, diagnosis, delivery decision or medication choice from a keyword match.</li>
<li>Use local protocol, senior obstetric/gynaecology review, pharmacy review and current product labeling where needed.</li>
<li>Do not enter patient-identifying information. Submitted fields are not saved and no external APIs are called.</li>
</ul>
<div class="note"><strong>Urgent care first.</strong> If an actual patient may be deteriorating, follow the hospital's emergency response now. Do not wait for this prototype to search or interpret references.</div>
<p class="small">This workbench is an unauthenticated local prototype. Bind only to loopback; do not expose it to the internet or use it in live patient care.</p></aside>
</div>
%s
<p class="disclaimer">Source matching is based on text/topic overlap, not evidence grading. Many specialist guidelines are copyrighted and/or access-restricted. Public access is not permission to copy. Every derived protocol would require local jurisdiction review, source-version checks, rights review and approval by an appropriately qualified clinical governance group.</p>
</main></body></html>""" % (
        esc(case_id), jurisdiction_options, stage_options,
        esc(_one(form, "gestational_week", "")), esc(_one(form, "postpartum_day", "")),
        esc(_one(form, "medication_context", "")), esc(query), urgent_checks, result_html,
        render_avatar_customizer("Personalize your OB-GYN Mia")
    )


class ObgynWorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "DrMiaOBGYN/0.1"

    def _send(self, code: int, payload: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        asset_name = self.path.rsplit("/", 1)[-1]
        if self.path.startswith("/assets/") and asset_name in AVATAR_ASSETS:
            content_type, filename = AVATAR_ASSETS[asset_name]
            try:
                payload = (BASE / "static" / filename).read_bytes()
            except OSError:
                self._send(404, b"Avatar asset not found", "text/plain; charset=utf-8")
                return
            self._send(200, payload, content_type)
            return
        if self.path not in {"/", "/health"}:
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        if self.path == "/health":
            body = json.dumps({"status": "local-prototype", "patient_data_persisted": False}).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        try:
            page = render_page()
        except (OSError, ValueError, json.JSONDecodeError):
            page = "<!doctype html><title>Dr. Mia OB-GYN</title><h1>Reference catalog unavailable</h1><p>No clinical interpretation is available.</p>"
            self._send(503, page.encode("utf-8"))
            return
        self._send(200, page.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        length_header = self.headers.get("Content-Length", "")
        if not length_header.isdigit():
            self._send(400, b"Invalid Content-Length", "text/plain; charset=utf-8")
            return
        length = int(length_header)
        if length > MAX_BODY:
            self._send(413, b"Request too large", "text/plain; charset=utf-8")
            return
        content_type = self.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            self._send(415, b"Unsupported Content-Type", "text/plain; charset=utf-8")
            return
        raw = self.rfile.read(length)
        try:
            parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True, max_num_fields=80)
        except (UnicodeDecodeError, ValueError):
            self._send(400, b"Invalid form", "text/plain; charset=utf-8")
            return
        form: Dict[str, Any] = {key: values[0] if values else "" for key, values in parsed.items()}
        try:
            form["case_id"] = validate_case_reference(_one(form, "case_id"))
            if _one(form, "jurisdiction", "EG").upper() not in ALLOWED_JURISDICTIONS:
                raise ValueError("Choose Egypt, US, UK, or Global reference mode.")
            stage = _one(form, "care_stage", "general")
            if stage not in CARE_STAGES:
                raise ValueError("Choose a listed OB-GYN care stage.")
            week = _one(form, "gestational_week")
            if week and not 0 <= int(week) <= 45:
                raise ValueError("Gestational week must be between 0 and 45.")
            postpartum_day = _one(form, "postpartum_day")
            if postpartum_day and not 0 <= int(postpartum_day) <= 365:
                raise ValueError("Postpartum day must be between 0 and 365.")
            query = _one(form, "clinical_question")[:1600]
            medication_context = _one(form, "medication_context")[:120]
            combined = " ".join([query, medication_context]).strip()
            sources = source_matches(combined, stage, _one(form, "jurisdiction", "EG").upper())
            review = {"sources": sources, "error": None}
            page = render_page(form, review)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            page = render_page(form, {"sources": [], "error": str(exc)})
            self._send(400, page.encode("utf-8"))
            return
        self._send(200, page.encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        # Do not log submitted form fields or clinical query values.
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Dr. Mia OB-GYN reference workbench")
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    server = HTTPServer(("127.0.0.1", args.port), ObgynWorkbenchHandler)
    print("Dr. Mia OB-GYN reference workbench running on http://127.0.0.1:%d" % args.port)
    print("Synthetic cases only. Do not expose this local prototype publicly.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
