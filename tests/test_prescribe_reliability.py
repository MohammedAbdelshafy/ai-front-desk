"""Reliability tests: the four non-negotiables.

1. CAN'T LAG — threaded server, benchmark: every page < 300ms.
2. CAN'T MAKE MISTAKES — wizard step order, idempotent finish, transitions.
3. CAN'T LOSE INFO — commits, backup round-trip, kill -9 crash safety.
4. CAN'T GET HACKED — CSRF, no version leak, 413, generic 500, no fixation.

See docs/engineering/RELIABILITY.md.
"""
import http.cookiejar
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
import urllib.parse
import urllib.request

import pytest

from ai_front_desk.clinical.prescribe import server as srv


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("rel")
    srv.DB_PATH = tmp / "r.sqlite3"
    srv.STORE = None
    srv.ACCOUNTS = None
    os.environ["PRESCRIBE_STATE_DIR"] = str(tmp / "state")
    http = srv.HTTPServer(("127.0.0.1", 0), srv.Handler)
    port = http.server_address[1]
    t = threading.Thread(target=http.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    http.shutdown()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _client():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), _NoRedirect)


def _get(opener, base, path):
    req = urllib.request.Request(base + path, method="GET")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.read().decode(), dict(r.headers)
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers.get("Location", ""), dict(e.headers)
        return e.code, e.read().decode(), dict(e.headers)


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
            return r.status, r.headers.get("Location", ""), dict(r.headers)
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers.get("Location", ""), dict(e.headers)
        return e.code, e.read().decode(), dict(e.headers)


@pytest.fixture(autouse=True)
def _reset_signup_limiter(live_server):
    accounts = srv.get_accounts()
    accounts._db.execute("DELETE FROM prescribe_signup_attempts")
    accounts._db.commit()
    yield


def _signup(opener, base, email=None):
    email = email or f"rel.{time.time_ns()}@example.com"
    pw = "correct horse battery staple"
    code, _, _ = _post(opener, base, "/api/signup", {
        "name": "Dr. Rel", "email": email, "clinic_name": "Rel Dental",
        "password": pw, "confirm": pw,
        "accept_terms": "1", "accept_privacy": "1",
    }, csrf=False)  # signup is pre-auth: no CSRF token exists yet
    assert code == 303, f"signup failed: {code}"
    return email


def _wizard_token(opener, base):
    code, loc, _ = _get(opener, base, "/app/wizard/start")
    assert code == 303 and "/app/wizard/wz_" in loc
    return loc.split("/app/wizard/")[1].split("/")[0]


def _walk_wizard(opener, base, token, drug="amoxicillin"):
    """Walk all 5 POST steps in order, then finish. Returns the check URL."""
    steps = [
        ("indication", {"indication": "infection", "indication_notes": ""}),
        ("factors", {"age_band": "31–50", "pregnancy": "no", "lactation": "no",
                      "renal": "no", "hepatic": "no", "weight_kg": ""}),
        ("allergies", {"allergies": "", "no_known_allergies": "1",
                        "latex_allergy": "no", "anesthesia_history": ""}),
        ("medications", {"meds": ""}),
        ("conditions", {}),
    ]
    for step, fields in steps:
        code, loc, _ = _post(opener, base, f"/api/wizard/{token}/{step}", fields)
        assert code == 303, f"step {step}: {code}"
    code, loc, _ = _post(opener, base, f"/api/wizard/{token}/finish",
                         {"drug_name": drug, "strength_mg": "500",
                          "times_per_day": "3", "dentist": "Dr. Rel"})
    assert code == 303, f"finish: {code} {loc}"
    return loc


# ---------------------------------------------------------------- lag ---
def test_server_is_threaded():
    import http.server as hs
    assert issubclass(srv.HTTPServer, hs.ThreadingHTTPServer)


def test_benchmark_signup_wizard_check(live_server):
    """Every page in the core flow renders in < 300ms locally.

    Signup/signin are measured separately: PBKDF2-HMAC-SHA256 (200k
    iterations) is intentionally slow — that's the password hashing doing
    its job, not a page render.
    """
    c = _client()
    timings = {}
    crypto = {}

    def timed(name, fn, bucket):
        t0 = time.perf_counter()
        out = fn()
        bucket[name] = (time.perf_counter() - t0) * 1000
        return out

    timed("landing", lambda: _get(c, live_server, "/"), timings)
    email = f"bench.{time.time_ns()}@example.com"
    pw = "correct horse battery staple"
    timed("signup", lambda: _post(c, live_server, "/api/signup", {
        "name": "Dr. Bench", "email": email, "clinic_name": "Bench Dental",
        "password": pw, "confirm": pw, "accept_terms": "1", "accept_privacy": "1",
    }, csrf=False), crypto)
    timed("app_start", lambda: _get(c, live_server, "/app/start"), timings)
    token = _wizard_token(c, live_server)
    timed("wizard_indication_get",
          lambda: _get(c, live_server, f"/app/wizard/{token}/indication"),
          timings)
    # Time each wizard POST individually (per-page target, not per-walk).
    steps = [
        ("indication", {"indication": "infection", "indication_notes": ""}),
        ("factors", {"age_band": "31–50", "pregnancy": "no", "lactation": "no",
                      "renal": "no", "hepatic": "no", "weight_kg": ""}),
        ("allergies", {"allergies": "", "no_known_allergies": "1",
                        "latex_allergy": "no", "anesthesia_history": ""}),
        ("medications", {"meds": ""}),
        ("conditions", {}),
    ]
    for step, fields in steps:
        def do_step(s=step, f=fields):
            code, _, _ = _post(c, live_server, f"/api/wizard/{token}/{s}", f)
            assert code == 303, f"step {s}: {code}"
        timed(f"wizard_post_{step}", do_step, timings)
    def do_finish():
        code, loc, _ = _post(c, live_server, f"/api/wizard/{token}/finish",
                             {"drug_name": "amoxicillin", "strength_mg": "500",
                              "times_per_day": "3", "dentist": "Dr. Bench"})
        assert code == 303
        return loc
    loc = timed("wizard_finish", do_finish, timings)
    timed("check_page", lambda: _get(c, live_server, loc), timings)

    slow = {k: round(v, 1) for k, v in timings.items() if v >= 300}
    assert not slow, f"pages over 300ms: {slow}"
    slow_crypto = {k: round(v, 1) for k, v in crypto.items() if v >= 1500}
    assert not slow_crypto, f"auth over 1500ms: {slow_crypto}"
    # Print the numbers for the report.
    print("\nbenchmark ms:",
          {k: round(v, 1) for k, v in {**timings, **crypto}.items()})


def test_concurrent_requests_dont_block(live_server):
    """20 concurrent page loads all succeed (threaded server)."""
    c = _client()
    _signup(c, live_server)
    results = []

    def hit():
        try:
            code, _, _ = _get(_client(), live_server, "/")
            # fresh client: landing is public
            results.append(code)
        except Exception as e:  # pragma: no cover
            results.append(str(e))

    threads = [threading.Thread(target=hit) for _ in range(20)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)
    elapsed = time.perf_counter() - t0
    assert len(results) == 20 and all(r == 200 for r in results), results[:5]
    assert elapsed < 10, f"20 concurrent hits took {elapsed:.1f}s"


# ----------------------------------------------------------- mistakes ---
def test_wizard_step_post_out_of_order_rejected(live_server):
    c = _client()
    _signup(c, live_server)
    token = _wizard_token(c, live_server)
    # Skip straight to conditions without doing indication/factors/allergies.
    code, body, _ = _post(c, live_server, f"/api/wizard/{token}/conditions", {})
    assert code == 409
    assert json.loads(body)["code"] == "step_locked"


def test_wizard_step_get_out_of_order_redirects(live_server):
    c = _client()
    _signup(c, live_server)
    token = _wizard_token(c, live_server)
    code, loc, _ = _get(c, live_server, f"/app/wizard/{token}/conditions")
    assert code == 303
    assert loc.endswith("/indication")


def test_wizard_finish_without_steps_rejected(live_server):
    c = _client()
    _signup(c, live_server)
    token = _wizard_token(c, live_server)
    code, body, _ = _post(c, live_server, f"/api/wizard/{token}/finish",
                          {"drug_name": "amoxicillin"})
    assert code == 409
    assert json.loads(body)["code"] == "cannot_finish"


def test_wizard_double_finish_is_idempotent(live_server):
    c = _client()
    _signup(c, live_server)
    token = _wizard_token(c, live_server)
    loc1 = _walk_wizard(c, live_server, token)
    # Second finish with identical payload: same check, no duplicate.
    code, loc2, _ = _post(c, live_server, f"/api/wizard/{token}/finish",
                          {"drug_name": "amoxicillin", "strength_mg": "500",
                           "times_per_day": "3", "dentist": "Dr. Rel"})
    assert code == 303
    assert loc1 == loc2, f"double finish created a second check: {loc1} vs {loc2}"


def test_wizard_concurrent_finish_creates_one_check(live_server):
    c, jar = _client_with_jar()
    _signup(c, live_server)
    token = _wizard_token(c, live_server)
    # Walk steps with the shared client (sequential), then race the finish.
    steps = [
        ("indication", {"indication": "infection", "indication_notes": ""}),
        ("factors", {"age_band": "31–50", "pregnancy": "no", "lactation": "no",
                      "renal": "no", "hepatic": "no", "weight_kg": ""}),
        ("allergies", {"allergies": "", "no_known_allergies": "1",
                        "latex_allergy": "no", "anesthesia_history": ""}),
        ("medications", {"meds": ""}),
        ("conditions", {}),
    ]
    for step, fields in steps:
        _post(c, live_server, f"/api/wizard/{token}/{step}", fields)
    csrf = _csrf_token(c, live_server)
    # Count checks before.
    before = _count_checks_for_token_wizard(c, live_server)

    barrier = threading.Barrier(5)
    locs = []
    errors = []

    def finish_race():
        try:
            # Share the SAME cookie jar (thread-safe): all racers act as the
            # same signed-in dentist from different threads.
            cc = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(jar), _NoRedirect)
            barrier.wait(timeout=10)
            code, loc, _ = _post(cc, live_server, f"/api/wizard/{token}/finish",
                                 {"drug_name": "amoxicillin", "csrf_token": csrf})
            locs.append((code, loc))
        except Exception as e:  # pragma: no cover - diagnostic
            errors.append(repr(e))

    threads = [threading.Thread(target=finish_race) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)
    assert not errors, errors[:3]
    after = _count_checks_for_token_wizard(c, live_server)
    assert after - before == 1, f"concurrent finish created {after - before} checks"
    # Every racer got either the check redirect or a graceful 409.
    for code, loc in locs:
        assert code in (303, 409), (code, loc)


def _count_checks_for_token_wizard(opener, base):
    code, body, _ = _get(opener, base, "/app/patients")
    # patients page lists patients; count via the store instead (same process).
    return len(srv.get_store()._db.execute(
        "SELECT check_id FROM prescribe_checks").fetchall())


def test_double_submit_patient_form_no_crash(live_server):
    c = _client()
    _signup(c, live_server)
    fields = {"label": "Demo Double", "allergies": "", "conditions": "", "meds": ""}
    code1, loc1, _ = _post(c, live_server, "/api/patient", fields)
    code2, loc2, _ = _post(c, live_server, "/api/patient", fields)
    assert code1 == 303 and code2 == 303
    # Two patients is fine (explicit creates); what matters is no 500.
    assert loc1 != loc2  # distinct ids, no collision


def test_billing_transition_subscribed_to_pending_rejected(live_server):
    accounts = srv.get_accounts()
    acct = accounts.create_account(
        "Dr. Trans", f"trans.{time.time_ns()}@example.com", "Trans Dental",
        "correct horse battery staple")
    acct_id = acct["account_id"]
    accounts.mark_subscribed(acct_id, "neteller-test-1")
    with pytest.raises(ValueError, match="already subscribed"):
        accounts.mark_payment_pending(acct_id)


# ----------------------------------------------------------------- lose ---
def test_backup_round_trip(live_server, tmp_path):
    from ai_front_desk.clinical.prescribe import admin as admin_mod
    c = _client()
    email = _signup(c, live_server)
    # Create clinical data through the HTTP API.
    _post(c, live_server, "/api/patient", {
        "label": "Demo Backup", "allergies": "penicillin | rash",
        "conditions": "hypertension", "meds": "warfarin | 5 mg daily"})
    store = srv.get_store()
    n_patients = len(store._db.execute(
        "SELECT patient_id FROM prescribe_patients").fetchall())
    # cmd_backup resolves the DB via PRESCRIBE_DB: point it at this test's DB.
    os.environ["PRESCRIBE_DB"] = str(srv.DB_PATH)
    dest = tmp_path / "backups"
    dest.mkdir(parents=True, exist_ok=True)
    rc = admin_mod.cmd_backup(srv.get_accounts(), str(dest))
    assert rc == 0
    backups = list(dest.glob("*.sqlite3"))
    assert len(backups) == 1
    # Restore into a fresh file and verify the data is there.
    restored = tmp_path / "restored.sqlite3"
    restored.write_bytes(backups[0].read_bytes())
    chk = sqlite3.connect(str(restored))
    try:
        n2 = chk.execute("SELECT COUNT(*) FROM prescribe_patients").fetchone()[0]
        assert n2 >= n_patients and n2 > 0
        assert chk.execute("SELECT COUNT(*) FROM prescribe_accounts").fetchone()[0] > 0
    finally:
        chk.close()


def test_crash_safety_kill9(live_server, tmp_path):
    """kill -9 the server mid-flow; committed data must survive restart."""
    db = tmp_path / "crash.sqlite3"
    state = tmp_path / "crash-state"
    env = dict(os.environ, PRESCRIBE_DB=str(db),
               PRESCRIBE_STATE_DIR=str(state), PRESCRIBE_PORT="18791")
    proc = subprocess.Popen(
        [sys.executable, "-m", "ai_front_desk.clinical.prescribe.server"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    try:
        base = "http://127.0.0.1:18791"
        c = _client()
        # Wait for boot.
        for _ in range(50):
            try:
                code, _, _ = _get(c, base, "/")
                if code == 200:
                    break
            except Exception:
                time.sleep(0.2)
        email = f"crash.{time.time_ns()}@example.com"
        pw = "correct horse battery staple"
        code, _, _ = _post(c, base, "/api/signup", {
            "name": "Dr. Crash", "email": email, "clinic_name": "Crash Dental",
            "password": pw, "confirm": pw,
            "accept_terms": "1", "accept_privacy": "1"}, csrf=False)
        assert code == 303
        code, loc, _ = _post(c, base, "/api/patient", {
            "label": "Demo Crash", "allergies": "penicillin | rash",
            "conditions": "", "meds": ""})
        assert code == 303 and "id=pat_" in loc
        # SIGKILL — no graceful shutdown, no cleanup.
        proc.kill()
        proc.wait(timeout=10)
        proc = None
        # Reopen the database file directly: the patient must be there.
        chk = sqlite3.connect(str(db))
        try:
            rows = chk.execute(
                "SELECT label FROM prescribe_patients WHERE label='Demo Crash'"
            ).fetchall()
            assert len(rows) == 1, "patient lost across kill -9"
            accts = chk.execute(
                "SELECT email FROM prescribe_accounts WHERE email=?",
                (email,)).fetchall()
            assert len(accts) == 1, "account lost across kill -9"
        finally:
            chk.close()
    finally:
        if proc is not None:
            proc.kill()


# --------------------------------------------------------------- hacked ---
def test_post_without_csrf_rejected(live_server):
    c = _client()
    _signup(c, live_server)
    code, body, _ = _post(c, live_server, "/api/patient", {
        "label": "Demo NoCsrf", "allergies": "", "conditions": "", "meds": "",
    }, csrf=False)
    assert code == 403
    assert json.loads(body)["code"] == "forbidden"


def test_post_with_wrong_csrf_rejected(live_server):
    c = _client()
    _signup(c, live_server)
    code, body, _ = _post(c, live_server, "/api/patient", {
        "label": "Demo BadCsrf", "allergies": "", "conditions": "", "meds": "",
        "csrf_token": "wrong-token",
    })
    assert code == 403


def test_post_with_valid_csrf_works(live_server):
    c = _client()
    _signup(c, live_server)
    code, loc, _ = _post(c, live_server, "/api/patient", {
        "label": "Demo GoodCsrf", "allergies": "", "conditions": "", "meds": ""})
    assert code == 303 and "id=pat_" in loc


def test_no_version_disclosure(live_server):
    c = _client()
    code, _, headers = _get(c, live_server, "/")
    server_hdr = headers.get("Server", "")
    assert "MiaDentalOS" not in server_hdr, server_hdr
    assert "Python" not in server_hdr, server_hdr


def test_oversized_body_rejected_413(live_server):
    c = _client()
    _signup(c, live_server)
    big = "x" * (srv.MAX_BODY + 1000)
    data = urllib.parse.urlencode({"label": "Demo Big", "allergies": big}).encode()
    req = urllib.request.Request(live_server + "/api/patient", data=data,
                                 method="POST")
    # The 413 body-size gate fires before CSRF validation, so no token needed.
    try:
        with c.open(req, timeout=10) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    assert code == 413, f"expected 413, got {code}"


def test_generic_500_no_traceback(live_server, monkeypatch):
    c = _client()
    _signup(c, live_server)

    def boom():
        raise RuntimeError("simulated internal failure")
    monkeypatch.setattr(srv, "get_store", boom)
    try:
        code, body, _ = _get(c, live_server, "/app/patients")
    finally:
        # restore is automatic via monkeypatch
        pass
    assert code == 500
    assert "Traceback" not in body
    assert "simulated internal failure" not in body


def _client_with_jar():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), _NoRedirect)
    return opener, jar


def test_no_session_fixation(live_server):
    """Every signin mints a fresh token; a pre-set cookie is never reused."""
    c = _client()
    email = _signup(c, live_server)
    pw = "correct horse battery staple"

    def signin_token():
        cc, jar = _client_with_jar()
        # Attacker plants a cookie before login (fixation attempt).
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name="mia_session", value="attacker-chosen-value",
            port=None, port_specified=False, domain="127.0.0.1",
            domain_specified=False, domain_initial_dot=False, path="/",
            path_specified=True, secure=False, expires=None, discard=True,
            comment=None, comment_url=None, rest={}, rfc2109=False))
        code, _, _ = _post(cc, live_server, "/api/signin",
                           {"email": email, "password": pw}, csrf=False)
        assert code == 303
        for cookie in jar:
            if cookie.name == "mia_session":
                return cookie.value
        raise AssertionError("no session cookie after signin")

    t1 = signin_token()
    t2 = signin_token()
    assert t1 != "attacker-chosen-value" and t2 != "attacker-chosen-value"
    assert t1 != t2, "signin reused a token — fixation possible"
