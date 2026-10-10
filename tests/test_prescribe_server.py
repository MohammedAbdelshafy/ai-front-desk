"""HTTP smoke tests for the Mia Dental OS demo server."""
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


def _get(base, path):
    """Returns (code, location-or-body): Location header on 3xx, body otherwise."""
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(base + path, method="GET")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers.get("Location", "")
        return e.code, e.read().decode()


def _post(base, path, fields):
    data = urllib.parse.urlencode(fields).encode()
    # don't follow the 303; check the redirect target instead
    class _NoRedirect2(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(_NoRedirect2)
    req = urllib.request.Request(base + path, data=data, method="POST")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "")


def test_landing_page_public(live_server):
    code, body = _get(live_server, "/")
    assert code == 200
    assert "Mia Dental OS" in body
    assert "Mia Dental Prescribing Copilot" in body
    assert "7-day" in body


def test_app_locked_before_trial(live_server):
    code, _ = _get(live_server, "/app/patients")
    assert code == 303  # redirected to trial/subscribe


def test_trial_activation_unlocks(live_server):
    code, loc = _post(live_server, "/api/trial/activate", {})
    assert code == 303
    code, body = _get(live_server, "/app/patients")
    assert code == 200
    assert "Prescribing Copilot" in body


def test_sample_flow_end_to_end(live_server):
    code, loc = _post(live_server, "/api/sample-patient?clinic=x", {})
    assert code == 303 and "id=pat_" in loc
    code, loc = _post(live_server, "/api/sample-check?clinic=x", {})
    assert code == 303 and "id=chk_" in loc
    # The redirect target must be a well-formed check URL — regression guard:
    # following it must resolve to the recorded check (HTTP 200), never 404.
    assert re.fullmatch(
        r"/app/check\?clinic=demo-smile-arts&id=chk_[a-f0-9]{12}", loc
    ), f"unexpected redirect target: {loc}"
    code, body = _get(live_server, loc)
    assert code == 200
    assert "RED" in body
    assert "reference v2" in body
    assert "warfarin" in body.lower() or "nsaid" in body.lower()


def test_review_records_clinician_conclusion(live_server):
    _, loc = _post(live_server, "/api/sample-check?clinic=x", {})
    check_id = loc.split("id=")[1]
    code, _ = _post(
        live_server, "/api/review?clinic=x",
        {"check_id": check_id, "state": "clinician_reviewed",
         "by": "Dr. Test", "note": "Switched to paracetamol."},
    )
    assert code == 303
    code, body = _get(live_server, loc)
    assert code == 200
    assert "clinician reviewed" in body
    assert "paracetamol" in body


def test_reference_page_lists_drugs(live_server):
    code, body = _get(live_server, "/app/reference")
    assert code == 200
    assert "Amoxicillin" in body
    assert "reference v2 (2026-10-11)" in body


def test_wizard_guided_flow(live_server):
    _post(live_server, "/api/trial/activate", {})  # pass the trial gate
    # start wizard (no patient -> will create demo patient at finish)
    code, loc = _get(live_server, "/app/wizard/start")
    assert code == 303 and "/app/wizard/wz_" in loc and loc.endswith("/indication")
    token = loc.split("/app/wizard/")[1].split("/")[0]
    # step 1: indication
    code, loc = _post(live_server, f"/api/wizard/{token}/indication",
                      {"indication": "infection", "indication_notes": "abscess"})
    assert code == 303 and loc.endswith("/factors")
    # step 2: factors
    code, loc = _post(live_server, f"/api/wizard/{token}/factors",
                      {"age_band": "31–50", "pregnancy": "no", "lactation": "no",
                       "renal": "no", "hepatic": "no", "weight_kg": ""})
    assert code == 303 and loc.endswith("/allergies")
    # step 3: allergies
    code, loc = _post(live_server, f"/api/wizard/{token}/allergies",
                      {"allergies": "penicillin | rash", "latex_allergy": "no",
                       "anesthesia_history": ""})
    assert code == 303 and loc.endswith("/medications")
    # step 4: meds (none)
    code, loc = _post(live_server, f"/api/wizard/{token}/medications", {"meds": ""})
    assert code == 303 and loc.endswith("/conditions")
    # step 5: conditions (none)
    code, loc = _post(live_server, f"/api/wizard/{token}/conditions", {})
    assert code == 303 and loc.endswith("/summary")
    # summary shows missing-info handling
    code, body = _get(live_server, loc)
    assert code == 200 and "Summary" in body
    # choose page shows indication reference
    code, body = _get(live_server, f"/app/wizard/{token}/choose")
    assert code == 200 and "Amoxicillin" in body and "reference v2" in body
    # finish with the dentist's own choice -> RED via penicillin allergy
    code, loc = _post(live_server, f"/api/wizard/{token}/finish",
                      {"drug_name": "amoxicillin", "strength_mg": "500",
                       "times_per_day": "3", "dentist": "Dr. Test"})
    assert code == 303 and "/app/check" in loc
    code, body = _get(live_server, loc)
    assert code == 200 and "RED" in body and "penicillin" in body.lower()


def test_upgrades_show_exact_tier_names(live_server):
    code, body = _get(live_server, "/app/upgrades")
    assert code == 200
    assert "Mia Dental Practice" in body
    assert "Mia Dental Automation" in body
    assert "Mia Dental OS Pro" in body
