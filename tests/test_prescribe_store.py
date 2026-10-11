"""Tests for the prescribe store: tenant isolation, review states, audit."""
import pytest

from ai_front_desk.clinical.prescribe.store import PrescribeStore, TenantMismatchError


@pytest.fixture
def store(tmp_path):
    s = PrescribeStore(tmp_path / "t.sqlite3")
    yield s
    s.close()


def _patient(store, clinic="clinic-a", label="Demo Patient A"):
    return store.add_patient(
        clinic, label,
        allergies=[{"substance": "penicillin", "reaction": "rash", "recorded_at": "2026-10-11"}],
        conditions=["hypertension"],
        current_meds=[{"name": "warfarin", "dose": "5 mg daily"}],
    )


def _check(store, clinic="clinic-a", patient_id=None, verdict="RED"):
    pid = patient_id or _patient(store, clinic)
    intended = {"drug_name": "ibuprofen", "strength_mg": 400, "times_per_day": 3}
    flags = [{"severity": "red", "reason": "test", "source": "test", "rule_id": "nsaid-anticoagulant"}]
    return store.record_check(clinic, pid, "Dr. Test", intended, verdict, flags)


def test_patient_round_trip(store):
    pid = _patient(store)
    p = store.get_patient("clinic-a", pid)
    assert p["label"] == "Demo Patient A"
    assert p["allergies"][0]["substance"] == "penicillin"


def test_cross_tenant_patient_denied(store):
    pid = _patient(store, "clinic-a")
    with pytest.raises(TenantMismatchError):
        store.get_patient("clinic-b", pid)
    assert store.list_patients("clinic-b") == []


def test_red_check_requires_review_initially(store):
    cid = _check(store, verdict="RED")
    c = store.get_check("clinic-a", cid)
    assert c["review_state"] == "review_required"


def test_green_check_ready_for_review(store):
    cid = _check(store, verdict="GREEN")
    c = store.get_check("clinic-a", cid)
    assert c["review_state"] == "ready_for_review"


def test_review_state_transition_audited(store):
    cid = _check(store, verdict="RED")
    store.set_review_state("clinic-a", cid, "clinician_reviewed", "Dr. Test",
                           note="Switched to paracetamol.", actor="dr-test")
    c = store.get_check("clinic-a", cid)
    assert c["review_state"] == "clinician_reviewed"
    assert c["reviewed_by"] == "Dr. Test"
    assert c["reviewed_at"] is not None
    trail = store.audit_trail("clinic-a", cid)
    actions = [e["action"] for e in trail]
    assert "prescribe_check" in actions
    assert "prescribe_review" in actions


def test_review_state_rejects_unknown(store):
    cid = _check(store)
    with pytest.raises(ValueError):
        store.set_review_state("clinic-a", cid, "nonsense", "Dr. Test")


def test_cross_tenant_review_denied(store):
    cid = _check(store, "clinic-a")
    with pytest.raises(TenantMismatchError):
        store.set_review_state("clinic-b", cid, "clinician_reviewed", "Dr. Evil")


def test_check_history_lists_newest_first(store):
    pid = _patient(store)
    _check(store, patient_id=pid, verdict="GREEN")
    _check(store, patient_id=pid, verdict="RED")
    hist = store.check_history("clinic-a", pid)
    assert len(hist) == 2
    assert hist[0]["verdict"] == "RED"
    assert "review_state" in hist[0]
