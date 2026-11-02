"""Tests for the prescribing-safety check engine (assistive only)."""
from ai_front_desk.clinical.prescribe.checker import check_prescription


def _patient(**over):
    base = {
        "allergies": [],
        "no_known_allergies": True,
        "conditions": [],
        "current_meds": [],
        "reports": {},
    }
    base.update(over)
    return base


def test_clean_prescription_is_green():
    r = check_prescription(
        _patient(),
        {"drug_name": "amoxicillin", "strength_mg": 500, "times_per_day": 3},
    )
    assert r.verdict == "GREEN", r.to_dict()


def test_allergy_conflict_is_red_with_source():
    r = check_prescription(
        _patient(allergies=[{"substance": "penicillin", "reaction": "rash",
                             "recorded_at": "2026-10-02"}]),
        {"drug_name": "amoxicillin", "strength_mg": 500, "times_per_day": 3},
    )
    assert r.verdict == "RED"
    reds = [f for f in r.flags if f.severity == "red"]
    assert reds
    assert "patient record" in reds[0].source
    assert "penicillin" in reds[0].reason.lower()


def test_nsaid_warfarin_interaction_is_red_with_rule_id():
    r = check_prescription(
        _patient(current_meds=[{"name": "warfarin", "dose": "5 mg daily"}]),
        {"drug_name": "ibuprofen", "strength_mg": 400, "times_per_day": 3},
    )
    assert r.verdict == "RED"
    rule_flags = [f for f in r.flags if f.rule_id == "nsaid-anticoagulant"]
    assert rule_flags, [f.rule_id for f in r.flags]
    assert "reference v2" in rule_flags[0].source
    assert "2026-10-11" in rule_flags[0].source


def test_metronidazole_alcohol_is_red():
    r = check_prescription(
        _patient(reports={"alcohol_use": True}),
        {"drug_name": "metronidazole", "strength_mg": 400, "times_per_day": 3},
    )
    assert r.verdict == "RED"
    assert any(f.rule_id == "metronidazole-alcohol" for f in r.flags)


def test_tetracycline_pregnancy_is_red():
    r = check_prescription(
        _patient(conditions=["pregnancy"]),
        {"drug_name": "doxycycline", "strength_mg": 100, "times_per_day": 1},
    )
    assert r.verdict == "RED"


def test_dose_exceedance_is_red():
    r = check_prescription(
        _patient(),
        {"drug_name": "paracetamol", "strength_mg": 1000, "times_per_day": 5},
    )
    assert r.verdict == "RED"
    assert any("exceeds" in f.reason for f in r.flags)


def test_missing_allergy_data_is_never_green():
    r = check_prescription(
        _patient(allergies=[], no_known_allergies=False),  # unknown
        {"drug_name": "amoxicillin", "strength_mg": 500, "times_per_day": 3},
    )
    assert r.verdict == "CANNOT_VERIFY"
    assert any("Allergy history is not recorded" in f.reason for f in r.flags)


def test_unknown_drug_is_cannot_verify():
    r = check_prescription(_patient(), {"drug_name": "unobtainium"})
    assert r.verdict == "CANNOT_VERIFY"
    assert r.drug_key is None


def test_aspirin_allergy_nsaid_is_yellow():
    r = check_prescription(
        _patient(allergies=[{"substance": "aspirin", "reaction": "wheeze",
                             "recorded_at": "2026-01-01"}]),
        {"drug_name": "naproxen", "strength_mg": 250, "times_per_day": 2},
    )
    assert r.verdict == "YELLOW"


def test_clindamycin_carries_counsel_flag():
    r = check_prescription(
        _patient(),
        {"drug_name": "clindamycin", "strength_mg": 300, "times_per_day": 4},
    )
    assert r.verdict == "GREEN"
    assert any("diarrhoea" in f.reason for f in r.flags if f.severity == "info")


def test_alias_resolution():
    r = check_prescription(
        _patient(),
        {"drug_name": "Tylenol", "strength_mg": 500, "times_per_day": 4},
    )
    assert r.verdict == "GREEN"
    assert r.drug_key == "paracetamol"
