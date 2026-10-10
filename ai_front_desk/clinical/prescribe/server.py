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

MIA_AVATAR_URL = (
    "https://raw.githubusercontent.com/MohammedAbdelshafy/"
    "mia-muse-assets/main/mia-hi-thumb-base.jpg"
)

# Inline stroke icons (currentColor) — no emoji as icon language in the workspace.
ICONS = {
    "copilot": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><rect x='3.5' y='8.5' width='17' height='7' rx='3.5' transform='rotate(-45 12 12)'/><path d='M12 6.8v10.4'/></svg>",
    "intake": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><rect x='5' y='4' width='14' height='17' rx='2'/><path d='M9 4a3 3 0 0 1 6 0'/><path d='M9 11h6M9 15h6'/></svg>",
    "dashboard": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'><rect x='3.5' y='3.5' width='7' height='7' rx='1.5'/><rect x='13.5' y='3.5' width='7' height='7' rx='1.5'/><rect x='3.5' y='13.5' width='7' height='7' rx='1.5'/><rect x='13.5' y='13.5' width='7' height='7' rx='1.5'/></svg>",
    "recall": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M18 9a6 6 0 1 0-12 0c0 6-2.5 7-2.5 7h17S18 15 18 9'/><path d='M10 20a2.2 2.2 0 0 0 4 0'/></svg>",
    "command": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'><path d='M4 20V10M10 20V4M16 20v-8M22 20H2'/></svg>",
    "lock": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><rect x='4.5' y='10.5' width='15' height='10' rx='2'/><path d='M8 10.5V7a4 4 0 0 1 8 0v3.5'/></svg>",
    "up": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M12 19V5M5 12l7-7 7 7'/></svg>",
    "check": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='9'/><path d='M8.5 12.5l2.5 2.5 4.5-5.5'/></svg>",
    "alert": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3.5L22 20H2z'/><path d='M12 10v4.5M12 17.5v.01'/></svg>",
    "stop": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M7.9 3.5h8.2L20.5 7.9v8.2l-4.4 4.4H7.9L3.5 16.1V7.9z'/><path d='M9.5 9.5l5 5M14.5 9.5l-5 5'/></svg>",
    "help": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='9'/><path d='M9.5 9.5a2.5 2.5 0 1 1 3.4 2.3c-.8.3-.9 1-.9 1.7'/><path d='M12 17v.01'/></svg>",
    "users": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='9' cy='8' r='3.5'/><path d='M3.5 20a5.5 5.5 0 0 1 11 0'/><path d='M16 4.6a3.5 3.5 0 0 1 0 6.8M17.5 14.7a5.5 5.5 0 0 1 3 5.3'/></svg>",
    "user": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='8' r='4'/><path d='M4.5 20.5a7.5 7.5 0 0 1 15 0'/></svg>",
    "arrow": "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12h14M13 6l6 6-6 6'/></svg>",
}

STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --ink:#152238; --mut:#5d6f86; --line:#dfe7f0;
  --bg:#f2f6fa; --surface:#ffffff;
  --brand:#0d7d8c; --brand-deep:#0a616d; --brand-soft:#e2f2f4; --brand-ink:#074b54;
  --green-bg:#e5f5ea; --green-ink:#166534; --green-line:#9fd8b4;
  --yellow-bg:#fff7dc; --yellow-ink:#7c5200; --yellow-line:#e8c547;
  --red-bg:#fdeceb; --red-ink:#b42318; --red-line:#f3b3ac;
  --gray-bg:#eef2f7; --gray-ink:#5d6f86;
  --r:16px; --shadow:0 1px 2px rgba(21,34,56,.05),0 10px 28px -14px rgba(21,34,56,.16);
  --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,"Helvetica Neue",Arial,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{font:16px/1.55 var(--font);margin:0;color:var(--ink);background:var(--bg)}
h1{font-size:30px;letter-spacing:-.015em;margin:.4em 0 .5em;line-height:1.2}
h2{font-size:22px;letter-spacing:-.01em;margin:.3em 0 .6em}
h3{font-size:17px;margin:.2em 0 .5em}
h4{font-size:15px;margin:.2em 0 .4em}
a{color:var(--brand-deep);text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{color:var(--brand)}
::selection{background:var(--brand-soft)}
:focus-visible{outline:3px solid var(--brand);outline-offset:2px;border-radius:6px}
.wrap{max-width:1060px;margin:0 auto;padding:16px}
.narrow{max-width:720px;margin:0 auto;padding:16px}
/* Safety strip — always on top, never subtle */
.safety{background:#152238;color:#fff;font-size:13.5px;padding:9px 16px;display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;text-align:center}
.demo-chip{background:#f5b942;color:#152238;font-weight:800;font-size:11.5px;letter-spacing:.08em;padding:3px 10px;border-radius:999px;flex-shrink:0}
/* Topbar */
.topbar{background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.topbar .wrap{display:flex;align-items:center;gap:12px;padding-top:10px;padding-bottom:10px}
.brand{font-weight:800;font-size:18px;letter-spacing:-.01em;display:flex;align-items:center;gap:10px}
.brand small{font-weight:500;color:var(--mut);font-size:14px}
.pill{margin-left:auto;font-size:13px;font-weight:600;padding:5px 14px;border-radius:999px;background:var(--brand-soft);color:var(--brand-ink);border:1px solid #bfe0e5;white-space:nowrap}
.pill.warn{background:var(--yellow-bg);color:var(--yellow-ink);border-color:var(--yellow-line)}
.pill.bad{background:var(--red-bg);color:var(--red-ink);border-color:var(--red-line)}
/* Layout + nav */
.layout{display:flex;gap:0;align-items:stretch;min-height:calc(100vh - 110px)}
.side{width:238px;background:var(--surface);border-right:1px solid var(--line);padding:14px 10px;flex-shrink:0}
.side a.mod{display:flex;gap:11px;align-items:center;padding:10px 12px;border-radius:12px;color:var(--ink);text-decoration:none;margin-bottom:4px;font-weight:500;font-size:15px;border:1px solid transparent}
.side a.mod:hover{background:#f4f8fb}
.side a.mod.active{background:var(--brand-soft);font-weight:700;color:var(--brand-ink);border-color:#cde9ec}
.side a.mod svg{width:20px;height:20px;flex-shrink:0;color:var(--brand-deep)}
.side a.mod.active svg{color:var(--brand-ink)}
.side .mod.locked{opacity:.6;cursor:default}
.side .mod.locked svg{color:var(--mut)}
.locktag{font-size:11px;font-weight:600;background:var(--gray-bg);color:var(--mut);border-radius:6px;padding:2px 8px;margin-left:auto;white-space:nowrap}
.main{flex:1;padding:20px;min-width:0;max-width:900px}
/* Cards, buttons, forms */
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px;margin-bottom:14px;box-shadow:var(--shadow)}
.card.tier{border-style:dashed;border-width:1.5px;background:#fbfdff}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--brand-deep);margin:0 0 6px}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--brand);color:#fff;border:0;border-radius:12px;padding:11px 20px;font:600 16px var(--font);cursor:pointer;text-decoration:none;box-shadow:0 4px 12px -4px rgba(13,125,140,.5)}
.btn:hover{background:var(--brand-deep);color:#fff}
.btn.ghost{background:var(--surface);color:var(--brand-deep);border:1.5px solid var(--brand);box-shadow:none}
.btn.ghost:hover{background:var(--brand-soft)}
.btn:disabled{opacity:.5;cursor:default;box-shadow:none}
.btn svg{width:18px;height:18px}
input,select,textarea{font:16px var(--font);color:var(--ink);width:100%;padding:11px 12px;border:1.5px solid var(--line);border-radius:12px;margin:4px 0 14px;background:#fff}
input:focus,select:focus,textarea:focus{border-color:var(--brand);outline:2px solid var(--brand-soft)}
input[type=checkbox],input[type=radio]{width:auto;margin:0 8px 0 0;accent-color:var(--brand)}
label{font-weight:600;font-size:14px;display:block}
label>span.hint, .hint{font-weight:400;color:var(--mut)}
/* Mia identity */
.mia{display:flex;gap:14px;background:linear-gradient(135deg,#e2f2f4,#f4fafb);border:1px solid #cde9ec;border-radius:var(--r);padding:16px;margin-bottom:16px;align-items:center;box-shadow:var(--shadow)}
.mia-avatar{position:relative;display:inline-block;width:var(--s,48px);height:var(--s,48px);border-radius:50%;flex-shrink:0;box-shadow:0 3px 10px rgba(10,97,109,.28)}
.mia-avatar svg.mono{width:100%;height:100%;display:block;border-radius:50%}
.mia-avatar img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:50%}
.mia-name{font-weight:800;font-size:16px}
.mia-role{font-weight:500;color:var(--brand-ink);font-size:14px}
.mia-say{color:#33475f;font-size:15px;margin-top:2px}
/* Verdict hero — decisive but calm */
.verdict-hero{display:flex;gap:16px;align-items:center;border-radius:var(--r);padding:20px;margin:6px 0 14px;border:1.5px solid;box-shadow:var(--shadow)}
.verdict-hero .v-icon{width:52px;height:52px;flex-shrink:0;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.65)}
.verdict-hero .v-icon svg{width:30px;height:30px}
.verdict-hero.v-green{background:var(--green-bg);border-color:var(--green-line);color:var(--green-ink)}
.verdict-hero.v-yellow{background:var(--yellow-bg);border-color:var(--yellow-line);color:var(--yellow-ink)}
.verdict-hero.v-red{background:var(--red-bg);border-color:var(--red-line);color:var(--red-ink)}
.verdict-hero.v-gray{background:var(--gray-bg);border-color:var(--line);color:var(--gray-ink)}
.v-word{font-size:30px;font-weight:800;letter-spacing:.04em;line-height:1.1}
.v-sub{font-size:14px;margin-top:2px;opacity:.92}
/* Flags */
.flag{border-left:4px solid var(--line);padding:10px 14px;margin:10px 0;background:#fbfdff;border-radius:0 10px 10px 0;border-top:1px solid var(--line);border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.flag.red{border-left-color:var(--red-ink);background:#fff7f6}
.flag.yellow{border-left-color:var(--yellow-line);background:#fffeF7}
.flag.info{border-left-color:#9fb2c8}
.flag b.sev{font-size:12.5px;letter-spacing:.06em}
.flag.red b.sev{color:var(--red-ink)}.flag.yellow b.sev{color:var(--yellow-ink)}.flag.info b.sev{color:var(--mut)}
.src{font-size:13px;color:var(--mut)}
.src a{color:var(--brand-deep)}
/* Wizard progress */
.wsteps{list-style:none;display:flex;gap:4px;padding:0;margin:0 0 18px;counter-reset:step}
.wsteps li{flex:1;text-align:center;font-size:12px;font-weight:600;color:var(--mut);position:relative;padding-top:26px;min-width:0}
.wsteps li::before{content:counter(step);counter-increment:step;position:absolute;top:0;left:50%;transform:translateX(-50%);width:22px;height:22px;border-radius:50%;background:var(--gray-bg);color:var(--mut);font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;border:1.5px solid var(--line)}
.wsteps li::after{content:"";position:absolute;top:11px;left:calc(-50% + 14px);right:calc(50% + 14px);height:2px;background:var(--line)}
.wsteps li:first-child::after{display:none}
.wsteps li.done{color:var(--brand-ink)}
.wsteps li.done::before{background:var(--brand);border-color:var(--brand);color:#fff}
.wsteps li.done::after{background:var(--brand)}
.wsteps li.now{color:var(--brand-ink)}
.wsteps li.now::before{background:var(--surface);border-color:var(--brand);color:var(--brand-ink);box-shadow:0 0 0 4px var(--brand-soft)}
.wsteps li span.lbl{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* Landing hero */
.hero{display:flex;gap:20px;align-items:center;margin:26px 0 20px}
.hero h1{margin:0 0 8px;font-size:34px}
.hero .lede{font-size:18px;color:#33475f;margin:0}
.howto{counter-reset:how}
.howto li{margin-bottom:12px;padding-left:4px}
/* Tables, misc */
h3 svg{width:18px;height:18px;vertical-align:-3px;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:14.5px}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.kv{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;font-size:15px}
.kv dt{color:var(--mut);font-weight:600}.kv dd{margin:0}
.divider{border:0;border-top:1px solid var(--line);margin:18px 0}
@media(max-width:760px){
  .layout{display:block}
  .side{width:100%;border-right:0;border-bottom:1px solid var(--line);display:flex;gap:6px;overflow-x:auto;padding:10px}
  .side a.mod{white-space:nowrap;margin-bottom:0;font-size:14px;padding:8px 12px}
  .side .locktag{display:none}
  .main{padding:14px;max-width:none}
  .hero{flex-direction:column;align-items:flex-start}
  .wsteps li span.lbl{display:none}
  .wsteps li{padding-top:24px}
  h1{font-size:26px}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
</style>
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def mia_avatar(size: int = 48) -> str:
    """Mia's identity mark: teal monogram with her photo layered on top.
    If the hotlinked photo fails, the monogram remains — the page never breaks."""
    return (
        f"<span class='mia-avatar' style='--s:{size}px'>"
        "<svg class='mono' viewBox='0 0 48 48' aria-hidden='true'>"
        "<defs><linearGradient id='miag' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#14a4b6'/><stop offset='1' stop-color='#0a616d'/>"
        "</linearGradient></defs>"
        "<circle cx='24' cy='24' r='24' fill='url(#miag)'/>"
        "<text x='24' y='32' text-anchor='middle' font-size='22' font-weight='700' "
        "fill='#ffffff' font-family='inherit'>M</text></svg>"
        f"<img src='{MIA_AVATAR_URL}' alt='' loading='lazy' onerror='this.remove()'>"
        "</span>"
    )


def banner() -> str:
    return (
        "<div class='safety' role='note'><span class='demo-chip'>DEMO</span>"
        "<span>Synthetic data only · Assistive reference aid — not a substitute "
        "for clinical judgment · Not for real patient use</span></div>"
    )


def mia_card(subtitle: str = "") -> str:
    return (
        "<div class='mia'>" + mia_avatar(52)
        + "<div><div class='mia-name'>Mia "
        f"<span class='mia-role'>· {esc(PRESCRIBE_MIA.role)}</span></div>"
        f"<div class='mia-say'>{esc(subtitle or PRESCRIBE_MIA.greeting)}</div>"
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
        icon = ICONS.get(m["id"], ICONS["lock"])
        if m["locked"]:
            mods.append(
                f"<a class='mod locked' aria-disabled='true'>{icon}<span>{esc(m['name'])}</span>"
                f"<span class='locktag'>Full OS</span></a>"
            )
        else:
            cls = " active" if m["id"] == active else ""
            mods.append(
                f"<a class='mod{cls}' href='{m['href']}'><span aria-hidden='true'>{icon}</span>"
                f"<span>{esc(m['name'])}</span></a>"
            )
    mods.append(
        f"<a class='mod' href='/app/upgrades'>{ICONS['up']}<span>Upgrades</span></a>"
    )
    return (
        "<!doctype html><html><head><title>Mia Dental OS</title>" + STYLE + "</head><body>"
        + banner()
        + "<div class='topbar'><div class='wrap'>"
        f"<div class='brand'>{mia_avatar(34)}Mia Dental OS <small>· {esc(clinic_name)}</small></div>{pill}"
        "</div></div>"
        f"<div class='layout'><nav class='side' aria-label='Modules'>{''.join(mods)}</nav>"
        f"<div class='main'>{body}</div></div>"
        "</body></html>"
    )


def landing_page() -> str:
    return (
        "<!doctype html><html><head><title>Mia Dental OS — Mia Dental Prescribing Copilot</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow'>"
        + "<div class='hero'>" + mia_avatar(88)
        + "<div><p class='eyebrow'>Mia Dental OS</p>"
        + "<h1>The prescribing copilot for young dentists</h1>"
        + "<p class='lede'>Hi, I'm Mia. I'll double-check every intended prescription against your patient's "
        "record before you sign — allergies, interactions, dosing. You always make the call; "
        "I just make sure nothing gets missed.</p></div></div>"
        + "<div class='card'><p class='eyebrow'>How the copilot workflow works</p><ol class='howto'>"
        "<li><b>Open the patient card</b> — allergies, conditions, current meds in one view.</li>"
        "<li><b>Answer the guided questions</b> — indication, patient factors, allergies, meds, conditions.</li>"
        "<li><b>Choose with cited references</b> — standard options for your indication, each with its source.</li>"
        "<li><b>Get a Green / Yellow / Red check</b> — every flag cites the patient record or the reference rule behind it.</li>"
        "<li><b>You decide.</b> The copilot never prescribes, transmits, or fills — it surfaces what you might have missed.</li>"
        "</ol></div>"
        + "<div class='card'><p class='eyebrow'>7-day free trial</p>"
        "<p>Full copilot access for 7 days, free. After that, "
        f"<b>${SUBSCRIPTION_PRICE_USD}/month</b>. No charges without your explicit subscription — "
        "billing is in test mode while we onboard pilot clinics.</p>"
        "<a class='btn' href='/app/start'>Start the guided demo " + ICONS["arrow"] + "</a> "
        "<a class='btn ghost' href='/invite'>Dentist sign-up</a></div>"
        + "<div class='card'><p class='eyebrow'>Scope &amp; limitations — read this</p><ul>"
        "<li>Assistive reference aid only. The dentist always decides and prescribes.</li>"
        "<li>Reference dataset " + esc(REFERENCE_VERSION) + ": standard dental prescribing references, each item source-cited. Requires dentist review before clinical use.</li>"
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
        + "<div class='card'><p class='eyebrow'>Patients</p>"
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
        + f"<div class='card'><p class='eyebrow'>Patient card</p><h2 style='margin-top:0'>{esc(p['label'])}</h2>"
        f"<h4>Allergies</h4><ul>{allergies}</ul>"
        f"<h4>Conditions</h4><ul>{conds}</ul>"
        f"<h4>Current medications</h4><ul>{meds}</ul></div>"
        + f"<p><a class='btn' href='/app/wizard/start?patient={patient_id}'>Start guided check {ICONS['arrow']}</a> "
        "<span class='src'>Walks through indication → factors → allergies → meds → conditions → your choice.</span></p>"
        + f"<div class='card'><p class='eyebrow'>Quick safety check <span class='hint'>(skip wizard)</span></p>"
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
    vicon = {"GREEN": ICONS["check"], "YELLOW": ICONS["alert"],
             "RED": ICONS["stop"]}.get(c["verdict"], ICONS["help"])
    flags = ""
    for f in c["flags"]:
        sev = f["severity"] if f["severity"] in ("red", "yellow") else "info"
        rule = f"<br><span class='src'>Rule: {esc(f['rule_id'])}</span>" if f.get("rule_id") else ""
        flags += (
            f"<div class='flag {sev}'><b class='sev'>{sev.upper()}</b> — {esc(f['reason'])}"
            f"<br><span class='src'>Source: {esc(f['source'])}</span>{rule}</div>"
        )
    intended = c["intended"]
    hero = (
        f"<div class='verdict-hero {vcls}' role='status'>"
        f"<span class='v-icon'>{vicon}</span>"
        f"<div><div class='v-word'>{esc(c['verdict'])}</div>"
        "<div class='v-sub'>Assistive reference aid — review the flags, then you decide.</div></div>"
        "</div>"
    )
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
        + f"<div class='card'><p class='eyebrow'>Safety check — {esc(intended.get('drug_name',''))}</p>"
        + hero
        + f"<p class='src'>Intended: {esc(str(intended.get('strength_mg','—')))} mg × "
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
        f"<div class='card tier'><h3>{ICONS['lock']} {esc(t['name'])}</h3><p>{esc(t['blurb'])}</p>"
        "<p class='src'>Available in the full Mia Dental OS — ask about the pilot.</p>"
        "<button class='btn' disabled>Locked</button></div>"
        for t in UPSELL_TIERS
    )
    body = (
        mia_card("The Prescribing Copilot is your wedge. Here's where Mia Dental OS goes next.")
        + "<p class='eyebrow'>Upgrades</p>" + tiers
        + "<div class='card'><h3>Also in the full OS</h3><ul>"
        f"<li>{esc('Patient Intake')} — locked teaser</li>"
        f"<li>{esc('Dentist Dashboard')} — locked teaser</li>"
        f"<li>{esc('Recall & Follow-up')} — locked teaser</li>"
        f"<li>{esc('Command Center')} — locked teaser</li></ul>"
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
        + "<div class='card'><p class='eyebrow'>Guided first run</p><ol class='howto'>"
        "<li><b>Trial active</b> <span class='pill' style='margin:0'>You're inside the 7-day free trial</span></li>"
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


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Mia Dental OS demo → http://127.0.0.1:{PORT}/  (synthetic data only)")
    server.serve_forever()


if __name__ == "__main__":
    main()


def _wizard_or_404(token: str):
    state = WIZARDS.get(token)
    return state


def _select(name: str, options: list[str], current: str) -> str:
    opts = "".join(
        f"<option value='{esc(o)}'{' selected' if o == current else ''}>{esc(o)}</option>"
        for o in options
    )
    return f"<select name='{name}'><option value=''>— choose —</option>{opts}</select>"


WIZ_STEP_LABELS = {
    "indication": "Indication", "factors": "Factors", "allergies": "Allergies",
    "medications": "Meds", "conditions": "Conditions",
    "summary": "Summary", "choose": "Choice",
}


def wizard_progress(current: str) -> str:
    """7-step progress rail. Done / current / upcoming states."""
    items = []
    seen_current = False
    for s in STEPS:
        if s == current:
            cls, seen_current = "now", True
        elif not seen_current:
            cls = "done"
        else:
            cls = ""
        items.append(
            f"<li class='{cls}'><span class='lbl'>{WIZ_STEP_LABELS.get(s, s)}</span></li>"
        )
    return f"<ol class='wsteps' aria-label='Check progress'>{''.join(items)}</ol>"


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
        + wizard_progress(step)
        + f"<div class='card'><form method='POST' action='/api/wizard/{token}/{step}'>"
        + inner
        + f"<button class='btn' type='submit'>Continue {ICONS['arrow']}</button></form></div>"
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
        f"<div class='flag info'><b class='sev'>INFO</b> — {esc(m['reason'])}<br><span class='src'>Source: {esc(m['source'])}</span></div>"
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
        + wizard_progress("summary")
        + f"<div class='card'><p class='eyebrow'>Step 6 of 7 — Summary</p>"
        f"<table><tr><th>Item</th><th>Answer</th><th></th></tr>{table}</table></div>"
        + (f"<p class='eyebrow'>Missing information</p>{mflags}" if mflags else "<p>No missing-info flags.</p>")
        + f"<p><a class='btn' href='/app/wizard/{token}/choose'>Continue to prescription choice {ICONS['arrow']}</a></p>"
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
        + wizard_progress("choose")
        + f"<div class='card'>{panel}</div>"
        + f"<div class='card'><p class='eyebrow'>Step 7 of 7 — Your prescription choice</p>"
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
