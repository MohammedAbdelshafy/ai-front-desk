"""Mia Dental OS — local demo server.

Mia Dental Prescribing Copilot is the active module. Everything else is a
locked teaser. stdlib only.

Run:  python -m ai_front_desk.clinical.prescribe.server
Then: http://127.0.0.1:8767/

SYNTHETIC DATA ONLY. Demo clinic selector via query string; production
MUST use authenticated routing. No external sends, bookings, or messages.
No real billing — billing.py is TEST MODE ONLY.
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

from ..mia_shell import CharacterManifest
from . import REFERENCE_DISCLAIMER, REFERENCE_VERSION
from .billing import provider as billing_provider, TEST_MODE
from .checker import check_prescription
from .reference_data import DRUGS, REFERENCE_DATE, SOURCES, GENERAL_SOURCES
from .store import PrescribeStore, TenantMismatchError
from .trial import (
    SUBSCRIPTION_PRICE_USD,
    activate as trial_activate,
    mark_subscribed,
    paid_features_unlocked,
    status as trial_status,
)

BASE = Path(__file__).resolve().parent
DB_PATH = Path(
    os.environ.get(
        "PRESCRIBE_DB",
        str(Path.home() / ".mia-prescribe" / "prescribe-demo.sqlite3"),
    )
)
PORT = int(os.environ.get("PRESCRIBE_PORT", "8767"))
MAX_BODY = 64 * 1024

DEMO_CLINIC_ID = "demo-smile-arts"
DEMO_CLINIC_NAME = "Smile Arts Dental (demo)"
DEMO_LABEL_RE = re.compile(r"(?:Demo|Test|Sample) [A-Za-z0-9][A-Za-z0-9 _-]{0,44}\Z", re.IGNORECASE)
ID_RE = re.compile(r"(pat|chk)_[a-f0-9]{12}\Z")

PRESCRIBE_MIA = CharacterManifest(
    character_id="prescribe-mia-v1",
    name="Mia",
    role="Prescribing-safety copilot for dental clinics",
    greeting=(
        "Hi, I'm Mia. I'll double-check prescriptions against your patient's "
        "record before you sign — allergies, interactions, dosing. You always "
        "make the call; I just make sure nothing gets missed."
    ),
    allowed_actions=("safety_check", "show_reference", "show_history"),
    domain_pack_ids=("dental-prescribing@reference-v2",),
    handoff_rules=(
        "On any clinical question beyond the safety check, or any request to "
        "prescribe, transmit, or fill: stop, show the boundary, and direct the "
        "dentist to their own clinical judgment."
    ),
    safety_boundaries=(
        "Assistive only: never prescribe, transmit, or fill prescriptions.",
        "Every flag cites its source rule.",
        "Missing or uncertain data is never shown as verified-safe.",
        "Identify as an AI assistant, not a clinician.",
    ),
)

# Locked upsell tiers — exact names, teasers only. Nothing behind them exists yet.
UPSELL_TIERS = [
    {
        "name": "Mia Dental Practice",
        "blurb": "Team seats, patient intake, and the dentist dashboard — the full front-desk loop for one practice.",
    },
    {
        "name": "Mia Dental Automation",
        "blurb": "Patient communications, scheduling, and recall follow-up on autopilot.",
    },
    {
        "name": "Mia Dental OS Pro",
        "blurb": "Multi-location command, reporting, and integrations for groups and DSOs.",
    },
]

MODULES = [
    {"id": "copilot", "name": "Prescribing Copilot", "icon": "💊", "locked": False,
     "href": "/app/patients"},
    {"id": "intake", "name": "Patient Intake", "icon": "📋", "locked": True},
    {"id": "dashboard", "name": "Dentist Dashboard", "icon": "🖥️", "locked": True},
    {"id": "recall", "name": "Recall & Follow-up", "icon": "🔔", "locked": True},
    {"id": "command", "name": "Command Center", "icon": "📊", "locked": True},
]

STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--ink:#14161a;--mut:#5b6472;--line:#e6e9ef;--bg:#f6f8fb;--brand:#314ca3;--brand2:#eef2ff}
*{box-sizing:border-box}
body{font:16px/1.5 system-ui,-apple-system,sans-serif;margin:0;color:var(--ink);background:var(--bg)}
a{color:var(--brand)}
.wrap{max-width:1060px;margin:0 auto;padding:16px}
.narrow{max-width:720px;margin:0 auto;padding:16px}
.topbar{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.topbar .wrap{display:flex;align-items:center;gap:12px}
.brand{font-weight:800;font-size:18px}
.brand small{font-weight:400;color:var(--mut)}
.pill{margin-left:auto;font-size:13px;padding:4px 12px;border-radius:999px;background:var(--brand2);color:var(--brand);border:1px solid #d7e0ff}
.pill.warn{background:#fff3cd;color:#664d03;border-color:#ffe69c}
.pill.bad{background:#fde8e8;color:#8a1f1f;border-color:#f5c2c2}
.layout{display:flex;gap:0;align-items:stretch;min-height:calc(100vh - 57px)}
.side{width:230px;background:#fff;border-right:1px solid var(--line);padding:14px 10px;flex-shrink:0}
.side a.mod{display:flex;gap:10px;align-items:center;padding:10px 12px;border-radius:10px;color:var(--ink);text-decoration:none;margin-bottom:4px}
.side a.mod.active{background:var(--brand2);font-weight:700}
.side .mod.locked{opacity:.55;cursor:default}
.locktag{font-size:11px;background:#eef1f6;color:var(--mut);border-radius:6px;padding:2px 8px;margin-left:auto}
.main{flex:1;padding:18px;min-width:0}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}
.btn{display:inline-block;background:var(--brand);color:#fff;border:0;border-radius:10px;padding:10px 18px;font-size:16px;cursor:pointer;text-decoration:none}
.btn.ghost{background:#fff;color:var(--brand);border:1px solid var(--brand)}
.btn:disabled{opacity:.5;cursor:default}
input,select,textarea{font:16px system-ui;width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;margin:4px 0 12px}
label{font-weight:600;font-size:14px}
.verdict{font-size:22px;font-weight:800;padding:10px 18px;border-radius:12px;display:inline-block;margin:8px 0}
.v-green{background:#e6f6ec;color:#14632e}
.v-yellow{background:#fff3cd;color:#664d03}
.v-red{background:#fde8e8;color:#8a1f1f}
.v-gray{background:#eef1f6;color:var(--mut)}
.flag{border-left:4px solid var(--line);padding:8px 12px;margin:8px 0;background:#fbfcfe;border-radius:0 8px 8px 0}
.flag.red{border-color:#d33}.flag.yellow{border-color:#e0a800}.flag.info{border-color:#8a94a6}
.src{font-size:13px;color:var(--mut)}
.mia{display:flex;gap:12px;background:linear-gradient(135deg,#eef2ff,#f8f9ff);border:1px solid #dce4ff;border-radius:14px;padding:14px;margin-bottom:14px}
.mia .face{font-size:34px}
.tier{border:1px dashed #b9c4d6;background:#fafbfe}
.steps li{margin-bottom:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line)}
.banner{background:#fff3cd;color:#664d03;padding:10px 14px;font-size:14px;border-bottom:1px solid #ffe69c}
@media(max-width:760px){.side{display:none}.layout{display:block}}
</style>
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def banner() -> str:
    return ("<div class='banner'>DEMO — synthetic data only. Assistive reference aid; "
            "not a substitute for clinical judgment. Not for real patient use.</div>")


def mia_card(subtitle: str = "") -> str:
    return (
        "<div class='mia'><div class='face'>👩‍⚕️</div><div>"
        f"<b>{esc(PRESCRIBE_MIA.name)}</b> · {esc(PRESCRIBE_MIA.role)}<br>"
        f"<span style='color:var(--mut)'>{esc(subtitle or PRESCRIBE_MIA.greeting)}</span>"
        "</div></div>"
    )


def shell(active: str, clinic_name: str, trial: dict, body: str) -> str:
    state = trial["state"]
    if state in ("active", "expiring"):
        pill = f"<span class='pill{' warn' if state == 'expiring' else ''}'>Trial: {trial['days_remaining']:.1f} days left</span>"
    elif state == "subscribed":
        pill = "<span class='pill'>Subscribed</span>"
    else:
        pill = "<span class='pill bad'>Trial expired</span>"
    mods = []
    for m in MODULES:
        if m["locked"]:
            mods.append(
                f"<a class='mod locked'><span>{m['icon']}</span>{esc(m['name'])}"
                f"<span class='locktag'>Full OS</span></a>"
            )
        else:
            cls = "active" if m["id"] == active else ""
            mods.append(
                f"<a class='mod {cls}' href='{m['href']}'><span>{m['icon']}</span>{esc(m['name'])}</a>"
            )
    mods.append(
        "<a class='mod' href='/app/upgrades'><span>⬆️</span>Upgrades</a>"
    )
    return (
        "<!doctype html><html><head><title>Mia Dental OS</title>" + STYLE + "</head><body>"
        + banner()
        + "<div class='topbar'><div class='wrap'>"
        f"<div class='brand'>Mia Dental OS <small>· {esc(clinic_name)}</small></div>{pill}"
        "</div></div>"
        f"<div class='layout'><div class='side'>{''.join(mods)}</div>"
        f"<div class='main'>{body}</div></div>"
        "</body></html>"
    )


def landing_page() -> str:
    return (
        "<!doctype html><html><head><title>Mia Dental OS — Mia Dental Prescribing Copilot</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow'>"
        + mia_card()
        + "<h1>Mia Dental OS</h1>"
        + "<p style='font-size:19px'>The <b>Mia Dental Prescribing Copilot</b> helps young dentists "
        "prescribe correctly: every intended prescription is checked against the patient's "
        "allergies, conditions, and current medications — with each flag citing its source.</p>"
        + "<div class='card'><h3>How the copilot workflow works</h3><ol class='steps'>"
        "<li><b>Open the patient card</b> — allergies, conditions, current meds in one view.</li>"
        "<li><b>Enter the intended prescription</b> — drug, strength, dose, frequency, duration.</li>"
        "<li><b>Get a Green / Yellow / Red check</b> — every flag cites the patient record or the reference rule behind it.</li>"
        "<li><b>You decide.</b> The copilot never prescribes, transmits, or fills — it surfaces what you might have missed.</li>"
        "</ol></div>"
        + "<div class='card'><h3>7-day free trial</h3>"
        "<p>Full copilot access for 7 days, free. After that, "
        f"<b>${SUBSCRIPTION_PRICE_USD}/month</b>. No charges without your explicit subscription — "
        "billing is in test mode while we onboard pilot clinics.</p>"
        "<a class='btn' href='/app/start'>Start the guided demo</a> "
        "<a class='btn ghost' href='/invite'>Dentist sign-up</a></div>"
        + "<div class='card'><h3>Scope & limitations — read this</h3><ul>"
        "<li>Assistive reference aid only. The dentist always decides and prescribes.</li>"
        "<li>Reference dataset v1 (2026-10-11): standard dental prescribing references. Requires dentist review before clinical use.</li>"
        "<li>Missing or uncertain patient data is never shown as verified-safe.</li>"
        "<li>Synthetic demo data only in this preview. Not HIPAA-compliant. Not for real patients.</li>"
        "</ul></div>"
        + "</div></body></html>"
    )


# ---------------------------------------------------------------- pages ---

def trial_page(trial: dict) -> str:
    return (
        "<!doctype html><html><head><title>Start your trial — Mia Dental OS</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow'>" + mia_card()
        + "<h1>7-day free trial</h1>"
        + "<p>The <b>Mia Dental Prescribing Copilot</b> runs free for 7 days from activation. "
        f"After that it's <b>${trial['price_usd']}/month</b> — no charges without your explicit subscription.</p>"
        + "<form method='POST' action='/api/trial/activate'>"
        "<button class='btn' type='submit'>Activate my 7-day trial</button></form>"
        + "<p class='src'>Server-side clock. Reinstalling can't restart the trial.</p>"
        + "</div></body></html>"
    )


def subscribe_page(trial: dict) -> str:
    state = trial["state"]
    headline = "Your trial has expired" if state == "expired" else "Subscription cancelled"
    return (
        "<!doctype html><html><head><title>Subscribe — Mia Dental OS</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow'>" + mia_card()
        + f"<h1>{headline}</h1>"
        + "<p>The copilot module is now locked. <b>Your patient records and check history are preserved</b> — "
        "nothing was deleted and nothing was charged.</p>"
        + "<div class='card'><h3>Mia Dental OS — Prescribing Copilot</h3>"
        f"<p><b>${trial['price_usd']}/month</b>, cancel anytime.</p>"
        "<p class='src'>Billing is in TEST MODE — no real charges, no provider keys. "
        "The founder wires the live provider before any real dentist is billed.</p>"
        + "<form method='POST' action='/api/billing/checkout'>"
        "<button class='btn' type='submit'>Continue (test checkout)</button></form></div>"
        + "</div></body></html>"
    )


def patients_page(store, clinic_id, clinic_name, trial) -> str:
    patients = store.list_patients(clinic_id)
    rows = "".join(
        f"<tr><td><a href='/app/patient?clinic={clinic_id}&id={p['patient_id']}'>{esc(p['label'])}</a></td>"
        f"<td>{len(p['allergies'])}</td><td>{len(p['current_meds'])}</td></tr>"
        for p in patients
    ) or "<tr><td colspan=3 style='color:var(--mut)'>No patients yet — add one below, or run the guided demo.</td></tr>"
    body = (
        mia_card("Pick a patient to open their card, or run a safety check.")
        + "<div class='card'><h2>👥 Patients</h2>"
        f"<table><tr><th>Patient</th><th>Allergies</th><th>Meds</th></tr>{rows}</table></div>"
        + "<div class='card'><h3>Add patient (synthetic demo data)</h3>"
        f"<form method='POST' action='/api/patient?clinic={clinic_id}'>"
        "<label>Label (must start with Demo/Test/Sample)<input name='label' value='Demo Patient ' required></label>"
        "<label>Allergies — one per line: substance | reaction<input name='allergies' placeholder='penicillin | rash'></label>"
        "<label><input type='checkbox' name='no_known_allergies' value='1' style='width:auto'> No known allergies (explicit)</label>"
        "<label>Conditions — comma separated<input name='conditions' placeholder='hypertension'></label>"
        "<label>Current meds — one per line: name | dose<input name='meds' placeholder='warfarin | 5 mg daily'></label>"
        "<label>Reports alcohol use <input type='checkbox' name='alcohol_use' value='1' style='width:auto'></label>"
        "<button class='btn' type='submit'>Add patient</button></form></div>"
    )
    return shell("copilot", clinic_name, trial, body)


def patient_detail_page(store, clinic_id, clinic_name, trial, patient_id) -> str:
    p = store.get_patient(clinic_id, patient_id)
    allergies = "".join(
        f"<li><b>{esc(a.get('substance',''))}</b> — {esc(a.get('reaction',''))} "
        f"<span class='src'>(recorded {esc(a.get('recorded_at','—'))})</span></li>"
        for a in p["allergies"]
    ) or ("<li style='color:var(--mut)'>Explicitly: no known allergies.</li>"
           if p["no_known_allergies"] else
           "<li style='color:#8a1f1f'><b>Not recorded</b> — checks cannot be GREEN until allergies are recorded.</li>")
    conds = "".join(f"<li>{esc(c)}</li>" for c in p["conditions"]) or "<li style='color:var(--mut)'>None recorded.</li>"
    meds = "".join(
        f"<li><b>{esc(m.get('name',''))}</b> <span class='src'>{esc(m.get('dose',''))}</span></li>"
        for m in p["current_meds"]
    ) or "<li style='color:var(--mut)'>None recorded.</li>"
    history = store.check_history(clinic_id, patient_id)
    hrows = "".join(
        f"<tr><td><a href='/app/check?clinic={clinic_id}&id={h['check_id']}'>{h['verdict']}</a></td>"
        f"<td>{esc(h['intended'].get('drug_name',''))}</td>"
        f"<td>{esc(h['review_state'].replace('_',' '))}</td>"
        f"<td class='src'>{time.strftime('%Y-%m-%d %H:%M', time.localtime(h['created_at']))}</td></tr>"
        for h in history
    ) or "<tr><td colspan=4 style='color:var(--mut)'>No checks yet.</td></tr>"
    drug_opts = "".join(f"<option value='{k}'>{v['display']}</option>" for k, v in sorted(DRUGS.items(), key=lambda x: x[1]["display"]))
    body = (
        mia_card(f"Patient card for {p['label']}. Enter what you intend to prescribe — I'll check it against this record.")
        + f"<div class='card'><h2>🧑 {esc(p['label'])}</h2>"
        f"<h4>Allergies</h4><ul>{allergies}</ul>"
        f"<h4>Conditions</h4><ul>{conds}</ul>"
        f"<h4>Current medications</h4><ul>{meds}</ul></div>"
        + f"<p><a class='btn' href='/app/wizard/start?patient={patient_id}'>🧭 Start guided check</a> "
        "<span class='src'>Walks through indication → factors → allergies → meds → conditions → your choice.</span></p>"
        + f"<div class='card'><h3>Quick safety check (skip wizard)</h3>"
        f"<form method='POST' action='/api/check?clinic={clinic_id}'>"
        f"<input type='hidden' name='patient_id' value='{patient_id}'>"
        f"<label>Drug<input name='drug_name' list='drugs' required placeholder='ibuprofen'></label>"
        f"<datalist id='drugs'>{drug_opts}</datalist>"
        "<label>Strength (mg)<input name='strength_mg' type='number' step='any' placeholder='400'></label>"
        "<label>Times per day<input name='times_per_day' type='number' step='any' placeholder='3'></label>"
        "<label>Duration<input name='duration' placeholder='5 days'></label>"
        "<label>Reason<input name='reason' placeholder='post-extraction pain'></label>"
        "<label>Your name (dentist)<input name='dentist' placeholder='Dr. Rivera'></label>"
        "<button class='btn' type='submit'>Run safety check</button></form>"
        f"<p class='src'>{esc(REFERENCE_DISCLAIMER)}</p></div>"
        + f"<div class='card'><h3>Check history</h3><table><tr><th>Verdict</th><th>Drug</th><th>Review</th><th>When</th></tr>{hrows}</table></div>"
    )
    return shell("copilot", clinic_name, trial, body)


def check_result_page(store, clinic_id, clinic_name, trial, check_id) -> str:
    c = store.get_check(clinic_id, check_id)
    vcls = {"GREEN": "v-green", "YELLOW": "v-yellow", "RED": "v-red"}.get(c["verdict"], "v-gray")
    flags = ""
    for f in c["flags"]:
        sev = f["severity"] if f["severity"] in ("red", "yellow") else "info"
        rule = f"<br><span class='src'>Rule: {esc(f['rule_id'])}</span>" if f.get("rule_id") else ""
        flags += (
            f"<div class='flag {sev}'><b>{sev.upper()}</b> — {esc(f['reason'])}"
            f"<br><span class='src'>Source: {esc(f['source'])}</span>{rule}</div>"
        )
    intended = c["intended"]
    review = (
        f"<div class='card'><h3>Clinician review</h3>"
        f"<p>State: <b>{esc(c['review_state'].replace('_', ' '))}</b>"
        + (f" — by {esc(c['reviewed_by'])}" if c["reviewed_by"] else "")
        + (f"<br><span class='src'>{esc(c['review_note'])}</span>" if c["review_note"] else "")
        + "</p><form method='POST' action='/api/review?clinic=" + clinic_id + "'>"
        f"<input type='hidden' name='check_id' value='{check_id}'>"
        "<label>Your conclusion (recorded with timestamp + audit)<textarea name='note' rows='2' placeholder='Reviewed — proceeding with alternative…'></textarea></label>"
        "<label>Mark as<select name='state'>"
        "<option value='clinician_reviewed'>Clinician reviewed</option>"
        "<option value='escalated'>Escalated</option></select></label>"
        "<label>Your name<input name='by' placeholder='Dr. Rivera'></label>"
        "<button class='btn' type='submit'>Record review</button></form>"
        "<p class='src'>Only the dentist's own conclusion counts. The app never marks a check reviewed by itself.</p></div>"
    )
    body = (
        mia_card("Check complete. Every flag below cites its source — you make the call.")
        + f"<div class='card'><h2>Safety check — {esc(intended.get('drug_name',''))}</h2>"
        f"<span class='verdict {vcls}'>{esc(c['verdict'])}</span>"
        f"<p class='src'>Intended: {esc(str(intended.get('strength_mg','—')))} mg × "
        f"{esc(str(intended.get('times_per_day','—')))} /day"
        + (f", {esc(intended.get('duration',''))}" if intended.get("duration") else "")
        + (f" — {esc(intended.get('reason',''))}" if intended.get("reason") else "")
        + f"<br>Dentist: {esc(c['dentist'] or '—')}</p>"
        + (flags or "<p>No flags.</p>")
        + f"<p class='src'>{esc(REFERENCE_DISCLAIMER)}</p></div>"
        + review
        + f"<p><a href='/app/patient?clinic={clinic_id}&id={c['patient_id']}'>← Back to patient card</a></p>"
    )
    return shell("copilot", clinic_name, trial, body)


def reference_page(clinic_id, clinic_name, trial) -> str:
    cats: dict[str, list] = {}
    for key, d in DRUGS.items():
        cats.setdefault(d["category"], []).append((key, d))

    def _src_links(key: str) -> str:
        links = "".join(
            f"<br>· <a href='{esc(s['url'])}' target='_blank' rel='noopener'>{esc(s['name'])}</a>"
            f" <span class='src'>(accessed {esc(s['accessed'])}) — {esc(s['supports'])}</span>"
            for s in SOURCES.get(key, [])
        )
        return f"<span class='src'><b>Cited sources:</b>{links}</span>" if links else ""

    sections = ""
    for cat in ("Antibiotic", "Analgesic", "Anxiolytic"):
        items = "".join(
            f"<div class='card'><h4>{esc(d['display'])}</h4>"
            f"<p><b>Standard adult:</b> {esc(d['standard_adult'])}<br>"
            f"<b>Reference max:</b> {d['max_daily_mg']:g} mg/day<br>"
            f"<span class='src'>{esc(d['notes'])}</span><br>{_src_links(key)}</p></div>"
            for key, d in sorted(cats.get(cat, []), key=lambda x: x[1]["display"])
        )
        sections += f"<h3>{cat}s</h3>{items}"
    gen = "".join(
        f"<br>· <a href='{esc(s['url'])}' target='_blank' rel='noopener'>{esc(s['name'])}</a>"
        f" <span class='src'>(accessed {esc(s['accessed'])}) — {esc(s['supports'])}</span>"
        for s in GENERAL_SOURCES
    )
    body = (
        mia_card("Standard dental prescribing references. Reference info — not recommendations.")
        + f"<div class='card'><p><b>Dataset:</b> {REFERENCE_VERSION} ({REFERENCE_DATE}) — "
        "requires dentist review before clinical use. Uncertain rules are omitted, not guessed."
        f"<br><span class='src'><b>Guidance sources:</b>{gen}</span></p></div>"
        + sections
    )
    return shell("copilot", clinic_name, trial, body)


def upgrades_page(clinic_id, clinic_name, trial) -> str:
    tiers = "".join(
        f"<div class='card tier'><h3>🔒 {esc(t['name'])}</h3><p>{esc(t['blurb'])}</p>"
        "<p class='src'>Available in the full Mia Dental OS — ask about the pilot.</p>"
        "<button class='btn' disabled>Locked</button></div>"
        for t in UPSELL_TIERS
    )
    body = (
        mia_card("The Prescribing Copilot is your wedge. Here's where Mia Dental OS goes next.")
        + "<h2>Upgrades</h2>" + tiers
        + "<div class='card'><h3>Also in the full OS</h3><ul>"
        "<li>📋 Patient Intake — locked teaser</li>"
        "<li>🖥️ Dentist Dashboard — locked teaser</li>"
        "<li>🔔 Recall &amp; Follow-up — locked teaser</li>"
        "<li>📊 Command Center — locked teaser</li></ul>"
        "<p class='src'>These modules are not built yet. The copilot is the working product today.</p></div>"
    )
    return shell("", clinic_name, trial, body)


def invite_page() -> str:
    return (
        "<!doctype html><html><head><title>Dentist sign-up — Mia Dental OS</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow'>" + mia_card()
        + "<h1>Dentist sign-up</h1>"
        + "<p>Request a pilot invite. We'll reach out personally — no automated onboarding, no spam.</p>"
        + "<div class='card'><form method='POST' action='/api/invite'>"
        "<label>Full name<input name='name' required placeholder='Dr. Jane Rivera'></label>"
        "<label>Clinic name<input name='clinic' required placeholder='Rivera Dental'></label>"
        "<label>Work email<input name='email' type='email' required placeholder='jane@riveradental.com'></label>"
        "<button class='btn' type='submit'>Request invite</button></form>"
        "<p class='src'>Stored locally in this demo. In production, invites go through the pilot team.</p></div>"
        + "</div></body></html>"
    )


def start_page(store, clinic_id, clinic_name, trial) -> str:
    body = (
        mia_card("60 seconds to get it. Three steps — trial, sample patient, sample check.")
        + "<div class='card'><h2>Guided first run</h2><ol class='steps'>"
        "<li><b>Trial active ✅</b> — you're inside the 7-day free trial.</li>"
        "<li><b>Load a sample patient</b> — synthetic record with a penicillin allergy and warfarin on board."
        f"<form method='POST' action='/api/sample-patient?clinic={clinic_id}' style='margin-top:8px'>"
        "<button class='btn ghost' type='submit'>Load sample patient</button></form></li>"
        "<li><b>Run the sample check</b> — ibuprofen 400 mg three times daily. Watch Mia flag it."
        f"<form method='POST' action='/api/sample-check?clinic={clinic_id}' style='margin-top:8px'>"
        "<button class='btn ghost' type='submit'>Run sample check</button></form></li>"
        "</ol>"
        f"<p><a class='btn' href='/app/patients?clinic={clinic_id}'>Or explore patients →</a></p></div>"
    )
    return shell("copilot", clinic_name, trial, body)


# ------------------------------------------------------------- handler ---

STORE: PrescribeStore | None = None


def get_store() -> PrescribeStore:
    global STORE
    if STORE is None:
        STORE = PrescribeStore(DB_PATH)
    return STORE


def _clinic_name() -> str:
    return DEMO_CLINIC_NAME


def _send(handler, code: int, body: str, content_type="text/html; charset=utf-8"):
    data = body.encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _redirect(handler, location: str):
    handler.send_response(303)
    handler.send_header("Location", location)
    handler.end_headers()


def _valid_id(value: str) -> bool:
    return bool(ID_RE.match(value or ""))


def _gate(handler, path: str) -> dict | None:
    """Trial gate for /app/* routes. Returns trial dict or sends redirect."""
    t = trial_status()
    if paid_features_unlocked():
        return t
    if t["state"] in ("eligible",):
        _redirect(handler, "/trial")
    else:
        _redirect(handler, "/subscribe")
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "MiaDentalOS/1.0"

    def log_message(self, *args):  # quiet
        pass

    # -- GET ------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        clinic = DEMO_CLINIC_ID
        try:
            if url.path == "/":
                _send(self, 200, landing_page())
            elif url.path == "/trial":
                _send(self, 200, trial_page(trial_status()))
            elif url.path == "/subscribe":
                _send(self, 200, subscribe_page(trial_status()))
            elif url.path == "/invite":
                _send(self, 200, invite_page())
            elif url.path == "/app/start":
                t = _gate(self, url.path)
                if t is None:
                    return
                _send(self, 200, start_page(get_store(), clinic, _clinic_name(), t))
            elif url.path == "/app/patients":
                t = _gate(self, url.path)
                if t is None:
                    return
                _send(self, 200, patients_page(get_store(), clinic, _clinic_name(), t))
            elif url.path == "/app/patient":
                t = _gate(self, url.path)
                if t is None:
                    return
                pid = q.get("id", [""])[0]
                if not _valid_id(pid):
                    _send(self, 400, "bad patient id")
                    return
                _send(self, 200, patient_detail_page(get_store(), clinic, _clinic_name(), t, pid))
            elif url.path == "/app/check":
                t = _gate(self, url.path)
                if t is None:
                    return
                cid = q.get("id", [""])[0]
                if not _valid_id(cid):
                    _send(self, 400, "bad check id")
                    return
                _send(self, 200, check_result_page(get_store(), clinic, _clinic_name(), t, cid))
            elif url.path == "/app/reference":
                t = _gate(self, url.path)
                if t is None:
                    return
                _send(self, 200, reference_page(clinic, _clinic_name(), t))
            elif url.path == "/app/upgrades":
                t = _gate(self, url.path)
                if t is None:
                    return
                _send(self, 200, upgrades_page(clinic, _clinic_name(), t))
            elif url.path == "/app/wizard/start":
                t = _gate(self, url.path)
                if t is None:
                    return
                pid = q.get("patient", [""])[0]
                patient = None
                if pid:
                    if not _valid_id(pid):
                        _send(self, 400, "bad patient id")
                        return
                    patient = get_store().get_patient(clinic, pid)
                state = WIZARDS.create(clinic, patient)
                _redirect(self, f"/app/wizard/{state['token']}/{STEPS[0]}")
            elif url.path.startswith("/app/wizard/"):
                t = _gate(self, url.path)
                if t is None:
                    return
                m = re.match(r"/app/wizard/(wz_[a-f0-9]{12})/([a-z]+)\Z", url.path)
                if not m:
                    _send(self, 404, "not found")
                    return
                state = _wizard_or_404(m.group(1))
                if state is None:
                    _send(self, 404, "wizard session expired")
                    return
                step = m.group(2)
                if step == "summary":
                    _send(self, 200, wizard_summary_page(state, _clinic_name(), t))
                elif step == "choose":
                    _send(self, 200, wizard_choose_page(state, _clinic_name(), t))
                elif step in STEPS:
                    _send(self, 200, wizard_step_page(state, step, _clinic_name(), t))
                else:
                    _send(self, 404, "not found")
            else:
                _send(self, 404, "not found")
        except (KeyError, TenantMismatchError) as e:
            _send(self, 403 if isinstance(e, TenantMismatchError) else 404, esc(str(e)))

    # -- POST -----------------------------------------------------
    def do_POST(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        clinic = DEMO_CLINIC_ID
        # Read the request body ONCE (a second rfile read would block forever).
        length = int(self.headers.get("Content-Length", 0) or 0)
        _raw = self.rfile.read(min(length, MAX_BODY)).decode("utf-8", errors="replace")
        _parsed = parse_qs(_raw)
        form = {k: v[0] for k, v in _parsed.items()}
        form_multi = dict(_parsed)
        store = get_store()
        try:
            if url.path == "/api/trial/activate":
                trial_activate()
                _redirect(self, "/app/start")
            elif url.path == "/api/billing/checkout":
                if not isinstance(billing_provider, object):
                    _send(self, 500, "billing unavailable")
                    return
                session = billing_provider.create_checkout(clinic, SUBSCRIPTION_PRICE_USD)
                # TEST MODE: simulate the dentist completing the test checkout.
                if TEST_MODE and hasattr(billing_provider, "start_test_subscription"):
                    ref = billing_provider.start_test_subscription(clinic)
                    mark_subscribed(ref)
                _redirect(self, f"/app/start?test_checkout={session.session_id}")
            elif url.path == "/api/patient":
                t = _gate(self, url.path)
                if t is None:
                    return
                label = form.get("label", "").strip()
                if not DEMO_LABEL_RE.match(label):
                    _send(self, 400, "patient label must look synthetic (Demo/Test/Sample …)")
                    return
                allergies = _parse_lines(form.get("allergies", ""), 2)
                meds = _parse_lines(form.get("meds", ""), 2)
                conditions = [c.strip() for c in form.get("conditions", "").split(",") if c.strip()]
                reports = {"alcohol_use": bool(form.get("alcohol_use"))}
                pid = store.add_patient(
                    clinic, label,
                    allergies=[{"substance": a[0], "reaction": a[1], "recorded_at": time.strftime("%Y-%m-%d")} for a in allergies],
                    conditions=conditions,
                    current_meds=[{"name": m[0], "dose": m[1]} for m in meds],
                    reports=reports,
                    no_known_allergies=bool(form.get("no_known_allergies")),
                )
                _redirect(self, f"/app/patient?clinic={clinic}&id={pid}")
            elif url.path == "/api/sample-patient":
                t = _gate(self, url.path)
                if t is None:
                    return
                pid = store.add_patient(
                    clinic, "Demo Patient Rivera",
                    allergies=[{"substance": "penicillin", "reaction": "rash",
                                "recorded_at": "2026-10-11"}],
                    conditions=["hypertension"],
                    current_meds=[{"name": "warfarin", "dose": "5 mg daily"}],
                    reports={},
                )
                _redirect(self, f"/app/patient?clinic={clinic}&id={pid}")
            elif url.path == "/api/sample-check":
                t = _gate(self, url.path)
                if t is None:
                    return
                patients = store.list_patients(clinic)
                if not patients:
                    _send(self, 400, "load the sample patient first")
                    return
                pid = patients[0]["patient_id"]
                intended = {"drug_name": "ibuprofen", "strength_mg": 400,
                            "times_per_day": 3, "duration": "5 days",
                            "reason": "post-extraction pain"}
                result = check_prescription(store.get_patient(clinic, pid), intended)
                cid = store.record_check(clinic, pid, "Dr. Demo", intended,
                                         result.verdict,
                                         [f.__dict__ for f in result.flags])
                _redirect(self, f"/app/check?clinic={clinic}&id={cid}")
            elif url.path == "/api/check":
                t = _gate(self, url.path)
                if t is None:
                    return
                pid = form.get("patient_id", "")
                if not _valid_id(pid):
                    _send(self, 400, "bad patient id")
                    return
                intended = {
                    "drug_name": form.get("drug_name", "").strip(),
                    "strength_mg": _num(form.get("strength_mg")),
                    "times_per_day": _num(form.get("times_per_day")),
                    "duration": form.get("duration", "").strip(),
                    "reason": form.get("reason", "").strip(),
                }
                if not intended["drug_name"]:
                    _send(self, 400, "drug name is required")
                    return
                patient = store.get_patient(clinic, pid)
                result = check_prescription(patient, intended)
                cid = store.record_check(
                    clinic, pid, form.get("dentist", "").strip() or "Dr. Demo",
                    intended, result.verdict, [f.__dict__ for f in result.flags],
                )
                _redirect(self, f"/app/check?clinic={clinic}&id={cid}")
            elif url.path == "/api/review":
                t = _gate(self, url.path)
                if t is None:
                    return
                cid = form.get("check_id", "")
                state = form.get("state", "")
                by = form.get("by", "").strip() or "dentist"
                if not _valid_id(cid):
                    _send(self, 400, "bad check id")
                    return
                store.set_review_state(clinic, cid, state, by, form.get("note", "").strip())
                _redirect(self, f"/app/check?clinic={clinic}&id={cid}")
            elif url.path.startswith("/api/wizard/"):
                t = _gate(self, url.path)
                if t is None:
                    return
                m = re.match(r"/api/wizard/(wz_[a-f0-9]{12})/([a-z]+)\Z", url.path)
                if not m:
                    _send(self, 404, "not found")
                    return
                state = _wizard_or_404(m.group(1))
                if state is None:
                    _send(self, 404, "wizard session expired")
                    return
                token, step = m.group(1), m.group(2)
                multi = form_multi
                if step == "indication":
                    WIZARDS.update(token, {
                        "indication": form.get("indication", ""),
                        "indication_notes": form.get("indication_notes", "").strip(),
                    })
                    _redirect(self, f"/app/wizard/{token}/factors")
                elif step == "factors":
                    WIZARDS.update(token, {"factors": {
                        "age_band": form.get("age_band", ""),
                        "pregnancy": form.get("pregnancy", ""),
                        "lactation": form.get("lactation", ""),
                        "renal": form.get("renal", ""),
                        "hepatic": form.get("hepatic", ""),
                        "weight_kg": form.get("weight_kg", "").strip(),
                    }})
                    _redirect(self, f"/app/wizard/{token}/allergies")
                elif step == "allergies":
                    allergies = [
                        {"substance": b[0], "reaction": b[1], "recorded_at": "wizard"}
                        for b in _parse_lines(form.get("allergies", ""), 2) if b[0]
                    ]
                    WIZARDS.update(token, {
                        "allergies": allergies,
                        "no_known_allergies": bool(form.get("no_known_allergies")),
                        "latex_allergy": form.get("latex_allergy", ""),
                        "anesthesia_history": form.get("anesthesia_history", "").strip(),
                    })
                    _redirect(self, f"/app/wizard/{token}/medications")
                elif step == "medications":
                    meds = [
                        {"name": b[0], "dose": b[1]}
                        for b in _parse_lines(form.get("meds", ""), 2) if b[0]
                    ]
                    WIZARDS.update(token, {"meds": meds})
                    _redirect(self, f"/app/wizard/{token}/conditions")
                elif step == "conditions":
                    conds = [c for c in multi.get("cond", []) if c in CONDITION_CHECKLIST]
                    WIZARDS.update(token, {"conditions": conds})
                    _redirect(self, f"/app/wizard/{token}/summary")
                elif step == "finish":
                    drug_name = form.get("drug_name", "").strip()
                    if not drug_name:
                        _send(self, 400, "drug name is required")
                        return
                    intended = {
                        "drug_name": drug_name,
                        "strength_mg": _num(form.get("strength_mg")),
                        "times_per_day": _num(form.get("times_per_day")),
                        "duration": form.get("duration", "").strip(),
                        "reason": form.get("reason", "").strip(),
                        "indication": state["indication"],
                    }
                    from .checker import Flag as _Flag
                    context = build_patient_context(state)
                    result = check_prescription(context, intended)
                    # Attach missing-info flags so unknowns are visible, never
                    # hidden. They are info-severity: they never change a
                    # red/yellow verdict and never turn CANNOT_VERIFY green.
                    for mf in missing_info_flags(state):
                        result.flags.append(_Flag(
                            mf["severity"], mf["reason"], mf["source"], mf["rule_id"]))
                    patient_id = state.get("patient_id")
                    if not patient_id:
                        patient_id = store.add_patient(
                            clinic, f"Demo Patient Wizard",
                            allergies=context["allergies"],
                            conditions=context["conditions"],
                            current_meds=context["current_meds"],
                        )
                    cid = store.record_check(
                        clinic, patient_id,
                        form.get("dentist", "").strip() or "Dr. Demo",
                        intended, result.verdict,
                        [f.__dict__ for f in result.flags],
                    )
                    _redirect(self, f"/app/check?clinic={clinic}&id={cid}")
                else:
                    _send(self, 404, "not found")
            elif url.path == "/api/invite":
                # Stored locally; the pilot team follows up personally.
                invites = BASE / "invites.jsonl"
                with open(invites, "a") as f:
                    f.write(json.dumps({
                        "name": form.get("name", ""), "clinic": form.get("clinic", ""),
                        "email": form.get("email", ""), "at": time.time(),
                    }) + "\n")
                _send(self, 200,
                      "<!doctype html><html><head><title>Thanks</title>" + STYLE +
                      "</head><body><div class='narrow'><h1>You're on the list.</h1>"
                      "<p>We'll reach out personally about the pilot. No spam, no drip sequence.</p>"
                      "<p><a href='/'>← Back</a></p></div></body></html>")
            else:
                _send(self, 404, "not found")
        except (KeyError, TenantMismatchError, ValueError) as e:
            code = 403 if isinstance(e, TenantMismatchError) else 400
            _send(self, code, esc(str(e)))


def _parse_lines(text: str, parts: int) -> list[list[str]]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        bits = [b.strip() for b in line.split("|")]
        while len(bits) < parts:
            bits.append("")
        out.append(bits[:parts])
    return out


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Mia Dental OS demo → http://127.0.0.1:{PORT}/  (synthetic data only)")
    server.serve_forever()


if __name__ == "__main__":
    main()


# --------------------------------------------------------------- wizard ---

from .wizard import (  # noqa: E402
    WizardSessions,
    STEPS,
    missing_info_flags,
    build_patient_context,
    indication_options,
    AGE_BANDS,
    YES_NO_UNK,
    CONDITION_CHECKLIST,
    UNKNOWN,
)
from .reference_data import INDICATIONS  # noqa: E402

WIZARDS = WizardSessions()
WIZ_TOKEN_RE = re.compile(r"wz_[a-f0-9]{12}\Z")


def _wizard_or_404(token: str):
    state = WIZARDS.get(token)
    return state


def _select(name: str, options: list[str], current: str) -> str:
    opts = "".join(
        f"<option value='{esc(o)}'{' selected' if o == current else ''}>{esc(o)}</option>"
        for o in options
    )
    return f"<select name='{name}'><option value=''>— choose —</option>{opts}</select>"


def wizard_step_page(state: dict, step: str, clinic_name: str, trial: dict) -> str:
    idx = STEPS.index(step)
    nxt = STEPS[idx + 1] if idx + 1 < len(STEPS) else None
    token = state["token"]
    inner = ""
    if step == "indication":
        radios = "".join(
            f"<label style='display:block;font-weight:400;margin:6px 0'>"
            f"<input type='radio' name='indication' value='{k}' style='width:auto'"
            f"{' checked' if state['indication'] == k else ''}> {esc(label)}</label>"
            for k, label in indication_options()
        )
        inner = (f"<h2>Step 1 of 7 — Indication</h2><p>What are you treating?</p>{radios}"
                 f"<label>Procedure / context notes<textarea name='indication_notes' rows='2'>"
                 f"{esc(state['indication_notes'])}</textarea></label>")
    elif step == "factors":
        f = state["factors"]
        inner = ("<h2>Step 2 of 7 — Patient factors</h2>"
                 f"<label>Age band{_select('age_band', AGE_BANDS, f['age_band'])}</label>"
                 f"<label>Pregnancy{_select('pregnancy', YES_NO_UNK, f['pregnancy'])}</label>"
                 f"<label>Lactation{_select('lactation', YES_NO_UNK, f['lactation'])}</label>"
                 f"<label>Renal issues{_select('renal', YES_NO_UNK, f['renal'])}</label>"
                 f"<label>Hepatic issues{_select('hepatic', YES_NO_UNK, f['hepatic'])}</label>"
                 f"<label>Weight (kg, if relevant)<input name='weight_kg' value='{esc(f['weight_kg'])}' placeholder=\"don't know\"></label>"
                 "<p class='src'>Every question offers “don't know / not applicable”. Unknowns are flagged, never assumed safe.</p>")
    elif step == "allergies":
        lines = "\n".join(f"{a.get('substance','')} | {a.get('reaction','')}" for a in state["allergies"])
        inner = ("<h2>Step 3 of 7 — Allergies</h2>"
                 f"<label>Drug allergies — one per line: substance | reaction<textarea name='allergies' rows='3'>{esc(lines)}</textarea></label>"
                 f"<label><input type='checkbox' name='no_known_allergies' value='1' style='width:auto'{' checked' if state['no_known_allergies'] else ''}> No known drug allergies (explicit)</label>"
                 f"<label>Latex allergy{_select('latex_allergy', YES_NO_UNK, state['latex_allergy'])}</label>"
                 f"<label>Anesthesia history / complications<input name='anesthesia_history' value='{esc(state['anesthesia_history'])}' placeholder=\"don't know\"></label>")
    elif step == "medications":
        lines = "\n".join(f"{m.get('name','')} | {m.get('dose','')}" for m in state["meds"])
        inner = ("<h2>Step 4 of 7 — Current medications</h2>"
                 f"<label>One per line: name | dose/frequency<textarea name='meds' rows='4'>{esc(lines)}</textarea></label>"
                 "<p class='src'>Include OTC, vitamins, and herbal products — interactions don't care about the source.</p>")
    elif step == "conditions":
        boxes = "".join(
            f"<label style='display:block;font-weight:400;margin:4px 0'>"
            f"<input type='checkbox' name='cond' value='{esc(c)}' style='width:auto'"
            f"{' checked' if c in state['conditions'] else ''}> {esc(c)}</label>"
            for c in CONDITION_CHECKLIST
        )
        inner = f"<h2>Step 5 of 7 — Conditions</h2><p>Tick all that apply.</p>{boxes}"
    else:
        inner = "<p>Unknown step.</p>"

    body = (
        mia_card(f"Guided check for {state['patient_label'] or 'new patient'} — step {idx + 1} of 7.")
        + f"<div class='card'><form method='POST' action='/api/wizard/{token}/{step}'>"
        + inner
        + f"<button class='btn' type='submit'>Continue →</button></form></div>"
        + (f"<p><a href='/app/wizard/{token}/{STEPS[idx-1]}'>← Back</a></p>" if idx > 0 else "")
    )
    return shell("copilot", clinic_name, trial, body)


def wizard_summary_page(state: dict, clinic_name: str, trial: dict) -> str:
    token = state["token"]
    f = state["factors"]
    allergies = ", ".join(a.get("substance", "") for a in state["allergies"]) or "—"
    meds = ", ".join(m.get("name", "") for m in state["meds"]) or "—"
    conds = ", ".join(state["conditions"]) or "—"
    ind_label = dict(indication_options()).get(state["indication"], "—")
    missing = missing_info_flags(state)
    mflags = "".join(
        f"<div class='flag info'><b>INFO</b> — {esc(m['reason'])}<br><span class='src'>Source: {esc(m['source'])}</span></div>"
        for m in missing
    )
    rows = [
        ("Indication", f"{ind_label}" + (f" — {state['indication_notes']}" if state["indication_notes"] else ""), "indication"),
        ("Age band", f["age_band"] or "—", "factors"),
        ("Pregnancy / lactation", f"{f['pregnancy'] or '—'} / {f['lactation'] or '—'}", "factors"),
        ("Renal / hepatic", f"{f['renal'] or '—'} / {f['hepatic'] or '—'}", "factors"),
        ("Weight", f["weight_kg"] or "—", "factors"),
        ("Allergies", allergies + (f" (latex: {state['latex_allergy'] or '—'})"), "allergies"),
        ("Anesthesia history", state["anesthesia_history"] or "—", "allergies"),
        ("Medications", meds, "medications"),
        ("Conditions", conds, "conditions"),
    ]
    table = "".join(
        f"<tr><td><b>{esc(k)}</b></td><td>{esc(v)}</td>"
        f"<td><a href='/app/wizard/{token}/{step}'>edit</a></td></tr>"
        for k, v, step in rows
    )
    body = (
        mia_card("Review everything before choosing. Missing-info flags are shown, never hidden.")
        + f"<div class='card'><h2>Step 6 of 7 — Summary</h2>"
        f"<table>{table}</table></div>"
        + (f"<h3>Missing information</h3>{mflags}" if mflags else "<p>No missing-info flags.</p>")
        + f"<p><a class='btn' href='/app/wizard/{token}/choose'>Continue to prescription choice →</a></p>"
    )
    return shell("copilot", clinic_name, trial, body)


def wizard_choose_page(state: dict, clinic_name: str, trial: dict) -> str:
    token = state["token"]
    ind = INDICATIONS.get(state["indication"] or "other", INDICATIONS["other"])
    ref_tag = f"{REFERENCE_VERSION} ({REFERENCE_DATE})"

    def _drug_rows(items):
        return "".join(
            f"<div class='flag info'><b>{esc(DRUGS[i['drug']]['display'])}</b> — {esc(i['dosing'])}"
            + (f"<br><span class='src'>When: {esc(i['when'])}</span>" if i.get("when") else "")
            + (f"<br><span class='src'>{esc(i['note'])}</span>" if i.get("note") else "")
            + f"<br><span class='src'>Source: {ref_tag} — reference info</span></div>"
            for i in items
        )

    panel = (
        f"<h3>Reference — {esc(ind['display'])}</h3>"
        + (_drug_rows(ind["first_line"]) if ind["first_line"] else "")
        + ("<h4>Alternatives</h4>" + _drug_rows(ind["alternatives"]) if ind["alternatives"] else "")
        + "".join(f"<p class='src'>⚠ {esc(c)}</p>" for c in ind["cautions"])
        + f"<p class='src'>Reference info only ({ref_tag}) — requires dentist review. The dentist selects and decides.</p>"
    )
    drug_opts = "".join(
        f"<option value='{k}'>{esc(v['display'])}</option>"
        for k, v in sorted(DRUGS.items(), key=lambda x: x[1]["display"])
    )
    body = (
        mia_card("Reference options for your indication. You choose — I check your choice.")
        + f"<div class='card'>{panel}</div>"
        + f"<div class='card'><h2>Step 7 of 7 — Your prescription choice</h2>"
        f"<form method='POST' action='/api/wizard/{token}/finish'>"
        f"<label>Drug — your choice<input name='drug_name' list='drugs2' required></label>"
        f"<datalist id='drugs2'>{drug_opts}</datalist>"
        "<label>Strength (mg)<input name='strength_mg' type='number' step='any'></label>"
        "<label>Times per day<input name='times_per_day' type='number' step='any'></label>"
        "<label>Duration<input name='duration' placeholder='5 days'></label>"
        "<label>Reason<input name='reason' placeholder='acute apical abscess'></label>"
        "<label>Your name (dentist)<input name='dentist' placeholder='Dr. Rivera'></label>"
        "<button class='btn' type='submit'>Run safety check on my choice</button></form>"
        "<p class='src'>Mia never auto-selects or issues a prescription. Unknown safety = “cannot verify”, never green.</p></div>"
    )
    return shell("copilot", clinic_name, trial, body)
