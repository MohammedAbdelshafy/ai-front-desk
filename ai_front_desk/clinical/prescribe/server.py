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
from urllib.parse import urlparse, parse_qs, quote

from ..mia_shell import CharacterManifest
from . import REFERENCE_DISCLAIMER, REFERENCE_VERSION
from .accounts import (
    AccountStore,
    DEMO_ACCOUNT_ID,
    DEMO_SESSION_TTL_SECONDS,
    SESSION_TTL_SECONDS,
    verify_password,
)
from .billing import provider as billing_provider, TEST_MODE, NETELLER_EMAIL
from .checker import check_prescription
from .reference_data import DRUGS, REFERENCE_DATE, SOURCES, GENERAL_SOURCES
from .store import PrescribeStore, TenantMismatchError
from .trial import SUBSCRIPTION_PRICE_USD

BASE = Path(__file__).resolve().parent
DB_PATH = Path(
    os.environ.get(
        "PRESCRIBE_DB",
        str(Path.home() / ".mia-prescribe" / "prescribe-demo.sqlite3"),
    )
)
PORT = int(os.environ.get("PRESCRIBE_PORT", "8767"))
MAX_BODY = 64 * 1024
SESSION_COOKIE = "mia_session"

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

# ---------------------------------------------------------------- legal ---

LEGAL_VERSION = "0.1"
LEGAL_DIR = Path(__file__).resolve().parents[3] / "docs" / "legal"
LEGAL_DOCS = {
    "privacy": ("Privacy Policy", "privacy-policy.md"),
    "terms": ("Terms of Service", "terms-of-service.md"),
    "security": ("Security Policy", "security-policy.md"),
    "intended-use": ("Intended Use & Clinical Limitations", "intended-use-clinical-limitations.md"),
    "refund": ("Refund & Cancellation Policy", "refund-cancellation.md"),
    "retention": ("Data Retention & Deletion", "data-retention-deletion.md"),
}
# Public short routes; everything else lives under /legal/<slug>.
LEGAL_ROUTES = {"/privacy": "privacy", "/terms": "terms", "/security": "security"}


def _md_inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", text)
    return text


def _md_table(rows: list) -> str:
    def cells(r):
        return [c.strip() for c in r.strip().strip("|").split("|")]
    out = ["<table class='legal-table'><thead><tr>"]
    out += ["<th>" + _md_inline(c) + "</th>" for c in cells(rows[0])]
    out.append("</tr></thead><tbody>")
    for r in rows[2:]:
        out.append("<tr>" + "".join("<td>" + _md_inline(c) + "</td>" for c in cells(r)) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def md_to_html(md: str) -> str:
    """Minimal markdown -> HTML for our own legal docs (headers, quotes, lists, tables)."""
    out: list = []
    lines = md.split("\n")
    i, in_list = 0, False
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|?$", lines[i + 1].strip()):
            if in_list:
                out.append("</ul>")
                in_list = False
            rows = [s]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(lines[j].strip())
                j += 1
            out.append(_md_table(rows))
            i = j
            continue
        if s.startswith(">"):
            if in_list:
                out.append("</ul>")
                in_list = False
            qs = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                qs.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<div class='flag info'><b>DRAFT NOTICE</b> — " + " ".join(_md_inline(q) for q in qs) + "</div>")
            continue
        if s.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<h2>" + _md_inline(s[3:]) + "</h2>")
        elif s.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<h1>" + _md_inline(s[2:]) + "</h1>")
        elif s.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + _md_inline(s[2:]) + "</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<p>" + _md_inline(s) + "</p>")
        i += 1
    if in_list:
        out.append("</ul>")
    return "".join(out)


def legal_footer() -> str:
    return (
        "<footer class='legal-foot'><div class='wrap'>"
        "<a href='/legal'>Legal</a> \u00b7 <a href='/privacy'>Privacy</a> \u00b7 "
        "<a href='/terms'>Terms</a> \u00b7 <a href='/security'>Security</a>"
        "<span class='src'> \u00b7 Mia Dental OS \u2014 demo, not for real patient use</span>"
        "</div></footer>"
    )


def legal_index_page() -> str:
    items = "".join(
        "<li><a href='/legal/" + slug + "'>" + esc(title) + "</a></li>"
        for slug, (title, _fn) in LEGAL_DOCS.items()
    )
    body = (
        "<div class='narrow'><p class='eyebrow'>Legal</p>"
        "<h1>Legal &amp; compliance</h1>"
        "<p class='src'>Draft documents (v" + esc(LEGAL_VERSION) + ") \u2014 they require qualified legal review "
        "before production use or real patient data. Nothing here is legal advice.</p>"
        "<div class='card'><ul>" + items + "</ul></div>"
        "</div>" + legal_footer()
    )
    return ("<!doctype html><html><head><title>Legal \u2014 Mia Dental OS</title>"
            + STYLE + "</head><body>" + banner() + body + "</body></html>")


def legal_doc_page(slug: str):
    if slug not in LEGAL_DOCS:
        return None
    title, filename = LEGAL_DOCS[slug]
    path = LEGAL_DIR / filename
    if not path.exists():
        return None
    md = path.read_text(encoding="utf-8")
    body = (
        "<div class='narrow legal-doc'><p class='eyebrow'><a href='/legal'>Legal</a></p>"
        + md_to_html(md)
        + "</div>" + legal_footer()
    )
    return ("<!doctype html><html><head><title>" + esc(title) + " \u2014 Mia Dental OS</title>"
            + STYLE + "</head><body>" + banner() + body + "</body></html>")


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
.acct-chip{display:inline-flex;align-items:center;gap:8px;margin-left:auto;font-size:13.5px;font-weight:600;color:var(--ink);background:#f4f8fb;border:1px solid var(--line);border-radius:999px;padding:4px 8px 4px 12px;white-space:nowrap}
.acct-chip svg{width:17px;height:17px;color:var(--brand-deep)}
.acct-chip a{font-size:12.5px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:3px 10px;text-decoration:none}
.acct-chip + .pill{margin-left:0}
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
.legal-foot{border-top:1px solid var(--line);margin-top:32px;padding:14px 0;color:var(--mut);font-size:13px}
.legal-foot a{color:var(--mut);text-decoration:none;margin-right:4px}
.legal-foot a:hover{color:var(--brand);text-decoration:underline}
.legal-doc h1{margin-top:8px}
.legal-doc h2{margin-top:26px}
.legal-doc .flag.info{margin:0 0 18px}
table.legal-table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}
table.legal-table th,table.legal-table td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
table.legal-table th{background:var(--brand2)}
label.check{display:flex;gap:10px;align-items:flex-start;font-weight:400;font-size:14px;margin:0 0 10px;cursor:pointer}
label.check input{width:18px;height:18px;margin-top:2px;flex-shrink:0;accent-color:var(--brand)}
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


def shell(active: str, clinic_name: str, trial: dict, body: str, ctx: dict | None = None) -> str:
    state = trial["state"]
    if trial.get("is_demo"):
        pill = "<span class='pill'>Explore demo</span>"
    elif state in ("active", "expiring"):
        pill = f"<span class='pill{' warn' if state == 'expiring' else ''}'>Trial: {trial['days_remaining']:.1f} days left</span>"
    elif state == "subscribed":
        pill = "<span class='pill'>Subscribed</span>"
    else:
        pill = "<span class='pill bad'>Trial expired</span>"
    if ctx is None:
        acct = ""
    elif ctx.get("is_demo"):
        acct = (
            "<span class='acct-chip'>" + ICONS["user"]
            + "<span>Demo Explorer</span>"
            + "<a href='/signup'>Save my work — sign up</a></span>"
        )
    else:
        acct = (
            "<span class='acct-chip'>" + ICONS["user"]
            + f"<span>{esc(ctx['name'])} · {esc(ctx['clinic_name'])}</span>"
            + "<a href='/signout'>Sign out</a></span>"
        )
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
        f"<div class='brand'>{mia_avatar(34)}Mia Dental OS <small>· {esc(clinic_name)}</small></div>{acct}{pill}"
        "</div></div>"
        f"<div class='layout'><nav class='side' aria-label='Modules'>{''.join(mods)}</nav>"
        f"<div class='main'>{body}</div></div>"
        + legal_footer()
        + "</body></html>"
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
        "<p>Full copilot access for 7 days, free — trial starts when you create your account. After that, "
        f"<b>${SUBSCRIPTION_PRICE_USD}/month</b>. No charges without your explicit subscription — "
        "billing is in test mode while we onboard pilot clinics.</p>"
        "<a class='btn' href='/demo'>Explore the demo — no sign-up " + ICONS["arrow"] + "</a> "
        "<a class='btn ghost' href='/signup'>Create account — free trial</a>"
        "<p class='src' style='margin-top:10px'>Already have an account? <a href='/signin'>Sign in</a> · "
        "A dentist? <a href='/invite'>Request a pilot invite</a></p></div>"
        + "<div class='card'><p class='eyebrow'>Scope &amp; limitations — read this</p><ul>"
        "<li>Assistive reference aid only. The dentist always decides and prescribes.</li>"
        "<li>Reference dataset " + esc(REFERENCE_VERSION) + ": standard dental prescribing references, each item source-cited. Requires dentist review before clinical use.</li>"
        "<li>Missing or uncertain patient data is never shown as verified-safe.</li>"
        "<li>Synthetic demo data only in this preview. Not HIPAA-compliant. Not for real patients.</li>"
        "</ul></div>"
        + "</div>" + legal_footer() + "</body></html>"
    )


# ---------------------------------------------------------------- pages ---

# ---------------------------------------------------------------- auth ---

def _auth_card(title: str, inner: str, switch: str) -> str:
    return (
        "<!doctype html><html><head><title>" + esc(title) + " — Mia Dental OS</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow' style='max-width:480px'>"
        + "<div style='text-align:center;margin:26px 0 6px'>" + mia_avatar(64) + "</div>"
        + "<div class='card'>" + inner + switch + "</div>"
        + "</div>" + legal_footer() + "</body></html>"
    )


def _field_errors(errors: list[str]) -> str:
    if not errors:
        return ""
    items = "".join(f"<li>{esc(e)}</li>" for e in errors)
    return (
        "<div class='flag red' role='alert' style='margin:0 0 14px'>"
        f"<b class='sev'>PLEASE CHECK</b><ul style='margin:6px 0 0;padding-left:18px'>{items}</ul></div>"
    )


def signup_page(errors: list[str] | None = None, values: dict | None = None) -> str:
    v = values or {}
    inner = (
        _field_errors(errors or [])
        + "<p class='eyebrow'>Create your account</p>"
        + "<h2 style='margin-top:0'>Start your 7-day free trial</h2>"
        + "<p class='src'>Full Prescribing Copilot access for 7 days from sign-up. "
        f"Then <b>${SUBSCRIPTION_PRICE_USD}/month</b> — no charges without your explicit subscription.</p>"
        + "<form method='POST' action='/api/signup' id='signup-form'>"
        f"<label>Full name<input name='name' required maxlength='80' placeholder='Dr. Jane Rivera' value='{esc(v.get('name', ''))}'></label>"
        f"<label>Work email<input name='email' type='email' required maxlength='254' placeholder='jane@riveradental.com' value='{esc(v.get('email', ''))}'></label>"
        f"<label>Clinic name<input name='clinic_name' required maxlength='80' placeholder='Rivera Dental' value='{esc(v.get('clinic_name', ''))}'></label>"
        "<label>Password <span class='hint'>(10+ characters — a phrase works great)</span>"
        "<input name='password' type='password' required minlength='10' autocomplete='new-password' id='pw'></label>"
        "<div class='src' id='pw-hint' aria-live='polite' style='margin:-8px 0 12px'></div>"
        "<label>Confirm password<input name='confirm' type='password' required autocomplete='new-password'></label>"
        "<label class='check'><input type='checkbox' name='accept_terms' value='1' required>"
        "<span>I agree to the <a href='/terms' target='_blank' rel='noopener'>Terms of Service</a> (draft v" + esc(LEGAL_VERSION) + ")</span></label>"
        "<label class='check'><input type='checkbox' name='accept_privacy' value='1' required>"
        "<span>I have read the <a href='/privacy' target='_blank' rel='noopener'>Privacy Policy</a> (draft v" + esc(LEGAL_VERSION) + ")</span></label>"
        "<button class='btn' type='submit' style='width:100%;justify-content:center'>Create account &amp; start trial</button>"
        "</form>"
        + _pw_strength_js()
    )
    switch = (
        "<p class='src' style='text-align:center'>Already have an account? "
        "<a href='/signin'>Sign in</a></p>"
    )
    return _auth_card("Sign up", inner, switch)


def _pw_strength_js() -> str:
    return """<script>
(function(){
  var pw=document.getElementById('pw'), hint=document.getElementById('pw-hint');
  if(!pw||!hint) return;
  pw.addEventListener('input', function(){
    var v=pw.value, score=0;
    if(v.length>=10) score++;
    if(v.length>=14) score++;
    if(/[A-Z]/.test(v)&&/[a-z]/.test(v)) score++;
    if(/[0-9]/.test(v)||/[^A-Za-z0-9]/.test(v)) score++;
    var label=['Too short','Weak','Okay','Good','Strong'][score];
    var color=['#b42318','#b42318','#7c5200','#0d7d8c','#166534'][score];
    hint.innerHTML='Strength: <b style="color:'+color+'">'+label+'</b>';
  });
})();
</script>"""


def signin_page(errors: list[str] | None = None, email: str = "", next_url: str = "") -> str:
    inner = (
        _field_errors(errors or [])
        + "<p class='eyebrow'>Welcome back</p>"
        + "<h2 style='margin-top:0'>Sign in</h2>"
        + "<form method='POST' action='/api/signin'>"
        f"<label>Email<input name='email' type='email' required placeholder='jane@riveradental.com' value='{esc(email)}'></label>"
        "<label>Password<input name='password' type='password' required autocomplete='current-password'></label>"
        + (f"<input type='hidden' name='next' value='{esc(next_url)}'>" if next_url else "")
        + "<button class='btn' type='submit' style='width:100%;justify-content:center'>Sign in</button>"
        "</form>"
    )
    switch = (
        "<p class='src' style='text-align:center'>New here? "
        "<a href='/signup'>Create an account — 7-day free trial</a></p>"
    )
    return _auth_card("Sign in", inner, switch)


def welcome_page(ctx: dict) -> str:
    trial = ctx["trial"]
    days = trial["days_remaining"]
    body = (
        mia_card(f"Welcome, {ctx['name']} — your 7-day free trial is active.")
        + "<div class='card'><p class='eyebrow'>You're in</p>"
        f"<p>Your trial runs until <b>{esc(_trial_end_str(ctx))}</b> "
        f"({days:.1f} days left). Full Prescribing Copilot access — nothing is charged without your say-so.</p>"
        "<p><b>First, see Mia work — 60 seconds:</b></p><ol class='howto'>"
        "<li><b>Load a sample patient</b> — synthetic record with a penicillin allergy and warfarin on board."
        "<form method='POST' action='/api/sample-patient' style='margin-top:8px'>"
        "<button class='btn ghost' type='submit'>Load sample patient</button></form></li>"
        "<li><b>Start a guided check</b> — Mia walks through indication → factors → allergies → meds → conditions → your choice."
        "<p style='margin-top:8px'><a class='btn ghost' href='/app/wizard/start'>Start guided check</a></p></li>"
        "</ol>"
        "<p><a class='btn' href='/app/patients'>Open the copilot " + ICONS["arrow"] + "</a></p></div>"
    )
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def _trial_end_str(ctx: dict) -> str:
    import datetime
    acct = get_accounts().get_account(ctx["account_id"])
    if not acct:
        return "—"
    end = acct["trial_activated_at"] + (acct["trial_days"] or 7) * 86400
    return datetime.datetime.fromtimestamp(end).strftime("%Y-%m-%d")


def subscribe_page(trial: dict, ctx: dict | None = None) -> str:
    state = trial["state"]
    price = trial["price_usd"]
    if state == "subscribed":
        headline = "You're subscribed"
        body = (
            "<p>The copilot module is unlocked. Cancel anytime — your records stay preserved.</p>"
            "<form method='POST' action='/api/billing/cancel'>"
            "<button class='btn ghost' type='submit'>Cancel subscription</button></form>"
        )
    elif state == "pending":
        headline = "Payment received — activating your account"
        body = (
            "<p>Thanks — we've got your Neteller payment on record. "
            "The founder activates accounts personally, usually within a day. "
            "You'll have full access as soon as it's confirmed.</p>"
            "<p class='src'>Nothing is charged automatically. "
            "Questions? Contact abdelshafyclapps@gmail.com.</p>"
        )
    else:
        headline = "Your trial has expired" if state == "expired" else "Subscription"
        body = (
            "<p>The copilot module is now locked. <b>Your patient records and check history are preserved</b> — "
            "nothing was deleted.</p>"
            "<div class='card'><h3>Subscribe — Mia Dental OS Prescribing Copilot</h3>"
            f"<p><b>${price}/month</b>, cancel anytime. No automatic charges, ever.</p>"
            "<ol>"
            f"<li>Send <b>${price}</b> via <b>Neteller</b> to <b>{esc(NETELLER_EMAIL)}</b></li>"
            "<li>Click the button below so we know to activate you</li>"
            "<li>We confirm your payment and unlock your account</li>"
            "</ol>"
            "<form method='POST' action='/api/billing/paid'>"
            "<button class='btn' type='submit'>I've completed my Neteller payment</button></form>"
            "<p class='src'>Manual billing — a human reviews every payment before activation. "
            "No card details are entered or stored here.</p>"
            "</div>"
        )
    return (
        "<!doctype html><html><head><title>Subscribe — Mia Dental OS</title>"
        + STYLE + "</head><body>" + banner()
        + "<div class='narrow'>" + mia_card()
        + f"<h1>{headline}</h1>"
        + body
        + ("<p><a href='/app/start'>← Back to the app</a></p>" if ctx else "")
        + "</div></body></html>"
    )


def patients_page(store, ctx: dict) -> str:
    trial = ctx["trial"]
    clinic_id = ctx["clinic_id"]
    px = ctx["prefix"]
    patients = store.list_patients(clinic_id)
    rows = "".join(
        f"<tr><td><a href='{px}/patient?id={p['patient_id']}'>{esc(p['label'])}</a></td>"
        f"<td>{len(p['allergies'])}</td><td>{len(p['current_meds'])}</td></tr>"
        for p in patients
    ) or "<tr><td colspan=3 style='color:var(--mut)'>No patients yet — add one below, or run the guided demo.</td></tr>"
    body = (
        mia_card("Pick a patient to open their card, or run a safety check.")
        + "<div class='card'><p class='eyebrow'>Patients</p>"
        f"<table><tr><th>Patient</th><th>Allergies</th><th>Meds</th></tr>{rows}</table></div>"
        + "<div class='card'><h3>Add patient (synthetic demo data)</h3>"
        f"<form method='POST' action='/api/patient'>"
        "<label>Label (must start with Demo/Test/Sample)<input name='label' value='Demo Patient ' required></label>"
        "<label>Allergies — one per line: substance | reaction<input name='allergies' placeholder='penicillin | rash'></label>"
        "<label><input type='checkbox' name='no_known_allergies' value='1' style='width:auto'> No known allergies (explicit)</label>"
        "<label>Conditions — comma separated<input name='conditions' placeholder='hypertension'></label>"
        "<label>Current meds — one per line: name | dose<input name='meds' placeholder='warfarin | 5 mg daily'></label>"
        "<label>Reports alcohol use <input type='checkbox' name='alcohol_use' value='1' style='width:auto'></label>"
        "<button class='btn' type='submit'>Add patient</button></form></div>"
    )
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def patient_detail_page(store, ctx: dict, patient_id: str) -> str:
    trial = ctx["trial"]
    clinic_id = ctx["clinic_id"]
    px = ctx["prefix"]
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
        f"<tr><td><a href='{px}/check?id={h['check_id']}'>{h['verdict']}</a></td>"
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
        + f"<p><a class='btn' href='{px}/wizard/start?patient={patient_id}'>Start guided check {ICONS['arrow']}</a> "
        "<span class='src'>Walks through indication → factors → allergies → meds → conditions → your choice.</span></p>"
        + f"<div class='card'><p class='eyebrow'>Quick safety check <span class='hint'>(skip wizard)</span></p>"
        f"<form method='POST' action='/api/check'>"
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
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def check_result_page(store, ctx: dict, check_id: str) -> str:
    trial = ctx["trial"]
    clinic_id = ctx["clinic_id"]
    px = ctx["prefix"]
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
        + "</p><form method='POST' action='/api/review'>"
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
        + f"<p><a href='{px}/patient?id={c['patient_id']}'>← Back to patient card</a></p>"
    )
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def reference_page(ctx: dict) -> str:
    trial = ctx["trial"]
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
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def upgrades_page(ctx: dict) -> str:
    trial = ctx["trial"]
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
    return shell("", ctx["clinic_name"], trial, body, ctx)


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


def start_page(store, ctx: dict) -> str:
    trial = ctx["trial"]
    if ctx.get("is_demo"):
        first = (
            "<li><b>You're exploring the demo</b> — synthetic data, nothing is saved to a real account. "
            "<span class='pill' style='margin:0'>Demo mode</span><br>"
            "<span class='src'>Like what you see? <a href='/signup'>Create an account</a> to keep your work.</span></li>"
        )
    else:
        first = (
            "<li><b>Trial active</b> <span class='pill' style='margin:0'>"
            f"{trial['days_remaining']:.1f} days left</span></li>"
        )
    body = (
        mia_card("60 seconds to get it. Three steps — sample patient, sample check, your own checks.")
        + "<div class='card'><p class='eyebrow'>Guided first run</p><ol class='howto'>"
        + first
        + "<li><b>Load a sample patient</b> — synthetic record with a penicillin allergy and warfarin on board."
        f"<form method='POST' action='/api/sample-patient' style='margin-top:8px'>"
        "<button class='btn ghost' type='submit'>Load sample patient</button></form></li>"
        "<li><b>Run the sample check</b> — ibuprofen 400 mg three times daily. Watch Mia flag it."
        f"<form method='POST' action='/api/sample-check' style='margin-top:8px'>"
        "<button class='btn ghost' type='submit'>Run sample check</button></form></li>"
        "</ol>"
        f"<p><a class='btn' href='{ctx['prefix']}/patients'>Or explore patients →</a></p></div>"
    )
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


# ------------------------------------------------------------- handler ---

STORE: PrescribeStore | None = None
ACCOUNTS: AccountStore | None = None


def get_store() -> PrescribeStore:
    global STORE
    if STORE is None:
        STORE = PrescribeStore(DB_PATH)
    return STORE


def get_accounts() -> AccountStore:
    global ACCOUNTS
    if ACCOUNTS is None:
        ACCOUNTS = AccountStore(DB_PATH)
    return ACCOUNTS


def _security_headers(handler) -> None:
    """Defense-in-depth headers on every response (inner + outer)."""
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
    handler.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # No JavaScript anywhere in the app; inline <style> blocks are used.
    # Images: self + https (Mia's avatar hotlinks from the assets repo).
    handler.send_header(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; "
        "img-src 'self' https: data:; font-src 'self' https:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; "
        "form-action 'self'",
    )


def _send(handler, code: int, body: str, content_type="text/html; charset=utf-8"):
    data = body.encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    _security_headers(handler)
    handler.end_headers()
    handler.wfile.write(data)


def _json(handler, code: int, obj: dict):
    data = json.dumps(obj).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    _security_headers(handler)
    handler.end_headers()
    handler.wfile.write(data)


def _redirect(handler, location: str):
    handler.send_response(303)
    handler.send_header("Location", location)
    _security_headers(handler)
    handler.end_headers()


def _cookie_flags() -> str:
    # Behind a TLS reverse proxy, set PRESCRIBE_SECURE_COOKIES=1 so the
    # session cookie is never sent over plaintext.
    secure = "; Secure" if os.environ.get("PRESCRIBE_SECURE_COOKIES") == "1" else ""
    return f"HttpOnly; SameSite=Lax; Path=/;{secure}"


def _set_session_cookie(handler, token: str, max_age: int = SESSION_TTL_SECONDS):
    handler.send_response(303)
    handler.send_header(
        "Set-Cookie",
        f"{SESSION_COOKIE}={token}; {_cookie_flags()}; Max-Age={max_age}",
    )
    _security_headers(handler)


def _redirect_with_cookie(handler, location: str, token: str,
                          max_age: int = SESSION_TTL_SECONDS):
    _set_session_cookie(handler, token, max_age)
    handler.send_header("Location", location)
    _security_headers(handler)
    handler.end_headers()


def _clear_session_cookie(handler, location: str = "/"):
    handler.send_response(303)
    handler.send_header(
        "Set-Cookie", f"{SESSION_COOKIE}=; {_cookie_flags()}; Max-Age=0"
    )
    handler.send_header("Location", location)
    _security_headers(handler)
    handler.end_headers()


# --- request hardening -------------------------------------------------
# Maximum lengths for free-text fields (DoS/bloat protection).
MAX_FIELD_LEN = 500
MAX_TEXTAREA_LEN = 4000


def _field(form: dict, key: str, max_len: int = MAX_FIELD_LEN) -> str:
    """Trimmed form field, hard-capped in length."""
    return (form.get(key, "") or "")[:max_len].strip()


def _cookie_token(handler) -> str | None:
    raw = handler.headers.get("Cookie") or ""
    for part in raw.split(";"):
        name, _, value = part.strip().partition("=")
        if name.strip() == SESSION_COOKIE and value.strip():
            return value.strip()
    return None


def _auth_ctx(handler) -> dict | None:
    """Auth context from the session cookie, or None. Sliding refresh inside."""
    token = _cookie_token(handler)
    if not token:
        return None
    ctx = get_accounts().session_ctx(token)
    if ctx is None:
        return None
    ctx["prefix"] = "/demo" if ctx["is_demo"] else "/app"
    return ctx


def _safe_next(value: str) -> str:
    v = (value or "").strip()
    if v.startswith("/") and not v.startswith("//"):
        return v
    return ""


def _require_page(handler, path: str, *, allow_demo: bool = True) -> dict | None:
    """Gate for /app/* and /demo/* pages. Redirects to signin/demo on failure."""
    ctx = _auth_ctx(handler)
    if ctx is None:
        if path.startswith("/demo/"):
            _redirect(handler, "/demo")
        else:
            _redirect(handler, "/signin?next=" + quote(path, safe=""))
        return None
    if not allow_demo and ctx["is_demo"]:
        _redirect(handler, "/demo/start")
        return None
    if not ctx["unlocked"]:
        _redirect(handler, "/subscribe")
        return None
    handler._ctx = ctx  # for the audit trail in the except block
    return ctx


def _require_api(handler) -> dict | None:
    """Gate for /api/* app routes. JSON errors, never redirects."""
    ctx = _auth_ctx(handler)
    if ctx is None:
        _json(handler, 401, {"code": "unauthorized",
                             "message": "Sign in required."})
        return None
    if not ctx["unlocked"]:
        _json(handler, 402, {"code": "subscription_required",
                             "message": "Trial expired — subscribe to continue."})
        return None
    handler._ctx = ctx
    return ctx


def _demo_enter(handler):
    """Start an explore-demo session (no sign-up): clearly labeled synthetic demo."""
    accounts = get_accounts()
    accounts.ensure_demo_account()
    token = accounts.create_session(DEMO_ACCOUNT_ID, DEMO_SESSION_TTL_SECONDS)
    _redirect_with_cookie(handler, "/demo/start", token, DEMO_SESSION_TTL_SECONDS)


def _audit_denied(handler, target: str, detail: str):
    ctx = getattr(handler, "_ctx", None)
    clinic = ctx["clinic_id"] if ctx else "unknown"
    actor = ctx["email"] if ctx else "anonymous"
    try:
        get_store()._audit(clinic, actor, "access_denied", target, detail)
        get_store()._db.commit()
    except Exception:
        pass


def _valid_id(value: str) -> bool:
    return bool(ID_RE.match(value or ""))


def _audit_auth(action: str, email: str, detail: str = "") -> None:
    """Best-effort audit of auth/billing events (never breaks the request)."""
    try:
        store = get_store()
        store._audit("auth", email.lower(), action, "account", detail[:500])
        store._db.commit()
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    server_version = "MiaDentalOS/1.0"

    def log_message(self, *args):  # quiet
        pass

    # -- GET ------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        path = url.path
        try:
            # ---- public pages ----
            if path == "/":
                _send(self, 200, landing_page())
                return
            if path == "/signup":
                if _auth_ctx(self) is not None:
                    _redirect(self, "/app/start")
                    return
                _send(self, 200, signup_page())
                return
            if path == "/signin":
                if _auth_ctx(self) is not None:
                    _redirect(self, "/app/start")
                    return
                _send(self, 200, signin_page(next_url=_safe_next(q.get("next", [""])[0])))
                return
            if path == "/signout":
                ctx = _auth_ctx(self)
                if ctx and not ctx.get("is_demo"):
                    _audit_auth("signout", ctx.get("email", ""))
                get_accounts().destroy_session(_cookie_token(self))
                _clear_session_cookie(self, "/")
                return
            if path == "/invite":
                _send(self, 200, invite_page())
                return
            if path == "/welcome":
                ctx = _require_page(self, path, allow_demo=False)
                if ctx is None:
                    return
                _send(self, 200, welcome_page(ctx))
                return
            if path == "/subscribe":
                ctx = _auth_ctx(self)
                if ctx is None:
                    _redirect(self, "/signin?next=" + quote(path, safe=""))
                    return
                _send(self, 200, subscribe_page(ctx["trial"], ctx))
                return
            # ---- legal (public) ----
            if path == "/legal":
                _send(self, 200, legal_index_page())
                return
            if path in LEGAL_ROUTES:
                page = legal_doc_page(LEGAL_ROUTES[path])
                if page is None:
                    _send(self, 404, "not found")
                else:
                    _send(self, 200, page)
                return
            if path.startswith("/legal/"):
                slug = path[len("/legal/"):]
                page = legal_doc_page(slug)
                if page is None:
                    _send(self, 404, "not found")
                else:
                    _send(self, 200, page)
                return
            # ---- explore demo (no sign-up; synthetic data, separate namespace) ----
            if path == "/demo":
                _demo_enter(self)
                return
            if path == "/demo/" or path.startswith("/demo/"):
                self._app_get("/app" + path[len("/demo"):], q)
                return
            # ---- authenticated app ----
            if path == "/app/" or path.startswith("/app/"):
                self._app_get(path, q)
                return
            _send(self, 404, "not found")
        except (KeyError, TenantMismatchError) as e:
            if isinstance(e, TenantMismatchError):
                _audit_denied(self, self.path, str(e))
                _send(self, 403, esc(str(e)))
            else:
                _send(self, 404, esc(str(e)))

    def _app_get(self, app_path: str, q: dict):
        """Route table shared by /app/* (accounts) and /demo/* (demo ctx)."""
        ctx = _require_page(self, app_path)
        if ctx is None:
            return
        store = get_store()
        clinic = ctx["clinic_id"]
        if app_path == "/app/start":
            _send(self, 200, start_page(store, ctx))
        elif app_path == "/app/patients":
            _send(self, 200, patients_page(store, ctx))
        elif app_path == "/app/patient":
            pid = q.get("id", [""])[0]
            if not _valid_id(pid):
                _send(self, 400, "bad patient id")
                return
            _send(self, 200, patient_detail_page(store, ctx, pid))
        elif app_path == "/app/check":
            cid = q.get("id", [""])[0]
            if not _valid_id(cid):
                _send(self, 400, "bad check id")
                return
            _send(self, 200, check_result_page(store, ctx, cid))
        elif app_path == "/app/reference":
            _send(self, 200, reference_page(ctx))
        elif app_path == "/app/upgrades":
            _send(self, 200, upgrades_page(ctx))
        elif app_path == "/app/wizard/start":
            pid = q.get("patient", [""])[0]
            patient = None
            if pid:
                if not _valid_id(pid):
                    _send(self, 400, "bad patient id")
                    return
                patient = store.get_patient(clinic, pid)
            state = WIZARDS.create(clinic, patient)
            _redirect(self, f"{ctx['prefix']}/wizard/{state['token']}/{STEPS[0]}")
        elif app_path.startswith("/app/wizard/"):
            m = re.match(r"/app/wizard/(wz_[a-f0-9]{12})/([a-z]+)\Z", app_path)
            if not m:
                _send(self, 404, "not found")
                return
            state = _wizard_or_404(m.group(1))
            if state is None:
                _send(self, 404, "wizard session expired")
                return
            if state.get("clinic_id") != clinic:
                _audit_denied(self, m.group(1), "cross-account wizard access denied")
                _send(self, 403, "cross-account wizard access denied")
                return
            step = m.group(2)
            if step == "summary":
                _send(self, 200, wizard_summary_page(state, ctx))
            elif step == "choose":
                _send(self, 200, wizard_choose_page(state, ctx))
            elif step in STEPS:
                _send(self, 200, wizard_step_page(state, step, ctx))
            else:
                _send(self, 404, "not found")
        else:
            _send(self, 404, "not found")

    # -- POST -----------------------------------------------------
    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        # Read the request body ONCE (a second rfile read would block forever).
        length = int(self.headers.get("Content-Length", 0) or 0)
        _raw = self.rfile.read(min(length, MAX_BODY)).decode("utf-8", errors="replace")
        _parsed = parse_qs(_raw)
        # Hard-cap every incoming field (DoS/bloat protection) and bound the
        # number of fields. No legitimate field needs more than this.
        form = {k[:128]: v[0][:MAX_TEXTAREA_LEN] for k, v in list(_parsed.items())[:200]}
        form_multi = {k[:128]: [x[:MAX_TEXTAREA_LEN] for x in v] for k, v in list(_parsed.items())[:200]}
        try:
            # ---- public auth endpoints (form posts -> page re-render on error) ----
            if path == "/api/signup":
                return self._handle_signup(form)
            if path == "/api/signin":
                return self._handle_signin(form)
            if path == "/api/invite":
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
                return
            # ---- billing (session required) ----
            if path == "/api/billing/paid":
                # Dentist clicked "I've completed my Neteller payment".
                ctx = _auth_ctx(self)
                if ctx is None:
                    _json(self, 401, {"code": "unauthorized",
                                      "message": "Sign in required."})
                    return
                if ctx["is_demo"]:
                    _redirect(self, "/signup")
                    return
                get_accounts().mark_payment_pending(ctx["account_id"])
                _audit_auth("payment_pending_neteller", ctx.get("email", ""),
                            f"${SUBSCRIPTION_PRICE_USD}/mo via {NETELLER_EMAIL}")
                _redirect(self, "/subscribe")
                return
            if path == "/api/billing/cancel":
                ctx = _auth_ctx(self)
                if ctx is None:
                    _json(self, 401, {"code": "unauthorized",
                                      "message": "Sign in required."})
                    return
                if ctx["is_demo"]:
                    _redirect(self, "/signup")
                    return
                get_accounts().mark_cancelled(ctx["account_id"])
                _redirect(self, "/subscribe")
                return
            # ---- app APIs (session required; JSON errors) ----
            ctx = _require_api(self)
            if ctx is None:
                return
            self._ctx = ctx
            store = get_store()
            clinic = ctx["clinic_id"]
            px = ctx["prefix"]
            dentist_default = ctx["name"]
            if path == "/api/patient":
                label = form.get("label", "").strip()
                if not DEMO_LABEL_RE.match(label):
                    _json(self, 400, {"code": "bad_label",
                                      "message": "patient label must look synthetic (Demo/Test/Sample …)"})
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
                _redirect(self, f"{px}/patient?id={pid}")
            elif path == "/api/sample-patient":
                pid = store.add_patient(
                    clinic, "Demo Patient Rivera",
                    allergies=[{"substance": "penicillin", "reaction": "rash",
                                "recorded_at": "2026-10-11"}],
                    conditions=["hypertension"],
                    current_meds=[{"name": "warfarin", "dose": "5 mg daily"}],
                    reports={},
                )
                _redirect(self, f"{px}/patient?id={pid}")
            elif path == "/api/sample-check":
                patients = store.list_patients(clinic)
                if not patients:
                    _json(self, 400, {"code": "no_patients",
                                      "message": "load the sample patient first"})
                    return
                pid = patients[0]["patient_id"]
                intended = {"drug_name": "ibuprofen", "strength_mg": 400,
                            "times_per_day": 3, "duration": "5 days",
                            "reason": "post-extraction pain"}
                result = check_prescription(store.get_patient(clinic, pid), intended)
                cid = store.record_check(clinic, pid, dentist_default, intended,
                                         result.verdict,
                                         [f.__dict__ for f in result.flags])
                _redirect(self, f"{px}/check?id={cid}")
            elif path == "/api/check":
                pid = form.get("patient_id", "")
                if not _valid_id(pid):
                    _json(self, 400, {"code": "bad_patient_id",
                                      "message": "bad patient id"})
                    return
                intended = {
                    "drug_name": form.get("drug_name", "").strip(),
                    "strength_mg": _num(form.get("strength_mg")),
                    "times_per_day": _num(form.get("times_per_day")),
                    "duration": form.get("duration", "").strip(),
                    "reason": form.get("reason", "").strip(),
                }
                if not intended["drug_name"]:
                    _json(self, 400, {"code": "missing_drug",
                                      "message": "drug name is required"})
                    return
                patient = store.get_patient(clinic, pid)
                result = check_prescription(patient, intended)
                cid = store.record_check(
                    clinic, pid, form.get("dentist", "").strip() or dentist_default,
                    intended, result.verdict, [f.__dict__ for f in result.flags],
                )
                _redirect(self, f"{px}/check?id={cid}")
            elif path == "/api/review":
                cid = form.get("check_id", "")
                state = form.get("state", "")
                by = form.get("by", "").strip() or dentist_default
                if not _valid_id(cid):
                    _json(self, 400, {"code": "bad_check_id",
                                      "message": "bad check id"})
                    return
                try:
                    store.set_review_state(clinic, cid, state, by,
                                           form.get("note", "").strip())
                except ValueError as e:
                    _json(self, 400, {"code": "bad_review_state", "message": str(e)})
                    return
                _redirect(self, f"{px}/check?id={cid}")
            elif path.startswith("/api/wizard/"):
                m = re.match(r"/api/wizard/(wz_[a-f0-9]{12})/([a-z]+)\Z", path)
                if not m:
                    _json(self, 404, {"code": "not_found", "message": "not found"})
                    return
                state = _wizard_or_404(m.group(1))
                if state is None:
                    _json(self, 404, {"code": "wizard_expired",
                                      "message": "wizard session expired"})
                    return
                if state.get("clinic_id") != clinic:
                    _audit_denied(self, m.group(1), "cross-account wizard access denied")
                    _json(self, 403, {"code": "forbidden",
                                      "message": "cross-account wizard access denied"})
                    return
                token, step = m.group(1), m.group(2)
                multi = form_multi
                if step == "indication":
                    WIZARDS.update(token, {
                        "indication": form.get("indication", ""),
                        "indication_notes": form.get("indication_notes", "").strip(),
                    })
                    _redirect(self, f"{px}/wizard/{token}/factors")
                elif step == "factors":
                    WIZARDS.update(token, {"factors": {
                        "age_band": form.get("age_band", ""),
                        "pregnancy": form.get("pregnancy", ""),
                        "lactation": form.get("lactation", ""),
                        "renal": form.get("renal", ""),
                        "hepatic": form.get("hepatic", ""),
                        "weight_kg": form.get("weight_kg", "").strip(),
                    }})
                    _redirect(self, f"{px}/wizard/{token}/allergies")
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
                    _redirect(self, f"{px}/wizard/{token}/medications")
                elif step == "medications":
                    meds = [
                        {"name": b[0], "dose": b[1]}
                        for b in _parse_lines(form.get("meds", ""), 2) if b[0]
                    ]
                    WIZARDS.update(token, {"meds": meds})
                    _redirect(self, f"{px}/wizard/{token}/conditions")
                elif step == "conditions":
                    conds = [c for c in multi.get("cond", []) if c in CONDITION_CHECKLIST]
                    WIZARDS.update(token, {"conditions": conds})
                    _redirect(self, f"{px}/wizard/{token}/summary")
                elif step == "finish":
                    drug_name = form.get("drug_name", "").strip()
                    if not drug_name:
                        _json(self, 400, {"code": "missing_drug",
                                          "message": "drug name is required"})
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
                            clinic, "Demo Patient Wizard",
                            allergies=context["allergies"],
                            conditions=context["conditions"],
                            current_meds=context["current_meds"],
                        )
                    cid = store.record_check(
                        clinic, patient_id,
                        form.get("dentist", "").strip() or dentist_default,
                        intended, result.verdict,
                        [f.__dict__ for f in result.flags],
                    )
                    _redirect(self, f"{px}/check?id={cid}")
                else:
                    _json(self, 404, {"code": "not_found", "message": "not found"})
            else:
                _json(self, 404, {"code": "not_found", "message": "not found"})
        except (KeyError, TenantMismatchError, ValueError) as e:
            if isinstance(e, TenantMismatchError):
                _audit_denied(self, path, str(e))
                _json(self, 403, {"code": "forbidden", "message": str(e)})
            elif isinstance(e, ValueError):
                _json(self, 400, {"code": "bad_request", "message": str(e)})
            else:
                _json(self, 404, {"code": "not_found", "message": str(e)})

    # -- auth handlers ------------------------------------------------
    def _handle_signup(self, form: dict):
        accounts = get_accounts()
        # DB-backed per-IP throttle (5/hour); isolated per test database.
        if not accounts.signup_allowed(self.client_address[0]):
            _send(self, 429, signup_page(
                ["Too many signups from this address — try again later."], {}))
            return
        values = {
            "name": form.get("name", "").strip(),
            "email": form.get("email", "").strip(),
            "clinic_name": form.get("clinic_name", "").strip(),
        }
        errors: list[str] = []
        password = form.get("password", "")
        confirm = form.get("confirm", "")
        if password != confirm:
            errors.append("Passwords don't match.")
        if form.get("accept_terms") != "1":
            errors.append("Please agree to the Terms of Service to create an account.")
        if form.get("accept_privacy") != "1":
            errors.append("Please confirm you have read the Privacy Policy.")
        if errors:
            _send(self, 400, signup_page(errors, values))
            return
        try:
            acct = accounts.create_account(
                values["name"], values["email"], values["clinic_name"], password,
                legal_version=LEGAL_VERSION)
        except ValueError as e:
            _send(self, 400, signup_page([str(e)], values))
            return
        token = accounts.create_session(acct["account_id"])
        _audit_auth("signup", values["email"])
        _redirect_with_cookie(self, "/welcome", token)

    def _handle_signin(self, form: dict):
        accounts = get_accounts()
        email = (form.get("email", "") or "").strip().lower()
        password = form.get("password", "")
        next_url = _safe_next(form.get("next", ""))
        allowed, wait = accounts.signin_allowed(email)
        if not allowed:
            _send(self, 429, signin_page(
                [f"Too many failed attempts — try again in {int(wait // 60) + 1} minutes."],
                email, next_url))
            return
        acct = accounts.get_account_by_email(email)
        if acct is None or acct["is_demo"] or not verify_password(password, acct["password_hash"]):
            # Generic message: don't reveal whether the email exists.
            accounts.record_signin_failure(email)
            _audit_auth("signin_failed", email)
            _send(self, 401, signin_page(
                ["Email or password didn't match. Try again."], email, next_url))
            return
        accounts.reset_signin_failures(email)
        token = accounts.create_session(acct["account_id"])
        _audit_auth("signin", email)
        _redirect_with_cookie(self, next_url or "/app/start", token)


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


def wizard_step_page(state: dict, step: str, ctx: dict) -> str:
    trial = ctx["trial"]
    px = ctx["prefix"]
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
        + (f"<p><a href='{px}/wizard/{token}/{STEPS[idx-1]}'>← Back</a></p>" if idx > 0 else "")
    )
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def wizard_summary_page(state: dict, ctx: dict) -> str:
    trial = ctx["trial"]
    px = ctx["prefix"]
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
        f"<td><a href='{px}/wizard/{token}/{step}'>edit</a></td></tr>"
        for k, v, step in rows
    )
    body = (
        mia_card("Review everything before choosing. Missing-info flags are shown, never hidden.")
        + wizard_progress("summary")
        + f"<div class='card'><p class='eyebrow'>Step 6 of 7 — Summary</p>"
        f"<table><tr><th>Item</th><th>Answer</th><th></th></tr>{table}</table></div>"
        + (f"<p class='eyebrow'>Missing information</p>{mflags}" if mflags else "<p>No missing-info flags.</p>")
        + f"<p><a class='btn' href='{px}/wizard/{token}/choose'>Continue to prescription choice {ICONS['arrow']}</a></p>"
    )
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


def wizard_choose_page(state: dict, ctx: dict) -> str:
    trial = ctx["trial"]
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
    return shell("copilot", ctx["clinic_name"], trial, body, ctx)


if __name__ == "__main__":
    main()
