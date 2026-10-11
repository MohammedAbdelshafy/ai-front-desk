"""HTTP tests for the Mia Dental OS demo server (accounts + auth + demo)."""
import http.cookiejar
import re
import threading
import time
import urllib.parse
import urllib.request

import pytest

from ai_front_desk.clinical.prescribe import server as srv


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("srv")
    srv.DB_PATH = tmp / "s.sqlite3"
    srv.STORE = None  # force re-init against the tmp db
    srv.ACCOUNTS = None  # force re-init against the tmp db
    if hasattr(srv, "_SIGNUP_ATTEMPTS"):
        srv._SIGNUP_ATTEMPTS.clear()
    import os
    os.environ["PRESCRIBE_STATE_DIR"] = str(tmp / "state")
    http = srv.HTTPServer(("127.0.0.1", 0), srv.Handler)
    port = http.server_address[1]
    t = threading.Thread(target=http.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    http.shutdown()


@pytest.fixture(autouse=True)
def _reset_signup_limiter(live_server):
    # The per-IP signup throttle is DB-backed and shared across this module's
    # tests (module-scoped DB); reset per test so the suite exercises
    # validation logic instead of tripping the throttle.
    accounts = srv.get_accounts()
    accounts._db.execute("DELETE FROM prescribe_signup_attempts")
    accounts._db.commit()
    yield


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _client():
    """A client with its own cookie jar (session isolation per test)."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), _NoRedirect)
    return opener


def _get(opener, base, path):
    """Returns (code, location-or-body): Location header on 3xx, body otherwise."""
    req = urllib.request.Request(base + path, method="GET")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers.get("Location", "")
        return e.code, e.read().decode()



def _csrf_token(opener, base):
    """Extract the session's CSRF token from a form page (test helper)."""
    for path in ("/app/start", "/subscribe"):
        res = _get(opener, base, path)
        body = res[1] if len(res) > 1 else ""
        if not isinstance(body, str):
            continue
        m = re.search(r"name='csrf_token' value='([^']*)'", body)
        if m:
            return m.group(1)
    return ""


def _post(opener, base, path, fields, csrf=True):
    fields = dict(fields)
    if csrf and "csrf_token" not in fields:
        tok = _csrf_token(opener, base)
        if tok:
            fields["csrf_token"] = tok
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(base + path, data=data, method="POST")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers.get("Location", "")
        return e.code, e.read().decode()


def _signup(opener, base, name="Dr. Test", email=None, clinic="Test Dental",
            password="correct horse battery staple"):
    email = email or f"dr.test.{time.time_ns()}@example.com"
    code, loc = _post(opener, base, "/api/signup", {
        "name": name, "email": email, "clinic_name": clinic,
        "password": password, "confirm": password,
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 303, f"signup failed: {code} {loc}"
    assert loc == "/welcome"
    return email


def test_landing_page_public(live_server):
    c = _client()
    code, body = _get(c, live_server, "/")
    assert code == 200
    assert "Mia Dental OS" in body
    assert "Mia Dental Prescribing Copilot" in body
    assert "7-day" in body
    assert "/signup" in body
    assert "/demo" in body


def test_signup_and_signin_pages_public(live_server):
    c = _client()
    code, body = _get(c, live_server, "/signup")
    assert code == 200 and "7-day free trial" in body
    code, body = _get(c, live_server, "/signin")
    assert code == 200 and "Sign in" in body


def test_app_requires_signin(live_server):
    c = _client()
    code, loc = _get(c, live_server, "/app/patients")
    assert code == 303
    assert loc.startswith("/signin?next=")


def test_api_requires_signin_json(live_server):
    import json
    c = _client()
    code, body = _post(c, live_server, "/api/sample-patient", {})
    assert code == 401
    obj = json.loads(body)
    assert obj["code"] == "unauthorized"


def test_signup_starts_trial_and_unlocks(live_server):
    c = _client()
    _signup(c, live_server)
    code, body = _get(c, live_server, "/app/patients")
    assert code == 200
    assert "Prescribing Copilot" in body
    # trial pill is per-account
    assert "days left" in body


def test_welcome_onboarding(live_server):
    c = _client()
    _signup(c, live_server, name="Dr. Rivera")
    code, body = _get(c, live_server, "/welcome")
    assert code == 200
    assert "Welcome, Dr. Rivera" in body
    assert "guided check" in body.lower() or "sample patient" in body.lower()


def test_sample_flow_end_to_end(live_server):
    c = _client()
    _signup(c, live_server)
    code, loc = _post(c, live_server, "/api/sample-patient", {})
    assert code == 303 and "id=pat_" in loc
    code, loc = _post(c, live_server, "/api/sample-check", {})
    assert code == 303 and "id=chk_" in loc
    # The redirect target must be a well-formed check URL — regression guard:
    # following it must resolve to the recorded check (HTTP 200), never 404.
    assert re.fullmatch(
        r"/app/check\?id=chk_[a-f0-9]{12}", loc
    ), f"unexpected redirect target: {loc}"
    code, body = _get(c, live_server, loc)
    assert code == 200
    assert "RED" in body
    assert "reference v2" in body
    assert "warfarin" in body.lower() or "nsaid" in body.lower()


def test_review_records_clinician_conclusion(live_server):
    c = _client()
    _signup(c, live_server)
    _post(c, live_server, "/api/sample-patient", {})
    _, loc = _post(c, live_server, "/api/sample-check", {})
    check_id = loc.split("id=")[1]
    code, _ = _post(
        c, live_server, "/api/review",
        {"check_id": check_id, "state": "clinician_reviewed",
         "by": "Dr. Test", "note": "Switched to paracetamol."},
    )
    assert code == 303
    code, body = _get(c, live_server, loc)
    assert code == 200
    assert "clinician reviewed" in body
    assert "paracetamol" in body


def test_reference_page_lists_drugs(live_server):
    c = _client()
    _signup(c, live_server)
    code, body = _get(c, live_server, "/app/reference")
    assert code == 200
    assert "Amoxicillin" in body
    assert "reference v2 (2026-10-11)" in body


def test_wizard_guided_flow(live_server):
    c = _client()
    _signup(c, live_server)  # trial starts at sign-up
    # start wizard (no patient -> will create demo patient at finish)
    code, loc = _get(c, live_server, "/app/wizard/start")
    assert code == 303 and "/app/wizard/wz_" in loc and loc.endswith("/indication")
    token = loc.split("/app/wizard/")[1].split("/")[0]
    # step 1: indication
    code, loc = _post(c, live_server, f"/api/wizard/{token}/indication",
                      {"indication": "infection", "indication_notes": "abscess"})
    assert code == 303 and loc.endswith("/factors")
    # step 2: factors
    code, loc = _post(c, live_server, f"/api/wizard/{token}/factors",
                      {"age_band": "31–50", "pregnancy": "no", "lactation": "no",
                       "renal": "no", "hepatic": "no", "weight_kg": ""})
    assert code == 303 and loc.endswith("/allergies")
    # step 3: allergies
    code, loc = _post(c, live_server, f"/api/wizard/{token}/allergies",
                      {"allergies": "penicillin | rash", "latex_allergy": "no",
                       "anesthesia_history": ""})
    assert code == 303 and loc.endswith("/medications")
    # step 4: meds (none)
    code, loc = _post(c, live_server, f"/api/wizard/{token}/medications", {"meds": ""})
    assert code == 303 and loc.endswith("/conditions")
    # step 5: conditions (none)
    code, loc = _post(c, live_server, f"/api/wizard/{token}/conditions", {})
    assert code == 303 and loc.endswith("/summary")
    # summary shows missing-info handling
    code, body = _get(c, live_server, loc)
    assert code == 200 and "Summary" in body
    # choose page shows indication reference
    code, body = _get(c, live_server, f"/app/wizard/{token}/choose")
    assert code == 200 and "Amoxicillin" in body and "reference v2" in body
    # finish with the dentist's own choice -> RED via penicillin allergy
    code, loc = _post(c, live_server, f"/api/wizard/{token}/finish",
                      {"drug_name": "amoxicillin", "strength_mg": "500",
                       "times_per_day": "3", "dentist": "Dr. Test"})
    assert code == 303 and "/app/check" in loc
    code, body = _get(c, live_server, loc)
    assert code == 200 and "RED" in body and "penicillin" in body.lower()


def test_upgrades_show_exact_tier_names(live_server):
    c = _client()
    _signup(c, live_server)
    code, body = _get(c, live_server, "/app/upgrades")
    assert code == 200
    assert "Mia Dental Practice" in body
    assert "Mia Dental Automation" in body
    assert "Mia Dental OS Pro" in body


def test_demo_explore_without_signup(live_server):
    c = _client()
    code, loc = _get(c, live_server, "/demo")
    assert code == 303 and loc == "/demo/start"
    code, body = _get(c, live_server, "/demo/start")
    assert code == 200
    assert "Explore demo" in body
    # demo can run the sample flow in its own namespace
    code, loc = _post(c, live_server, "/api/sample-patient", {})
    assert code == 303 and loc.startswith("/demo/patient?id=pat_")
    code, body = _get(c, live_server, "/demo/patients")
    assert code == 200 and "Demo Patient Rivera" in body


def test_demo_data_never_mixes_with_accounts(live_server):
    demo = _client()
    _get(demo, live_server, "/demo")  # establish demo session
    acct = _client()
    _signup(acct, live_server)
    code, body = _get(acct, live_server, "/app/patients")
    assert code == 200
    assert "Demo Patient Rivera" not in body  # demo's patients are invisible here
