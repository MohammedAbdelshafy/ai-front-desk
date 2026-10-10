"""Tests for the clinical store: tenant isolation, reviews, corrections, audit."""
import pytest

from ai_front_desk.clinical.store import ClinicalStore, TenantMismatchError


@pytest.fixture()
def store(tmp_path):
    s = ClinicalStore(tmp_path / "test.db")
    s.register_clinic("clinic-a", "Clinic A (synthetic)")
    s.register_clinic("clinic-b", "Clinic B (synthetic)")
    yield s
    s.close()


def _answers():
    return {"id.full_name": "Synth Patient", "med.taking_any": "No"}


def test_save_and_read_roundtrip(store):
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Synth Patient", _answers())
    sub = store.get_submission("clinic-a", sid)
    assert sub["answers"] == _answers()
    assert sub["bank_version"] == "1.0.0"
    assert sub["status"] == "submitted"


def test_cross_tenant_read_denied_and_audited(store):
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Synth Patient", _answers())
    with pytest.raises(TenantMismatchError):
        store.get_submission("clinic-b", sid)
    # the denied attempt is in clinic-b's audit trail
    trail = store.audit_trail("clinic-b", sid)
    assert any(a["action"] == "access.denied" for a in trail)


def test_list_submissions_scoped_to_tenant(store):
    store.save_submission("clinic-a", "dental-intake", "1.0.0", "P1", _answers())
    store.save_submission("clinic-b", "dental-intake", "1.0.0", "P2", _answers())
    assert [s["patient_ref"] for s in store.list_submissions("clinic-a")] == ["P1"]
    assert [s["patient_ref"] for s in store.list_submissions("clinic-b")] == ["P2"]


def test_review_recorded_and_status_updated(store):
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Synth Patient", _answers())
    store.record_review("clinic-a", sid, "Dr. Synth", "approved", "looks complete")
    sub = store.get_submission("clinic-a", sid)
    assert sub["status"] == "reviewed:approved"
    trail = store.audit_trail("clinic-a", sid)
    assert any(a["action"] == "submission.reviewed" and a["actor"] == "Dr. Synth"
               for a in trail)


def test_review_invalid_decision_rejected(store):
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Synth Patient", _answers())
    with pytest.raises(ValueError):
        store.record_review("clinic-a", sid, "Dr. Synth", "maybe")


def test_correction_preserves_original_and_audits(store):
    answers = {"id.full_name": "Synth Patient", "med.taking_any": "Yes",
               "med.list": "Old Med"}
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Synth Patient", answers)
    store.record_correction("clinic-a", sid, "med.list", "New Med 5mg",
                            "staff_verified", "Nurse Synth")
    # original submission answers are untouched (corrections are overlays)
    sub = store.get_submission("clinic-a", sid)
    assert sub["answers"]["med.list"] == "Old Med"
    corrs = store.list_corrections("clinic-a", sid)
    assert len(corrs) == 1
    assert corrs[0]["old_value"] == "Old Med"
    assert corrs[0]["new_value"] == "New Med 5mg"
    trail = store.audit_trail("clinic-a", sid)
    assert any(a["action"] == "answer.corrected" for a in trail)


def test_unregistered_clinic_cannot_create_submission(store):
    with pytest.raises(TenantMismatchError):
        store.save_submission("not-a-clinic", "dental-intake", "1.0.0",
                              "Demo Patient One", _answers())


def test_correction_chain_uses_previous_correction_as_old_value(store):
    answers = {"med.taking_any": "Yes", "med.list": "Original medication"}
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Demo Patient One", answers)
    store.record_correction("clinic-a", sid, "med.list", "First correction",
                             "staff_verified", "Nurse Demo")
    store.record_correction("clinic-a", sid, "med.list", "Second correction",
                             "staff_verified", "Nurse Demo")
    corrections = store.list_corrections("clinic-a", sid)
    assert corrections[0]["old_value"] == "Original medication"
    assert corrections[1]["old_value"] == "First correction"
    trail = store.audit_trail("clinic-a", sid)
    assert all("Original medication" not in event["detail"] for event in trail)


def test_correction_cross_tenant_denied(store):
    sid = store.save_submission("clinic-a", "dental-intake", "1.0.0",
                                "Synth Patient", _answers())
    with pytest.raises(TenantMismatchError):
        store.record_correction("clinic-b", sid, "med.list", "X",
                                "staff_verified", "Nurse Synth")
