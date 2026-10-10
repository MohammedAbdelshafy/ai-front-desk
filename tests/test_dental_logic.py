from ai_front_desk.dental_logic import (
    ClinicConfig, new_dental_session, process_dental_message, URGENT_HANDOFF_TEXT,
)


def config():
    return ClinicConfig(
        clinic_id="demo-clinic",
        name="Demo Dental",
        timezone="America/Chicago",
        phone="+15551234567",
        address="DEMO ONLY",
        hours="DEMO ONLY",
        approved_faqs={
            "hours": "DEMO: clinic hours are configured by clinic staff.",
            "parking": "DEMO: use the parking instructions approved by the clinic.",
        },
    )


def turn(state, text, cfg=None):
    return process_dental_message(state, text, cfg or config())


def test_welcome_is_clinic_specific_and_not_generic():
    state = new_dental_session("test-sender", "demo-clinic")
    state, reply, handoff, stage = turn(state, "hello")
    assert "Demo Dental" in reply
    assert stage == "collect_intent"
    assert not handoff


def test_no_unapproved_hours_or_prices_are_invented():
    state = new_dental_session("s", "demo-clinic")
    state, _, _, _ = turn(state, "hello")
    _, reply, _, _ = turn(state, "What are your hours?", cfg=config_without_faq())
    assert "Monday to Saturday" not in reply
    assert "9:00 to 18:00" not in reply


def config_without_faq():
    cfg = config()
    return ClinicConfig(
        clinic_id=cfg.clinic_id,
        name=cfg.name,
        timezone=cfg.timezone,
        phone=cfg.phone,
        address=cfg.address,
        hours=cfg.hours,
        services=cfg.services,
        languages=cfg.languages,
        approved_faqs={},
        handoff_message=cfg.handoff_message,
    )


def test_approved_faq_is_returned_exactly():
    state = new_dental_session("s", "demo-clinic")
    state, _, _, _ = turn(state, "hello")
    _, reply, handoff, _ = turn(state, "What are your hours?")
    assert reply == "DEMO: clinic hours are configured by clinic staff."
    assert not handoff


def test_explicit_human_request_always_handoffs():
    _, _, handoff, stage = turn(new_dental_session("s", "demo-clinic"), "please speak to a human")
    assert handoff is True
    assert stage == "handoff"


def test_clinical_concern_never_gets_diagnosis():
    _, reply, handoff, stage = turn(new_dental_session("s", "demo-clinic"), "My toothache is severe")
    assert handoff is True
    assert stage == "clinical_handoff"
    assert "not a clinician" in reply
    assert "you have" not in reply.lower()


def test_tenant_mismatch_fails_closed():
    state = new_dental_session("s", "clinic-a")
    state, _, handoff, stage = process_dental_message(state, "hello", config())
    assert handoff is True
    assert stage == "handoff"
    assert state["clinic_id"] == "demo-clinic"
    assert state["handoff_required"] is True


def test_appointment_request_never_claims_booking_confirmation():
    state = new_dental_session("s", "demo-clinic")
    for msg in ["hello", "I'd like a cleaning", "next Thursday", "WhatsApp", "yes"]:
        state, reply, handoff, stage = turn(state, msg)
    assert handoff
    assert stage == "handoff"
    assert "not a confirmed appointment" in reply


def test_followup_permission_is_explicit():
    state = new_dental_session("s", "demo-clinic")
    for msg in ["hello", "checkup", "tomorrow", "phone", "no"]:
        state, _, handoff, stage = turn(state, msg)
    assert not handoff
    assert state["consent_to_follow_up"] is False


def test_session_serializable():
    import json
    state = new_dental_session("s", "demo-clinic")
    state, _, _, _ = turn(state, "hello")
    json.dumps(state)


def test_handoff_state_stays_handed_off():
    state = new_dental_session("s", "demo-clinic")
    state, _, handoff, stage = turn(state, "please speak to a human")
    assert handoff and stage == "handoff"
    state, _, handoff, stage = turn(state, "what are your hours?")
    assert handoff and stage == "handoff"
    assert state["handoff_required"] is True
