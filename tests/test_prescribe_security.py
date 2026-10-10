"""Security tests: headers, rate limits, input caps, session lifetime, audit."""
import http.cookiejar
import threading
import time
import urllib.parse
import urllib.request

import pytest

from ai_front_desk.clinical.prescribe import server as srv


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("sec")
    srv.DB_PATH = tmp / "s.sqlite3"
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


@pytest.fixture(autouse=True)
def _reset_signup_limiter(live_server):
    # The per-IP signup throttle is DB-backed and shared across this module's
    # tests (module-scoped DB); reset per test so the suite exercises
    # validation logic instead of tripping the throttle.
    accounts = srv.get_accounts()
    accounts._db.execute("DELETE FROM prescribe_signup_attempts")
    accounts._db.commit()
    yield


def _signup(opener, base, email=None):
    email = email or f"sec.{time.time_ns()}@example.com"
    pw = "correct horse battery staple"
    code, _, _ = _post(opener, base, "/api/signup", {
        "name": "Dr. Sec", "email": email, "clinic_name": "Sec Dental",
        "password": pw, "confirm": pw,
        "accept_terms": "1", "accept_privacy": "1",
    })
    assert code == 303, f"signup failed: {code}"
    return email


def test_security_headers_on_pages(live_server):
    c = _client()
    for path in ("/", "/signup", "/signin", "/privacy", "/terms", "/security"):
        code, _, headers = _get(c, live_server, path)
        assert code == 200, path
        assert headers.get("X-Content-Type-Options") == "nosniff", path
        assert headers.get("X-Frame-Options") == "DENY", path
        csp = headers.get("Content-Security-Policy", "")
        assert "script-src 'none'" in csp, path
        assert "frame-ancestors 'none'" in csp, path


def test_security_headers_on_json_and_redirect(live_server):
    c = _client()
    code, _, headers = _get(c, live_server, "/app/patients")
    assert code == 303
    assert headers.get("X-Frame-Options") == "DENY"
    code, body, headers = _post(c, live_server, "/api/signin",
                                {"email": "no@one.com", "password": "wrong"})
    assert code == 401
    assert headers.get("X-Content-Type-Options") == "nosniff"


def test_session_cookie_is_httponly_samesite(live_server):
    c = _client()
    email = f"cookie.{time.time_ns()}@example.com"
    pw = "correct horse battery staple"
    data = urllib.parse.urlencode({
        "name": "Dr. Sec", "email": email, "clinic_name": "Sec Dental",
        "password": pw, "confirm": pw,
        "accept_terms": "1", "accept_privacy": "1",
    }).encode()
    req = urllib.request.Request(live_server + "/api/signup", data=data, method="POST")
    try:
        with c.open(req, timeout=10) as r:
            raw = r.headers.get("Set-Cookie", "")
    except urllib.error.HTTPError as e:
        raw = e.headers.get("Set-Cookie", "") if e.headers else ""
    assert "mia_session=" in raw, f"no session cookie: {raw[:120]}"
    lowered = raw.lower()
    assert "httponly" in lowered
    assert "samesite=lax" in lowered


def test_signup_rate_limit(live_server):
    # 5/hour/IP allowed; the 6th is rejected. (Other tests in this module
    # already consumed signups from 127.0.0.1, so just assert eventually 429.)
    c = _client()
    got_429 = False
    for i in range(8):
        pw = "correct horse battery staple"
        code, _, _ = _post(c, live_server, "/api/signup", {
            "name": "Dr. Flood", "email": f"flood.{time.time_ns()}.{i}@example.com",
            "clinic_name": "Flood Dental", "password": pw, "confirm": pw,
            "accept_terms": "1", "accept_privacy": "1",
        })
        if code == 429:
            got_429 = True
            break
    assert got_429, "expected signup rate limit to trigger"


def test_oversized_input_is_capped(live_server):
    c = _client()
    email = _signup(c, live_server)
    huge = "x" * 20000
    code, _, _ = _post(c, live_server, "/api/patient", {
        "label": "Demo Huge", "allergies": huge, "conditions": "", "meds": "",
    })
    assert code in (303, 400)  # accepted-but-capped, or rejected — never 500
    # session still valid after the abuse attempt
    code, _, _ = _get(c, live_server, "/app/patients")
    assert code == 200


def test_session_absolute_timeout(live_server):
    c = _client()
    email = _signup(c, live_server)
    accounts = srv.get_accounts()
    acct = accounts.get_account_by_email(email)
    # backdate the session's creation beyond the absolute cap
    import sqlite3
    db = sqlite3.connect(str(accounts.path))
    db.execute(
        "UPDATE prescribe_sessions SET created_at = ?",
        (time.time() - 8 * 24 * 3600,),
    )
    db.commit()
    db.close()
    code, _, _ = _get(c, live_server, "/app/patients")
    assert code == 303  # session killed despite sliding refresh


def test_auth_events_audited(live_server):
    c = _client()
    email = _signup(c, live_server)
    _post(c, live_server, "/api/signin",
          {"email": email, "password": "wrong password here"})
    trail = srv.get_store().audit_trail("auth")
    actions = {(r["actor"], r["action"]) for r in trail}
    assert (email, "signup") in actions
    assert (email, "signin_failed") in actions
