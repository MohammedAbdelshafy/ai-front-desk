"""Local demo server for the Mia Clinical intake platform.

stdlib only. Serves:
- GET /                      landing + demo clinic picker
- GET /intake?clinic=ID      mobile-friendly patient intake form
- POST /api/intake            submit answers (JSON)
- GET /dashboard?clinic=ID   dentist dashboard (submission list)
- GET /record?clinic=ID&sub=SID  single-record brief
- POST /api/review            record dentist review
- POST /api/correct           record a correction
- GET /api/audit?clinic=ID&target=SID  audit trail

SYNTHETIC DATA ONLY. No real patient information. The demo uses a
query-string clinic selector; production MUST use authenticated routing
(see docs/adr/001-clinical-data-store.md). DRY_RUN-style: no external
sends, bookings, or messages are ever triggered from this server.
"""
from __future__ import annotations

import html
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .intake import process_intake, to_fhir_questionnaire_response
from .dashboard import generate_brief
from .mia_shell import DENTAL_MIA, TaskStage
from .question_bank import load_bank, bank_snapshot
from .store import ClinicalStore, TenantMismatchError
from .medication_support import load_medication_catalog, review_medication_options

BASE = Path(__file__).resolve().parent
BANK = load_bank(BASE / "dental_intake_v1.json")
DB_PATH = Path(os.environ.get("CLINICAL_DB", str(Path.home() / ".mia-clinical-demo" / "clinical-demo.sqlite3")))
MAX_REQUEST_BODY = 64 * 1024
DEMO_PATIENT_LABEL_RE = re.compile(r"(?:Demo|Test|Sample) [A-Za-z0-9][A-Za-z0-9 _-]{0,44}\Z", re.IGNORECASE)
SUBMISSION_ID_RE = re.compile(r"sub_[a-f0-9]{12}\Z")

DEMO_CLINICS = [
    ("demo-smile-arts", "Smile Arts Dental (demo)"),
    ("demo-lakeside", "Lakeside Family Dental (demo)"),
]

DEMO_CLINIC_IDS = {clinic_id for clinic_id, _name in DEMO_CLINICS}

BANNER = (
    "<div style='background:#fff3cd;color:#664d03;padding:10px 14px;"
    "font:14px system-ui'>DEMO — synthetic data only. Not HIPAA-compliant. "
    "Not for real patient use.</div>"
)

STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font:16px/1.5 system-ui,-apple-system,sans-serif;margin:0;color:#1a1a1a}
.wrap{max-width:720px;margin:0 auto;padding:16px}
.mia-stage{display:flex;align-items:flex-start;gap:14px;margin:14px 0 20px;padding:14px;background:linear-gradient(135deg,#eef2ff,#f8f9ff);border:1px solid #dce4ff;border-radius:16px;box-shadow:0 4px 18px rgba(49,76,160,.07)}
.mia-avatar{width:64px;height:64px;flex:0 0 64px;object-fit:cover;object-position:top center;border-radius:15px;background:#e3eaff;border:1px solid #d4defd}
.mia-stage-content{min-width:0;flex:1}.mia-stage-head{display:flex;align-items:center;justify-content:space-between;gap:9px;flex-wrap:wrap}
.mia-stage-head strong{font-size:15px;letter-spacing:-.2px;color:#26365a}.mia-stage>div p{font-size:13px;color:#586784;line-height:1.55;margin:7px 0 0}
.mia-stage .stage{font-size:10px;text-transform:uppercase;letter-spacing:.08em;font-weight:800;padding:4px 8px;color:#3554bf;background:#e1e9ff;border:1px solid #cedaff;border-radius:20px}
.mia-help{margin-top:9px;font-size:12px;color:#596985}.mia-help summary{cursor:pointer;font-weight:700;color:#4560c6}
.mia-model-note{font-size:11px!important;color:#8994a8!important;margin-top:8px!important}
.mia-chat-log{display:flex;flex-direction:column;gap:7px;max-height:220px;overflow:auto;margin:10px 0}
.mia-chat-line{max-width:95%;border-radius:10px;padding:9px 10px;margin:0;font-size:12px;line-height:1.5}
.mia-chat-assistant{align-self:flex-start;background:#fff;border:1px solid #e3e8f7;color:#4b5b78}
.mia-chat-user{align-self:flex-end;background:#3c5ed1;color:#fff}
.mia-chat-form label{display:block;font-size:11px;font-weight:700;color:#5b6780;margin-bottom:5px}
.mia-chat-entry{display:flex;gap:7px;align-items:stretch}
.mia-chat-entry input{flex:1;min-width:0;border:1px solid #d2dbef;border-radius:8px;padding:9px 10px;font-size:12px}
.mia-chat-entry button{padding:9px 13px;font-size:12px;white-space:nowrap}
h1{font-size:22px} h2{font-size:18px;margin-top:28px}
.q{border:1px solid #ddd;border-radius:10px;padding:12px;margin:10px 0}
.q>label{font-weight:600;display:block;margin-bottom:6px}
.multi-option{font-weight:400!important;display:block;margin:6px 0}
.multi-option input{margin-right:6px}
input[type=text],input[type=date],input[type=number],textarea,select{width:100%;padding:10px;font-size:16px;border:1px solid #bbb;border-radius:8px;box-sizing:border-box}
textarea{min-height:70px}
button{background:#0b5fff;color:#fff;border:0;border-radius:10px;padding:12px 20px;font-size:16px;cursor:pointer}
button:disabled{background:#999}
.flag{border-left:4px solid #c00;background:#fdeeee;padding:8px 12px;margin:8px 0;border-radius:4px}
.flag.med{border-color:#e6a700;background:#fff8e1}
.src{font-size:12px;color:#666;text-transform:uppercase;letter-spacing:.04em}
table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:8px;text-align:left;font-size:14px}
 Mia-stage{margin:12px 0}
.stage{display:inline-block;background:#eef4ff;border:1px solid #bcd;padding:6px 12px;border-radius:20px;font-size:14px}
.escape{font-size:13px;color:#555}
</style>
"""


def esc(s):
    return html.escape(str(s), quote=True)


def mia_stage_html(manifest_name="Dental Mia", stage="listening", reason=""):
    default_message = (
        "I'm your intake guide. I can explain this workflow, but I don't diagnose "
        "conditions or recommend medicines."
    )
    message = reason or default_message
    return (
        "<section class='mia-stage' aria-label='Dental Mia assistant'>"
        "<img class='mia-avatar' src='/assets/mia-stand-hi.webp' "
        "alt='Mia, your AI intake guide' width='64' height='64'>"
        "<div class='mia-stage-content'>"
        "<div class='mia-stage-head'>"
        f"<strong>{esc(manifest_name)}</strong>"
        f"<span class='stage'>{esc(stage)}</span>"
        "</div>"
        f"<p>{esc(message)}</p>"
        "<details class='mia-help'><summary>Talk with Mia (local demo guide)</summary>"
        "<p class='mia-model-note'>This prototype uses fixed, local workflow answers. "
        "It is not connected to a live AI model and does not send your question anywhere.</p>"
        "<div class='mia-chat-log' role='log' aria-live='polite'>"
        "<p class='mia-chat-line mia-chat-assistant'>Hi, I'm Mia. Ask me how to complete this form or what information to include.</p>"
        "</div>"
        "<form class='mia-chat-form'>"
        "<label for='mia-question'>Your question</label>"
        "<div class='mia-chat-entry'><input id='mia-question' name='question' type='text' maxlength='280' "
        "autocomplete='off' required placeholder='Ask about the intake process…'>"
        "<button type='submit'>Ask Mia</button></div>"
        "</form>"
        "</details></div></section>"
        + MIA_CHAT_SCRIPT
    )


MIA_CHAT_SCRIPT = r"""<script>
(function () {
  if (window.__miaClinicalGuideBound) return;
  window.__miaClinicalGuideBound = true;
  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!form || !form.classList || !form.classList.contains("mia-chat-form")) return;
    event.preventDefault();
    const input = form.querySelector("input[name='question']");
    const log = form.parentElement.querySelector(".mia-chat-log");
    const question = (input && input.value || "").trim();
    if (!question || !log) return;
    const q = question.toLowerCase();
    let answer = "I can explain the form and the intake workflow. I can't interpret symptoms or make medical decisions. For personal clinical questions, contact your dentist or another qualified clinician.";
    if (/(which medicine|what medicine should|what drug should|should i take|which antibiotic|dose should i|prescribe|diagnos|what disease|treat my|is this serious)/.test(q)) {
      answer = "I can't diagnose a condition or recommend a medicine or dose. Please ask the dentist or another qualified clinician, who can consider your history and examination.";
    } else if (/(don't know|do not know|not sure|unsure|unknown|leave blank|skip this)/.test(q)) {
      answer = "Choose “I don't know”, “Not applicable”, or “Prefer not to answer” where those options are available. If the answer is important and you are unsure, the clinic can clarify it with you.";
    } else if (/(antibiotic|medication|medicine|supplement|vitamin|drug list)/.test(q)) {
      answer = "List the medicines you currently take and any recent changes. Where known, include the name, strength, dose, how often you take it, and why. Include current or recent antibiotics, over-the-counter medicines, vitamins, and supplements. Do not start, stop, or change a medicine because of this form.";
    } else if (/(allerg|reaction|penicillin|latex)/.test(q)) {
      answer = "Report the substance and what happened during the reaction, if you know. The form records your answer for the dentist to review; it does not assess the allergy or decide treatment.";
    } else if (/(staff|human|person|contact|message|call the clinic|talk to someone)/.test(q)) {
      answer = "This local demo cannot send messages to clinic staff. Please call the clinic directly for help or urgent clinical concerns.";
    } else if (/(privacy|data|real patient|actual patient|safe to enter)/.test(q)) {
      answer = "This is a local synthetic-data demonstration. Do not enter real names, dates of birth, phone numbers, or real health information.";
    } else if (/(complete|fill|questionnaire|form|history|what is this)/.test(q)) {
      answer = "This form collects the history you report so the dentist can review it before your visit. Answer what you know, be as accurate as you can, and use an available “Not sure” option instead of guessing.";
    }
    const userLine = document.createElement("p");
    userLine.className = "mia-chat-line mia-chat-user";
    userLine.textContent = question;
    const assistantLine = document.createElement("p");
    assistantLine.className = "mia-chat-line mia-chat-assistant";
    assistantLine.textContent = answer;
    log.appendChild(userLine);
    log.appendChild(assistantLine);
    input.value = "";
    log.scrollTop = log.scrollHeight;
  });
})();
</script>"""


def render_landing():
    links = "".join(
        f"<li><b>{esc(name)}</b> — "
        f"<a href='/intake?clinic={cid}'>patient intake</a> · "
        f"<a href='/dashboard?clinic={cid}'>dentist dashboard</a> · "
        f"<a href='/medication-review?clinic={cid}'>medication review</a></li>"
        for cid, name in DEMO_CLINICS
    )
    return f"""<html><head><title>Mia Clinical — demo</title>{STYLE}</head><body>
{BANNER}<div class="wrap">
{mia_stage_html(stage="idle", reason="choose a demo clinic")}
<h1>Mia Clinical Platform — local demo</h1>
<p>Dental pre-visit intake + dentist history brief. Synthetic data only.</p>
<ul>{links}</ul>
<p class="src">Question bank: {esc(BANK.bank_id)} v{esc(BANK.version)} ·
review status: {esc(BANK.review_status)} (dentist review pending)</p>
</div></body></html>"""


def render_medication_review(clinic_id, clinic_name):
    """Clinician-facing synthetic demo; never persists or transmits this request."""
    catalog = load_medication_catalog()
    page = (
        "<html><head><title>Mia Medication Review</title>" + STYLE + "</head><body>"
        + BANNER + "<div class='wrap'>"
        + mia_stage_html(
            manifest_name="Mia Medication Review",
            stage="review",
            reason="I can compare a clinician-entered diagnosis with reviewed reference entries. I do not diagnose or prescribe.",
        )
        + """
<h1>Medication teaching and safety review</h1>
<p><strong>Clinic:</strong> __CLINIC_NAME__</p>
<p>This clinician-only prototype accepts fictional cases. Enter the diagnosis already made by the clinician and review the patient factors. It does not create or transmit prescriptions.</p>
<div class="q">
  <p><b>Catalogue state:</b> __CATALOG_STATUS__</p>
  <p>The initial medication catalogue is intentionally empty until a dentist/gynecologist and a medication-safety reviewer approve sourced entries.</p>
</div>
<form id="medication-review" data-clinic-id="__CLINIC_ID__">
  <div class="q"><label for="demo-label">Fictional case label</label><input id="demo-label" type="text" value="Demo Patient 01" maxlength="55" required pattern="(Demo|Test|Sample) [A-Za-z0-9][A-Za-z0-9 _-]{0,44}"><small>Use only labels beginning with Demo, Test, or Sample. Never enter real patient data.</small></div>
  <div class="q"><label for="specialty">Specialty</label><select id="specialty" required><option value="">Choose specialty</option><option value="dentistry">Dentistry</option><option value="gynecology">Gynecology</option></select></div>
  <div class="q"><label for="diagnosis">Clinician-entered diagnosis code</label><input id="diagnosis" type="text" maxlength="80" required placeholder="Exact code used by your approved pathway"><small>The engine uses exact codes only. It will not infer a diagnosis from symptoms or free text.</small></div>
  <div class="q"><label for="age">Age in years</label><input id="age" type="number" min="0" max="130" step="1" required></div>
  <div class="q"><label for="allergies-reviewed">Allergies reviewed by clinician</label><select id="allergies-reviewed" required><option value="">Choose</option><option value="yes">Reviewed and confirmed</option><option value="no">Not reviewed / uncertain</option></select></div>
  <div class="q"><label for="allergies">Known allergies or reactions (comma-separated; leave empty only if none reported)</label><textarea id="allergies" rows="2" placeholder="Synthetic allergy examples only"></textarea></div>
  <div class="q"><label for="meds-reviewed">Current medication list reviewed by clinician</label><select id="meds-reviewed" required><option value="">Choose</option><option value="yes">Reviewed and confirmed</option><option value="no">Not reviewed / uncertain</option></select></div>
  <div class="q"><label for="meds">Current medicines (comma-separated; include known OTC medicines)</label><textarea id="meds" rows="2" placeholder="Synthetic medicine names only"></textarea></div>
  <div class="q"><label for="pregnancy">Pregnancy status</label><select id="pregnancy" required><option value="">Choose</option><option value="yes">Yes</option><option value="no">No</option><option value="not_applicable">Clinician confirmed not applicable</option><option value="unknown">Unknown</option></select></div>
  <div class="q"><label for="lactation">Lactation status</label><select id="lactation" required><option value="">Choose</option><option value="yes">Yes</option><option value="no">No</option><option value="not_applicable">Clinician confirmed not applicable</option><option value="unknown">Unknown</option></select></div>
  <div class="q"><label for="severe-allergy">Relevant severe allergy flag</label><select id="severe-allergy" required><option value="unknown">Unknown / not assessed</option><option value="yes">Present</option><option value="no">Absent after review</option></select></div>
  <div class="q"><label for="renal">Renal function context</label><select id="renal" required><option value="unknown">Unknown / not assessed</option><option value="normal">Known normal</option><option value="abnormal">Known abnormal</option><option value="not_applicable">Clinician confirmed not applicable</option></select></div>
  <div class="q"><label for="hepatic">Hepatic function context</label><select id="hepatic" required><option value="unknown">Unknown / not assessed</option><option value="normal">Known normal</option><option value="abnormal">Known abnormal</option><option value="not_applicable">Clinician confirmed not applicable</option></select></div>
  <div class="q"><label for="extra-facts">Other structured safety facts (JSON object, optional)</label><textarea id="extra-facts" rows="3">{}</textarea><small>Use only synthetic, clinician-confirmed key/value facts requested by a reviewed rule. Core fields above cannot be overwritten here.</small></div>
  <button type="submit" id="review-button">Evaluate reviewed entries</button>
</form>
<section id="review-result" aria-live="polite"></section>
<script>
(function () {
  const form = document.getElementById('medication-review');
  const output = document.getElementById('review-result');
  const button = document.getElementById('review-button');
  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (char) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[char];
    });
  }
  function csvValues(value) {
    return String(value || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
  }
  function render(data) {
    if (!data || !data.review) {
      output.innerHTML = '<div class="flag">The review response was not in the expected format. No medication decision was made.</div>';
      return;
    }
    const result = data.review;
    let html = '<h2>Review result</h2><p><b>Status:</b> ' + escapeHtml(result.status) + '</p>';
    html += '<p><b>Catalogue:</b> ' + escapeHtml(data.catalog.status) + ' · version ' + escapeHtml(data.catalog.version) + '</p>';
    html += '<p>' + escapeHtml(result.notice) + '</p>';
    html += '<p class="escape">' + escapeHtml(result.interaction_coverage_warning || '') + '</p>';
    if (result.missing_context && result.missing_context.length) {
      html += '<div class="flag">Review blocked. Missing or unresolved: ' + result.missing_context.map(escapeHtml).join(', ') + '</div>';
    }
    const options = result.candidate_options || [];
    if (!options.length) {
      if (data.catalog.status !== 'approved') {
        html += '<div class="q"><b>No medication entries are enabled.</b><p>This is intentional while the catalogue is awaiting qualified review. It is not a conclusion that a medicine is or is not indicated.</p></div>';
      } else {
        html += '<div class="q"><b>No eligible candidate was returned from this catalogue.</b><p>This does not establish that medication is unnecessary. Follow the clinician-approved guideline and local workflow.</p></div>';
      }
    }
    options.forEach(function (item) {
      html += '<article class="q"><h3>' + escapeHtml(item.display_name) + '</h3>';
      html += '<p><b>State:</b> source-backed option for independent clinician review, not a final decision.</p>';
      const sections = [
        ['why_consider','Why this may be considered'],['mechanism','Mechanism'],
        ['evidence_summary','Evidence summary'],['alternatives','Alternatives'],
        ['common_adverse_effects','Common adverse effects'],['serious_warnings','Serious warnings'],
        ['pregnancy_lactation','Pregnancy and lactation'],['monitoring','Monitoring'],
        ['counseling','Patient counseling'],['dose_summary','Official-label dose context']
      ];
      sections.forEach(function (section) {
        html += '<p><b>' + escapeHtml(section[1]) + ':</b> ' + escapeHtml(item.teaching[section[0]]) + '</p>';
      });
      html += '<p><b>Source:</b> <a target="_blank" rel="noopener noreferrer" href="' + escapeHtml(item.source.url) + '">' + escapeHtml(item.source.title) + '</a></p>';
      html += '<p class="src">Jurisdiction ' + escapeHtml(item.source.jurisdiction) + ' · ' + escapeHtml(item.source.source_type) + ' · version ' + escapeHtml(item.source.version) + ' · effective ' + escapeHtml(item.source.effective_date) + ' · review due ' + escapeHtml(item.source.review_due) + '</p>';
      html += '</article>';
    });
    (result.withheld_options || []).forEach(function (item) {
      html += '<div class="flag"><b>Withheld for safety review:</b> ' + escapeHtml(item.display_name) + ' · ' + escapeHtml(item.reason_code) + '<p>' + escapeHtml(item.message) + '</p></div>';
    });
    output.innerHTML = html;
  }
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;
    let extraFacts;
    try {
      extraFacts = JSON.parse(document.getElementById('extra-facts').value || '{}');
    } catch (_error) {
      output.innerHTML = '<div class="flag">Additional facts must be valid JSON.</div>';
      return;
    }
    if (!extraFacts || Array.isArray(extraFacts) || typeof extraFacts !== 'object' ||
        Object.values(extraFacts).some(function (v) { return v !== null && !['string','number','boolean'].includes(typeof v); })) {
      output.innerHTML = '<div class="flag">Additional facts must be a JSON object with scalar values.</div>';
      return;
    }
    const payload = {
      clinic_id: form.dataset.clinicId,
      demo_patient_label: document.getElementById('demo-label').value.trim(),
      specialty: document.getElementById('specialty').value,
      diagnosis_code: document.getElementById('diagnosis').value.trim(),
      age_years: Number(document.getElementById('age').value),
      allergies_reviewed: document.getElementById('allergies-reviewed').value === 'yes',
      allergies: csvValues(document.getElementById('allergies').value),
      current_medications_reviewed: document.getElementById('meds-reviewed').value === 'yes',
      current_medications: csvValues(document.getElementById('meds').value),
      pregnancy_status: document.getElementById('pregnancy').value || 'unknown',
      lactation_status: document.getElementById('lactation').value || 'unknown',
      severe_allergy: document.getElementById('severe-allergy').value === 'yes' ? true :
        (document.getElementById('severe-allergy').value === 'no' ? false : 'unknown'),
      renal_function: document.getElementById('renal').value || 'unknown',
      hepatic_function: document.getElementById('hepatic').value || 'unknown',
      additional_facts: extraFacts
    };
    button.disabled = true;
    button.textContent = 'Checking reviewed entries…';
    output.innerHTML = '<p>Checking exact diagnosis, source status and the supplied synthetic safety context…</p>';
    try {
      const response = await fetch('/api/medication-review', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        output.innerHTML = '<div class="flag">' + escapeHtml(data.error || 'The review request could not be processed.') + '</div>';
      } else {
        render(data);
      }
    } catch (_error) {
      output.innerHTML = '<div class="flag">The local review endpoint could not be reached. No medication decision was made.</div>';
    } finally {
      button.disabled = false;
      button.textContent = 'Evaluate reviewed entries';
    }
  });
})();
</script>
</div></body></html>
"""
    )
    return (
        page.replace("__CLINIC_NAME__", esc(clinic_name))
        .replace("__CLINIC_ID__", esc(clinic_id))
        .replace("__CATALOG_STATUS__", esc(catalog.get("status", "unavailable")))
    )


def render_intake(clinic_id, clinic_name):
    qs_html = []
    for q in BANK.questions:
        cond = ""
        if q.show_if:
            cond = (f" data-show-if-qid='{esc(q.show_if['qid'])}'"
                    f" data-show-if-equals='{esc(q.show_if.get('equals', ''))}'"
                    f" data-show-if-in='{esc(','.join(q.show_if.get('in', [])))}'")
        field = ""
        if q.qtype in ("choice", "yes_no"):
            opts = "".join(f"<option value='{esc(o)}'>{esc(o)}</option>" for o in q.options)
            esc_opts = "".join(f"<option value='{esc(e)}'>{esc(e)}</option>" for e in ("I don't know", "Not applicable", "Prefer not to answer")) if q.allow_escape else ""
            req_attr = " required" if q.required else ""
            field = f"<select id='{esc(q.qid)}' name='{esc(q.qid)}' data-qtype='{esc(q.qtype)}'{req_attr}><option value=''>— choose —</option>{opts}{esc_opts}</select>"
        elif q.qtype == "multi_choice":
            boxes = "".join(
                f"<label class='multi-option'>"
                f"<input type='checkbox' id='{esc(q.qid)}-{i}' name='{esc(q.qid)}' value='{esc(o)}'> {esc(o)}</label>"
                for i, o in enumerate(q.options)
            )
            field = f"<div role='group' aria-labelledby='label-{esc(q.qid)}' data-qtype='multi_choice' data-qid='{esc(q.qid)}'>{boxes}</div>"
        elif q.qtype == "date":
            req_attr = " required" if q.required else ""
            field = f"<input type='date' id='{esc(q.qid)}' name='{esc(q.qid)}'{req_attr}>"
        elif q.qtype == "number":
            req_attr = " required" if q.required else ""
            field = f"<input type='number' id='{esc(q.qid)}' name='{esc(q.qid)}'{req_attr}>"
        else:
            req_attr = " required" if q.required else ""
            field = f"<textarea id='{esc(q.qid)}' name='{esc(q.qid)}' rows='2'{req_attr}></textarea>"
        req = " <span style='color:#c00' aria-hidden='true'>*</span>" if q.required else ""
        label_for = "" if q.qtype == "multi_choice" else f" for='{esc(q.qid)}'"
        qs_html.append(
            f"<div class='q' data-qid='{esc(q.qid)}'{cond}>"
            f"<label id='label-{esc(q.qid)}'{label_for}>{esc(q.text)}{req}</label>{field}</div>"
        )
    return f"""<html><head><title>Pre-visit intake — {esc(clinic_name)}</title>{STYLE}</head><body>
{BANNER}<div class="wrap">
{mia_stage_html(stage="listening", reason="guiding your pre-visit history")}
<h1>Pre-visit health history</h1>
<p><b>{esc(clinic_name)}</b> · takes about 5 minutes. You can skip anything
you're unsure about. <span class="escape">Your answers are recorded exactly as
you give them.</span></p>
<form id="intake">
{''.join(qs_html)}
<button type="submit" id="submitBtn">Submit my history</button>
</form><div id="done" style="display:none"></div>
<script>
const form = document.getElementById('intake');
function currentAnswers(){{
  const a={{}};
  form.querySelectorAll('[name]').forEach(el=>{{
    if(el.type==='checkbox'){{ (a[el.name]=a[el.name]||[]).push(el.value); if(el.checked){{}} else {{a[el.name]=a[el.name].filter(v=>v!==el.value);}} }}
    else a[el.name]=el.value;
  }});
  return a;
}}
function applyConditions(){{
  const a=currentAnswers();
  document.querySelectorAll('.q[data-show-if-qid]').forEach(div=>{{
    const qid=div.dataset.showIfQid, eq=div.dataset.showIfEquals, inn=div.dataset.showIfIn;
    let show=false; const v=a[qid];
    if(eq) show=(v===eq); else if(inn) show=inn.split(',').includes(v);
    div.style.display=show?'':'none';
  }});
}}
form.addEventListener('change',applyConditions); applyConditions();
form.addEventListener('submit', async e=>{{
  e.preventDefault();
  const answers=currentAnswers();
  // drop hidden conditional answers
  document.querySelectorAll('.q[data-show-if-qid]').forEach(div=>{{
    if(div.style.display==='none') delete answers[div.dataset.qid];
  }});
  const btn=document.getElementById('submitBtn'); btn.disabled=true; btn.textContent='Submitting…';
  const r=await fetch('/api/intake',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{clinic_id:'{clinic_id}',patient_ref:answers['id.full_name']||'anonymous',answers}})}});
  const j=await r.json();
  if(j.ok){{ document.getElementById('done').style.display=''; 
    document.getElementById('done').innerHTML='<h2>Thank you — received.</h2><p>Your history was recorded. The dental team will review it before your visit.</p>';
    form.style.display='none';
  }} else {{
    btn.disabled=false; btn.textContent='Submit my history';
    alert('Please fix the highlighted issues:\\n'+(j.errors||[]).join('\\n')+(j.missing||[]).map(m=>'missing: '+m).join('\\n'));
  }}
}});
</script></div></body></html>"""


def render_dashboard(clinic_id, clinic_name, store):
    subs = store.list_submissions(clinic_id)
    rows = "".join(
        f"<tr><td>{esc(s['patient_ref'])}</td><td>{esc(s['status'])}</td>"
        f"<td>{time.strftime('%Y-%m-%d %H:%M', time.localtime(s['created_at']))}</td>"
        f"<td><a href='/record?clinic={clinic_id}&sub={s['submission_id']}'>open brief</a></td></tr>"
        for s in subs
    ) or "<tr><td colspan=4>No submissions yet.</td></tr>"
    return f"""<html><head><title>Dentist dashboard — {esc(clinic_name)}</title>{STYLE}</head><body>
{BANNER}<div class="wrap">
{mia_stage_html(stage="working", reason="listing intake submissions")}
<h1>Dentist dashboard</h1><p><b>{esc(clinic_name)}</b></p>
<table><tr><th>Patient</th><th>Status</th><th>Submitted</th><th></th></tr>{rows}</table>
<p><a href="/">← demo home</a></p></div></body></html>"""


def render_record(clinic_id, sub_id, store):
    try:
        sub = store.get_submission(clinic_id, sub_id)
    except TenantMismatchError:
        return 403, "Cross-clinic access denied."
    except KeyError:
        return 404, "Submission not found."
    corrections = store.list_corrections(clinic_id, sub_id)
    brief = generate_brief(BANK, sub, corrections)
    audit = store.audit_trail(clinic_id, sub_id)

    flags_html = "".join(
        f"<div class='flag{' med' if f['severity']=='medium' else ''}'>"
        f"<b>{esc(f['type'])}</b> · {esc(f['message'])} "
        f"<span class='src'>source: {esc(f['source'])}</span></div>"
        for f in brief["flags"]
    ) or "<p>No flags — no omissions or contradictions detected.</p>"

    sections_html = ""
    for sec in brief["section_order"]:
        items = "".join(
            f"<tr><td>{esc(e['question'])}</td><td>{esc(e.get('corrected_answer', e['answer']))}"
            f"{('<br><span class=src>corrected from: '+esc(e['answer'])+' ('+esc(e.get('correction_source',''))+')</span>') if 'corrected_answer' in e else ''}"
            f"<br><span class='src'>source: {esc(e['source'])}</span></td></tr>"
            for e in brief["sections"][sec]
        )
        sections_html += f"<h2>{esc(brief['section_labels'].get(sec, sec))}</h2><table>{items}</table>"

    rollup = brief["structured_rollup"]
    rollup_html = ("<h2>Structured rollup <span class='src'>source: structured_rollup — deterministic, not AI-generated</span></h2><ul>"
                   + "".join(f"<li>{esc(line)}</li>" for line in rollup["lines"])
                   + f"</ul><p class='src'>{esc(rollup['disclaimer'])}</p>")

    audit_html = "".join(
        f"<tr><td>{time.strftime('%H:%M:%S', time.localtime(a['created_at']))}</td>"
        f"<td>{esc(a['actor'])}</td><td>{esc(a['action'])}</td><td>{esc(a['detail'])}</td></tr>"
        for a in audit
    )

    return 200, f"""<html><head><title>Patient brief</title>{STYLE}</head><body>
{BANNER}<div class="wrap">
{mia_stage_html(stage="working", reason="presenting patient history brief")}
<h1>Patient history brief</h1>
<p>Patient ref: <b>{esc(brief['patient_ref'])}</b> · status: <b>{esc(brief['status'])}</b><br>
<span class="src">bank {esc(brief['bank']['bank_id'])} v{esc(brief['bank']['version'])} ·
review status: {esc(brief['bank']['review_status'])} · original answers preserved</span></p>
<h2>Flags ({brief['flag_count']})</h2>{flags_html}
{sections_html}
{rollup_html}
<h2>Record review</h2>
<form method="POST" action="/api/review" id="revForm">
<input type="hidden" name="clinic_id" value="{clinic_id}">
<input type="hidden" name="sub" value="{sub_id}">
<select name="decision">
<option value="approved">Approved — history reviewed</option>
<option value="needs_clarification">Needs clarification</option>
<option value="flagged">Flagged for follow-up</option>
</select><br><br>
<input type="text" name="reviewer" placeholder="Reviewer name" required style="margin-bottom:8px"><br>
<textarea name="note" placeholder="Review note (optional)"></textarea><br><br>
<button type="submit">Record review</button></form>
<h2>Correct an answer</h2>
<form method="POST" action="/api/correct">
<input type="hidden" name="clinic_id" value="{clinic_id}">
<input type="hidden" name="sub" value="{sub_id}">
<input type="text" name="qid" placeholder="question id (e.g. med.list)" required style="margin-bottom:8px"><br>
<textarea name="new_value" placeholder="Corrected value" required></textarea><br><br>
<input type="text" name="author" placeholder="Your name" required style="margin-bottom:8px"><br>
<select name="source"><option value="staff_verified">staff verified with patient</option>
<option value="patient_correction">patient correction</option></select><br><br>
<button type="submit">Record correction</button></form>
<h2>Audit trail</h2>
<table><tr><th>Time</th><th>Actor</th><th>Action</th><th>Detail</th></tr>{audit_html}</table>
<p><a href="/dashboard?clinic={clinic_id}">← back to dashboard</a></p>
</div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    store: ClinicalStore | None = None

    def log_message(self, *a):
        pass  # keep demo output clean; no patient data in logs

    def _send(self, code, body, ctype="text/html"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        if ctype.startswith(("text/", "application/json")):
            self.send_header("Content-Type", ctype + "; charset=utf-8")
        else:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self):
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            raise ValueError("invalid Content-Length")
        if length <= 0:
            raise ValueError("request body is required")
        if length > MAX_REQUEST_BODY:
            raise OverflowError("request body exceeds the demo limit")
        return self.rfile.read(length)

    def _resolve_clinic(self, clinic_id):
        if not isinstance(clinic_id, str) or clinic_id not in DEMO_CLINIC_IDS:
            return None
        return dict(DEMO_CLINICS).get(clinic_id)

    def _valid_submission_id(self, submission_id):
        return bool(isinstance(submission_id, str) and SUBMISSION_ID_RE.fullmatch(submission_id))

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json")

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        clinic_id = q.get("clinic", [""])[0]
        if u.path == "/":
            self._send(200, render_landing())
        elif u.path in ("/intake", "/dashboard", "/record", "/api/audit", "/medication-review"):
            name = self._resolve_clinic(clinic_id)
            if name is None:
                self._send(404, "Unknown demo clinic.")
                return
            if u.path == "/intake":
                self._send(200, render_intake(clinic_id, name))
            elif u.path == "/medication-review":
                self._send(200, render_medication_review(clinic_id, name))
            elif u.path == "/dashboard":
                self._send(200, render_dashboard(clinic_id, name, self.store))
            elif u.path == "/record":
                sub_id = q.get("sub", [""])[0]
                if not self._valid_submission_id(sub_id):
                    self._send(404, "Submission not found.")
                    return
                code, body = render_record(clinic_id, sub_id, self.store)
                self._send(code, body)
            else:
                target = q.get("target", [""])[0]
                if not self._valid_submission_id(target):
                    self._send(404, "Submission not found.")
                    return
                try:
                    self.get_submission_guard(clinic_id, target)
                    self._json(200, {"audit": self.store.audit_trail(clinic_id, target)})
                except TenantMismatchError:
                    self._json(403, {"ok": False, "error": "Cross-clinic access denied."})
                except KeyError:
                    self._json(404, {"ok": False, "error": "Submission not found."})
        elif u.path == "/assets/mia-stand-hi.webp":
            asset = BASE / "static" / "mia-stand-hi.webp"
            try:
                data = asset.read_bytes()
            except OSError:
                self._send(404, "Mia avatar asset not found.")
                return
            self._send(200, data, "image/webp")
        elif u.path == "/api/questions":
            self._json(200, {"bank": bank_snapshot(BANK),
                             "questions": [{"qid": x.qid, "section": x.section,
                                             "text": x.text, "qtype": x.qtype,
                                             "required": x.required,
                                             "options": list(x.options),
                                             "show_if": x.show_if}
                                            for x in BANK.questions]})
        elif u.path == "/api/manifest":
            from .mia_shell import DENTAL_MIA
            self._json(200, DENTAL_MIA.to_dict())
        elif u.path == "/api/fhir/questionnaire":
            self._json(200, BANK.to_fhir_questionnaire())
        elif u.path == "/api/fhir/questionnaire-response":
            clinic_id = q.get("clinic", [""])[0]
            sub_id = q.get("sub", [""])[0]
            if clinic_id not in DEMO_CLINIC_IDS or not self._valid_submission_id(sub_id):
                self._json(404, {"ok": False, "error": "Demo submission not found."})
                return
            try:
                submission = self.store.get_submission(clinic_id, sub_id)
            except TenantMismatchError:
                self._json(403, {"ok": False, "error": "Cross-clinic access denied."})
                return
            except KeyError:
                self._json(404, {"ok": False, "error": "Demo submission not found."})
                return
            self._json(200, to_fhir_questionnaire_response(
                BANK, submission["answers"], submission["submission_id"]
            ))
        else:
            self._send(404, "Not found.")

    def get_submission_guard(self, clinic_id, sub_id):
        # Raises TenantMismatchError / KeyError — never returns cross-tenant data.
        return self.store.get_submission(clinic_id, sub_id)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            raw = self._read_body()
        except OverflowError:
            self._send(413, "Request body too large.")
            return
        except ValueError:
            self._send(400, "Invalid request body.")
            return
        ctype = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()

        if u.path == "/api/medication-review":
            if ctype != "application/json":
                self._json(415, {"ok": False, "error": "Content-Type must be application/json"})
                return
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(400, {"ok": False, "error": "invalid JSON"})
                return
            if not isinstance(payload, dict):
                self._json(400, {"ok": False, "error": "request must be a JSON object"})
                return
            clinic_id = payload.get("clinic_id", "")
            if clinic_id not in DEMO_CLINIC_IDS:
                self._json(404, {"ok": False, "error": "unknown demo clinic"})
                return
            demo_label = payload.get("demo_patient_label", "")
            if not isinstance(demo_label, str) or not DEMO_PATIENT_LABEL_RE.fullmatch(demo_label):
                self._json(422, {"ok": False, "error": "Use a fictional label beginning with Demo, Test, or Sample."})
                return
            allergies = payload.get("allergies", [])
            medications = payload.get("current_medications", [])
            extra_facts = payload.get("additional_facts", {})
            if (not isinstance(allergies, list) or any(not isinstance(x, str) for x in allergies)
                    or not isinstance(medications, list) or any(not isinstance(x, str) for x in medications)):
                self._json(422, {"ok": False, "error": "allergies and current_medications must be lists of strings"})
                return
            if (not isinstance(extra_facts, dict)
                    or any(not isinstance(k, str) or not k.strip()
                           or (v is not None and isinstance(v, (dict, list)))
                           for k, v in extra_facts.items())):
                self._json(422, {"ok": False, "error": "additional_facts must be an object of scalar values"})
                return

            # Extra facts are applied first; trusted, explicitly reviewed form fields override them.
            facts = dict(extra_facts)
            facts.update({
                "age_years": payload.get("age_years"),
                "allergies_reviewed": payload.get("allergies_reviewed") is True,
                "allergies": allergies,
                "current_medications_reviewed": payload.get("current_medications_reviewed") is True,
                "current_medications": medications,
                "pregnancy_status": payload.get("pregnancy_status", "unknown"),
                "lactation_status": payload.get("lactation_status", "unknown"),
                "severe_allergy": payload.get("severe_allergy", "unknown"),
                "renal_function": payload.get("renal_function", "unknown"),
                "hepatic_function": payload.get("hepatic_function", "unknown"),
            })
            catalog = load_medication_catalog()
            review = review_medication_options({
                "specialty": payload.get("specialty"),
                "diagnosis_code": payload.get("diagnosis_code"),
                "patient_facts": facts,
            }, catalog)
            self._json(200, {
                "ok": True,
                "demo_patient_label": demo_label,
                "catalog": {
                    "catalog_id": catalog.get("catalog_id"),
                    "version": catalog.get("version"),
                    "status": catalog.get("status"),
                },
                "review": review,
                "persisted": False,
                "prescription_created": False,
            })
            return

        if u.path == "/api/intake":
            if ctype != "application/json":
                self._json(415, {"ok": False, "errors": ["Content-Type must be application/json"]})
                return
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(400, {"ok": False, "errors": ["invalid JSON"]})
                return
            if not isinstance(payload, dict):
                self._json(400, {"ok": False, "errors": ["request must be a JSON object"]})
                return
            clinic_id = payload.get("clinic_id", "")
            if clinic_id not in DEMO_CLINIC_IDS:
                self._json(404, {"ok": False, "errors": ["unknown demo clinic"]})
                return
            answers = payload.get("answers", {})
            result = process_intake(BANK, answers)
            if not result["valid"]:
                self._json(422, {"ok": False, "errors": result["errors"],
                                 "missing": result["missing_required"]})
                return
            patient_ref = answers.get("id.demo_label", "")
            if not isinstance(patient_ref, str) or not DEMO_PATIENT_LABEL_RE.fullmatch(patient_ref):
                self._json(422, {"ok": False, "errors": [
                    "Use a fictional patient label beginning with Demo, Test, or Sample."
                ]})
                return
            try:
                sub_id = self.store.save_submission(
                    clinic_id, BANK.bank_id, BANK.version, patient_ref, answers)
            except (TenantMismatchError, ValueError):
                self._json(400, {"ok": False, "errors": ["Could not save this demo intake."]})
                return
            self._json(201, {"ok": True, "submission_id": sub_id,
                             "contradictions": result["contradictions"],
                             "needs_confirmation": result["needs_confirmation"]})
            return

        # Form-encoded review/correction actions remain available only for fixed demo clinics.
        if ctype != "application/x-www-form-urlencoded":
            self._send(415, "Content-Type must be application/x-www-form-urlencoded.")
            return
        try:
            form = parse_qs(raw.decode("utf-8", errors="strict"), max_num_fields=30)
        except (UnicodeDecodeError, ValueError):
            self._send(400, "Invalid form body.")
            return
        get = lambda k: (form.get(k, [""])[0] or "").strip()
        clinic_id, sub_id = get("clinic_id"), get("sub")
        if clinic_id not in DEMO_CLINIC_IDS or not self._valid_submission_id(sub_id):
            self._send(404, "Submission not found.")
            return
        if u.path == "/api/review":
            try:
                self.store.record_review(clinic_id, sub_id, get("reviewer"),
                                         get("decision"), get("note"))
            except TenantMismatchError:
                self._send(403, "Cross-clinic access denied.")
                return
            except (KeyError, ValueError) as e:
                self._send(400, f"Review failed: {esc(str(e))}")
                return
            self.send_response(303)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Location", f"/record?clinic={clinic_id}&sub={sub_id}")
            self.end_headers()
        elif u.path == "/api/correct":
            if BANK.get(get("qid")) is None:
                self._send(400, "Unknown question id.")
                return
            try:
                self.store.record_correction(clinic_id, sub_id, get("qid"),
                                             get("new_value"), get("source"),
                                             get("author"))
            except TenantMismatchError:
                self._send(403, "Cross-clinic access denied.")
                return
            except (KeyError, ValueError) as e:
                self._send(400, f"Correction failed: {esc(str(e))}")
                return
            self.send_response(303)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Location", f"/record?clinic={clinic_id}&sub={sub_id}")
            self.end_headers()
        else:
            self._send(404, "Not found.")


def ensure_demo_clinics(store: ClinicalStore):
    for cid, name in DEMO_CLINICS:
        store.register_clinic(cid, name)


def run(host="127.0.0.1", port=8766):
    if host != "127.0.0.1":
        raise ValueError("The synthetic demo server must bind to 127.0.0.1 only.")
    store = ClinicalStore(DB_PATH)
    ensure_demo_clinics(store)
    Handler.store = store
    srv = HTTPServer((host, port), Handler)
    print(f"Mia Clinical demo on http://{host}:{port}  (synthetic data only)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        store.close()


if __name__ == "__main__":
    run()
