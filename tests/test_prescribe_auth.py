"""Auth tests: signup, signin, sessions, per-account trial, lockout, isolation."""
import http.cookiejar
import json
import threading
import time
import urllib.parse
import urllib.request

import pytest

from ai_front_desk.clinical.prescribe import accounts as acct_mod
from ai_front_desk.clinical.prescribe import server as srv


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("auth")
    srv.DB_PATH = tmp / "a.sqlite3"
    srv.STORE = None
    srv.ACCOUNTS = None
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


def _post(opener, base, path, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(base + path, data=data, method="POST")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.headers.get("Location", ""), dict(r.headers)
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers.get("Location", ""), dict(e.headers)
        return e.code, e.read().decode(), dict(e.headers)


def _uniq():
    return f"auth.{time.time_ns()}@example.com"


def _signup(opener, base, email=None, password="correct horse battery staple"):
    email = email or _uniq()
    code, loc, _ = _post(opener, base, "/api/signup", {
        "name": "Dr. Auth", "email": email, "clinic_name": "Auth Dental",
        "password": password, "confirm": password,
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 303, f"signup failed: {code} {loc}"
    return email


def test_password_is_hashed_not_plaintext(live_server):
    c = _client()
    email = _uniq()
    pw = "correct horse battery staple"
    _signup(c, live_server, email=email, password=pw)
    acct = srv.get_accounts().get_account_by_email(email)
    assert acct is not None
    stored = acct["password_hash"]
    assert stored != pw
    assert "pbkdf2-sha256" in stored
    assert acct_mod.verify_password(pw, stored)
    assert not acct_mod.verify_password("wrong password here", stored)


def test_duplicate_email_rejected_case_insensitive(live_server):
    c = _client()
    email = _uniq()
    _signup(c, live_server, email=email)
    c2 = _client()
    code, body, _ = _post(c2, live_server, "/api/signup", {
        "name": "Dr. Dup", "email": email.upper(), "clinic_name": "Dup Dental",
        "password": "correct horse battery staple",
        "confirm": "correct horse battery staple",
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 400
    assert "already exists" in body


def test_signup_validation_errors_inline(live_server):
    c = _client()
    # bad email
    code, body, _ = _post(c, live_server, "/api/signup", {
        "name": "Dr. X", "email": "not-an-email", "clinic_name": "X Dental",
        "password": "correct horse battery staple",
        "confirm": "correct horse battery staple",
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 400 and "doesn&#x27;t look valid" in body or "look valid" in body
    # short password
    code, body, _ = _post(c, live_server, "/api/signup", {
        "name": "Dr. X", "email": _uniq(), "clinic_name": "X Dental",
        "password": "short", "confirm": "short",
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 400 and "10 characters" in body
    # mismatched confirm
    code, body, _ = _post(c, live_server, "/api/signup", {
        "name": "Dr. X", "email": _uniq(), "clinic_name": "X Dental",
        "password": "correct horse battery staple", "confirm": "different words here ok",
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 400 and "don&#x27;t match" in body or "match" in body


def test_signin_wrong_password_no_session(live_server):
    c = _client()
    email = _uniq()
    _signup(c, live_server, email=email)
    c2 = _client()
    code, body, headers = _post(c2, live_server, "/api/signin", {
        "email": email, "password": "definitely wrong password",
    })
    assert code == 401
    assert "didn&#x27;t match" in body or "match" in body
    # no session cookie was set
    assert "mia_session" not in (headers.get("Set-Cookie") or "")
    # and the app is still locked for this client
    code, loc, _ = _get(c2, live_server, "/app/patients")
    assert code == 303 and loc.startswith("/signin")


def test_signin_success_and_session_persists(live_server):
    c = _client()
    email = _uniq()
    pw = "correct horse battery staple"
    _signup(c, live_server, email=email, password=pw)
    c2 = _client()  # fresh client, no session
    code, loc, _ = _post(c2, live_server, "/api/signin", {
        "email": email, "password": pw,
    })
    assert code == 303
    code, body, _ = _get(c2, live_server, "/app/patients")
    assert code == 200 and "Prescribing Copilot" in body
    # account chip shows the signed-in dentist
    assert "Dr. Auth" in body


def test_signout_invalidates_session(live_server):
    c = _client()
    _signup(c, live_server)
    code, body, _ = _get(c, live_server, "/app/patients")
    assert code == 200
    code, loc, _ = _get(c, live_server, "/signout")
    assert code == 303 and loc == "/"
    code, loc, _ = _get(c, live_server, "/app/patients")
    assert code == 303 and loc.startswith("/signin")


def test_trial_expiry_locks_and_subscribe_unlocks(live_server):
    c = _client()
    email = _uniq()
    _signup(c, live_server, email=email)
    accounts = srv.get_accounts()
    acct = accounts.get_account_by_email(email)
    # backdate the trial 8 days -> expired
    accounts.set_trial_start(acct["account_id"], time.time() - 8 * 86400)
    code, loc, _ = _get(c, live_server, "/app/patients")
    assert code == 303 and loc == "/subscribe"
    code, body, _ = _post(c, live_server, "/api/sample-patient", {})
    assert code == 402
    assert json.loads(body)["code"] == "subscription_required"
    # manual Neteller flow: dentist clicks "I've paid" -> pending (still locked)
    code, loc, _ = _post(c, live_server, "/api/billing/paid", {})
    assert code == 303 and loc == "/subscribe"
    code, loc2, _ = _get(c, live_server, "/app/patients")
    assert code == 303 and loc2 == "/subscribe"  # pending != unlocked
    code, body, _ = _get(c, live_server, "/subscribe")
    assert code == 200 and "activating your account" in body.lower()
    # founder activates via the admin path -> unlocked
    accounts.mark_subscribed(acct["account_id"], "neteller-manual-001")
    code, body, _ = _get(c, live_server, "/app/patients")
    assert code == 200


def test_cross_account_patient_access_forbidden(live_server):
    a = _client()
    _signup(a, live_server)
    code, loc, _ = _post(a, live_server, "/api/patient", {
        "label": "Demo Private", "allergies": "", "conditions": "", "meds": "",
    })
    assert code == 303 and "id=pat_" in loc
    pid = loc.split("id=")[1]
    b = _client()
    b_email = _uniq()
    _signup(b, live_server, email=b_email)
    code, body, _ = _get(b, live_server, f"/app/patient?id={pid}")
    assert code == 403
    # the denied attempt was audited under B's namespace
    b_acct = srv.get_accounts().get_account_by_email(b_email)
    trail = srv.get_store().audit_trail(b_acct["account_id"])
    assert any(r["action"] == "access_denied" for r in trail)


def test_brute_force_lockout(live_server):
    c = _client()
    email = _uniq()
    _signup(c, live_server, email=email)
    c2 = _client()
    for _ in range(10):
        code, _, _ = _post(c2, live_server, "/api/signin", {
            "email": email, "password": "wrong password attempt",
        })
        assert code == 401
    code, body, _ = _post(c2, live_server, "/api/signin", {
        "email": email, "password": "wrong password attempt",
    })
    assert code == 429
    assert "Too many failed attempts" in body


def test_demo_cannot_signin_as_demo_email(live_server):
    c = _client()
    code, body, _ = _post(c, live_server, "/api/signin", {
        "email": "demo@localhost", "password": "anything at all here",
    })
    assert code in (401, 429)
