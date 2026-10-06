"""E2E contract tests: launch the webhook dev server and verify the Meta
webhook contract (verify challenge, inbound parsing, dry-run reply payload).
Stdlib only."""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PORT = 18765
VERIFY_TOKEN = "test-token-xyz"
SENDER = "15551234567"


def get(path):
    url = "http://127.0.0.1:%d%s" % (PORT, path)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def post(path, obj):
    url = "http://127.0.0.1:%d%s" % (PORT, path)
    req = urllib.request.Request(
        url, data=json.dumps(obj).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def whatsapp_payload(sender, text, msg_id="wamid.test1"):
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "entry1", "changes": [{
                "value": {"messaging_product": "whatsapp",
                          "metadata": {"display_phone_number": "15550001111",
                                       "phone_number_id": "pnid"},
                          "messages": [{"from": sender, "id": msg_id,
                                        "timestamp": "1728000000",
                                        "type": "text",
                                        "text": {"body": text}}]},
                "field": "messages"}]}]}


def wait_for_server(proc, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("server exited early")
        try:
            get("/webhook")
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("server did not start in time")


def test_webhook_contract_e2e():
    env = dict(os.environ, VERIFY_TOKEN=VERIFY_TOKEN, DRY_RUN="1",
               PORT=str(PORT))
    proc = subprocess.Popen(
        [sys.executable, "-m", "ai_front_desk.webhook"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_server(proc)

        # (a) verification contract
        challenge = "challenge-abc-987"
        qs = urllib.parse.urlencode(
            {"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN,
             "hub.challenge": challenge})
        status, body = get("/webhook?" + qs)
        assert status == 200 and body == challenge, (status, body)

        qs_bad = urllib.parse.urlencode(
            {"hub.mode": "subscribe", "hub.verify_token": "wrong-token",
             "hub.challenge": challenge})
        status, _ = get("/webhook?" + qs_bad)
        assert status == 403, status

        # (b) inbound message + dry-run reply
        status, resp = post("/webhook", whatsapp_payload(SENDER, "hello"))
        assert status == 200 and resp.get("ok") is True, resp
        r0 = resp["results"][0]
        assert r0["sender"] == SENDER
        assert r0["stage"] == "qualify_name"
        assert "name" in r0["reply"].lower()
        assert r0["escalate"] is False
        payload = r0["sent"]["payload"]
        assert r0["sent"]["dry_run"] is True
        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == SENDER
        assert payload["text"]["body"] == r0["reply"]

        # multi-turn through the state machine
        for text, want_stage in [("Omar", "qualify_service"),
                                 ("I need cleaning", "qualify_urgency"),
                                 ("today please", "done")]:
            status, resp = post("/webhook", whatsapp_payload(SENDER, text))
            assert resp["results"][0]["stage"] == want_stage, (text, resp)

        # escalation keyword
        status, resp = post("/webhook",
                            whatsapp_payload("15559998888", "talk to a human"))
        r0 = resp["results"][0]
        assert r0["escalate"] is True and r0["stage"] == "escalate"
    finally:
        proc.terminate()
        proc.wait(timeout=10)
