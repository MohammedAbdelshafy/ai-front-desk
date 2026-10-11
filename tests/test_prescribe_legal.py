"""Legal/compliance pages, signup acceptance, and recorded consent."""
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
    tmp = tmp_path_factory.mktemp("legal")
    srv.DB_PATH = tmp / "l.sqlite3"
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
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def _signup_fields(**over):
    f = {
        "name": "Dr. Legal Test",
        "email": "legal-test@riveradental.example",
        "clinic_name": "Rivera Legal Dental",
        "password": "correct-horse-20",
        "confirm": "correct-horse-20",
        "accept_terms": "1",
        "accept_privacy": "1",
    }
    f.update(over)
    return f


def test_legal_index_lists_all_docs(live_server):
    c = _client()
    code, body = _get(c, live_server, "/legal")
    assert code == 200
    for slug in ("privacy", "terms", "security", "intended-use", "refund", "retention"):
        assert f"/legal/{slug}" in body


def test_short_legal_routes_return_200_with_draft_header(live_server):
    c = _client()
    for path, title in (("/privacy", "Privacy Policy"),
                        ("/terms", "Terms of Service"),
                        ("/security", "Security Policy")):
        code, body = _get(c, live_server, path)
        assert code == 200, path
        assert title in body
        assert "DRAFT v0.1" in body
        assert "requires qualified legal review" in body


def test_nested_legal_routes_return_200(live_server):
    c = _client()
    for path, title in (("/legal/intended-use", "Intended Use"),
                        ("/legal/refund", "Refund"),
                        ("/legal/retention", "Retention")):
        code, body = _get(c, live_server, path)
        assert code == 200, path
        assert title in body


def test_unknown_legal_slug_404(live_server):
    c = _client()
    code, _ = _get(c, live_server, "/legal/nope")
    assert code == 404


def test_legal_docs_make_no_false_claims(live_server):
    """The drafts must never claim compliance/certification we don't have."""
    c = _client()
    code, body = _get(c, live_server, "/privacy")
    assert code == 200
    low = body.lower()
    assert "hipaa-compliant" not in low or "not" in low.split("hipaa-compliant")[0][-120:]
    assert "not hipaa-compliant" in low or "not currently hipaa-compliant" in low


def test_footer_links_on_public_pages(live_server):
    c = _client()
    for path in ("/", "/signup", "/signin"):
        code, body = _get(c, live_server, path)
        assert code == 200, path
        assert "href='/privacy'" in body
        assert "href='/terms'" in body
        assert "href='/security'" in body
        assert "href='/legal'" in body


def test_signup_page_has_acceptance_checkboxes(live_server):
    c = _client()
    code, body = _get(c, live_server, "/signup")
    assert code == 200
    assert "name='accept_terms'" in body
    assert "name='accept_privacy'" in body
    assert "/terms" in body and "/privacy" in body


def test_signup_rejected_without_acceptance(live_server):
    c = _client()
    cases = [
        ("no-terms", {"accept_terms"}),
        ("no-privacy", {"accept_privacy"}),
        ("no-both", {"accept_terms", "accept_privacy"}),
    ]
    for tag, drop in cases:
        fields = _signup_fields(email=f"{tag}@riveradental.example")
        for k in drop:
            fields.pop(k)
        code, body = _post(c, live_server, "/api/signup", fields)
        assert code == 400, tag
        assert "Terms of Service" in body or "Privacy Policy" in body
        assert srv.get_accounts().get_account_by_email(fields["email"]) is None


def test_signup_records_acceptance_version(live_server):
    c = _client()
    fields = _signup_fields(email="accept-ok@riveradental.example")
    code, _ = _post(c, live_server, "/api/signup", fields)
    assert code in (303, 200), code
    acct = srv.get_accounts().get_account_by_email(fields["email"])
    assert acct is not None
    assert acct["legal_accepted_version"] == srv.LEGAL_VERSION
    assert acct["legal_accepted_at"] and acct["legal_accepted_at"] > 0
