"""Unit tests for the front-desk qualification state machine."""
from ai_front_desk import new_session, process_message


def run_turns(messages):
    st = new_session("15551234567")
    out = []
    for m in messages:
        st, reply, esc, stage = process_message(st, m)
        out.append((stage, esc, reply))
    return st, out


def test_full_qualification_flow():
    st, out = run_turns(["hi", "Layla", "consulting", "this week"])
    stages = [s for s, _, _ in out]
    assert stages == ["qualify_name", "qualify_service", "qualify_urgency", "done"]
    assert st["name"] == "Layla"
    assert st["service"] == "consulting"
    assert st["urgency"] == "this week"
    assert not any(esc for _, esc, _ in out)


def test_greet_asks_for_name():
    _, out = run_turns(["hello"])
    assert "name" in out[0][2].lower()


def test_faq_price_inline_keeps_stage():
    st = new_session("1")
    st, _, _, _ = process_message(st, "hi")
    st, _, _, _ = process_message(st, "Layla")  # now at qualify_service
    st2, reply, esc, stage2 = process_message(st, "how much does it cost?")
    assert stage2 == "qualify_service"
    assert "pricing" in reply.lower()
    assert not esc


def test_escalation_keyword_any_stage():
    st = new_session("1")
    st2, reply, esc, stage = process_message(st, "let me talk to a human")
    assert esc is True
    assert stage == "escalate"
    assert "team" in reply.lower()


def test_two_failed_service_parses_escalate():
    st = new_session("1")
    st, _, _, _ = process_message(st, "hi")
    st, _, _, _ = process_message(st, "Layla")
    st, _, esc1, stage1 = process_message(st, "blargh")
    assert not esc1 and stage1 == "qualify_service"
    st, _, esc2, stage2 = process_message(st, "still blargh")
    assert esc2 is True and stage2 == "escalate"


def test_empty_message_reprompts():
    st = new_session("1")
    st2, reply, esc, stage = process_message(st, "   ")
    assert not esc
    assert "repeat" in reply.lower()


def test_done_stage_offers_human():
    st, _ = run_turns(["hi", "Omar", "cleaning", "today"])
    st2, reply, esc, stage = process_message(st, "anything else?")
    assert stage == "done" and not esc
    assert "human" in reply.lower()


def test_urgency_classification():
    for text, want in [("today please", "today"), ("URGENT!", "today"),
                      ("this week", "this week"), ("just looking", "low")]:
        st = new_session("1")
        for m in ["hi", "Sam", "support"]:
            st, _, _, _ = process_message(st, m)
        st, _, _, stage = process_message(st, text)
        assert stage == "done" and st["urgency"] == want, (text, st)


def test_state_is_json_serializable():
    import json
    st = new_session("15551234567")
    st, _, _, _ = process_message(st, "hi")
    json.dumps(st)
