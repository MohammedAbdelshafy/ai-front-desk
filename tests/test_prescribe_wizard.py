"""Tests for the guided question wizard (context gathering, never prescribing)."""
from ai_front_desk.clinical.prescribe import wizard
from ai_front_desk.clinical.prescribe.checker import check_prescription


def _state(**over):
    s = wizard.new_wizard("clinic-a")
    s.update(over)
    return s


def test_wizard_prefills_from_patient():
    patient = {
        "patient_id": "pat_abc",
        "label": "Demo Patient A",
        "allergies": [{"substance": "penicillin", "reaction": "rash", "recorded_at": "2026-10-11"}],
        "conditions": ["hypertension"],
        "current_meds": [{"name": "warfarin", "dose": "5 mg daily"}],
        "no_known_allergies": False,
    }
    s = wizard.new_wizard("clinic-a", patient)
    assert s["allergies"][0]["substance"] == "penicillin"
    assert s["meds"][0]["name"] == "warfarin"
    assert s["patient_id"] == "pat_abc"


def test_missing_info_flags_unknowns():
    s = _state()  # nothing answered
    flags = wizard.missing_info_flags(s)
    reasons = " ".join(f["reason"] for f in flags)
    assert "allergy history not recorded" in reasons.lower()
    assert "Pregnancy status unknown" in reasons
    assert "Renal status unknown" in reasons
    assert all(f["severity"] == "info" for f in flags)


def test_missing_info_flags_clear_when_answered():
    s = _state(
        allergies=[{"substance": "penicillin", "reaction": "rash", "recorded_at": "x"}],
        factors={"pregnancy": "no", "renal": "no", "age_band": "31–50",
                 "lactation": "no", "hepatic": "no", "weight_kg": ""},
        indication="infection",
    )
    assert wizard.missing_info_flags(s) == []


def test_build_patient_context_merges_factors():
    s = _state(factors={"pregnancy": "yes", "renal": "yes", "hepatic": "no",
                        "age_band": "", "lactation": "", "weight_kg": ""},
               latex_allergy="yes")
    ctx = wizard.build_patient_context(s)
    assert "pregnancy" in ctx["conditions"]
    assert "renal impairment" in ctx["conditions"]
    assert "liver disease" not in ctx["conditions"]
    assert any(a["substance"] == "latex" for a in ctx["allergies"])


def test_wizard_context_drives_checker_red():
    s = _state(
        allergies=[{"substance": "penicillin", "reaction": "rash", "recorded_at": "2026-10-11"}],
        factors={"pregnancy": "no", "renal": "no", "age_band": "", "lactation": "",
                 "hepatic": "", "weight_kg": ""},
        indication="infection",
    )
    ctx = wizard.build_patient_context(s)
    r = check_prescription(ctx, {"drug_name": "amoxicillin", "strength_mg": 500,
                                 "times_per_day": 3})
    assert r.verdict == "RED"


def test_indication_options_cover_all():
    opts = dict(wizard.indication_options())
    assert set(opts) == {"infection", "prophylaxis", "post_op_pain", "anxiety", "other"}


def test_sessions_are_server_side_and_isolated():
    ws = wizard.WizardSessions()
    a = ws.create("clinic-a")
    b = ws.create("clinic-b")
    assert a["token"] != b["token"]
    assert ws.get(a["token"])["clinic_id"] == "clinic-a"
    assert ws.get("wz_deadbeef1234") is None
    ws.update(a["token"], {"indication": "infection"})
    assert ws.get(a["token"])["indication"] == "infection"
    assert ws.get(b["token"])["indication"] == ""
