"""Tests for the append-only, clinic-scoped operational event ledger.

The ledger is deliberately count-only: no patient name, health information, message
body, phone number or free-form note belongs in an operational metric event.
"""
import time
import uuid

import pytest

from ai_front_desk.clinical.store import (
    ClinicalStore,
    OperationalEventConflictError,
    TenantMismatchError,
)


@pytest.fixture()
def store(tmp_path):
    s = ClinicalStore(tmp_path / "events.db")
    s.register_clinic("clinic-a", "Clinic A (synthetic)")
    s.register_clinic("clinic-b", "Clinic B (synthetic)")
    yield s
    s.close()


def new_key():
    return str(uuid.uuid4())


def test_records_count_only_event_and_audits_without_patient_details(store):
    key = new_key()
    event_id = store.record_operational_event(
        "clinic-a", "missed_call", source="phone",
        idempotency_key=key, actor="staff",
    )

    events = store.list_operational_events("clinic-a")
    assert len(events) == 1
    assert events[0]["event_id"] == event_id
    assert events[0]["event_type"] == "missed_call"
    assert events[0]["source"] == "phone"
    assert events[0]["actor"] == "staff"
    assert "patient_name" not in events[0]
    assert "message_body" not in events[0]

    trail = store.audit_trail("clinic-a")
    event_audits = [item for item in trail if item["action"] == "operational_event.recorded"]
    assert len(event_audits) == 1
    assert key not in event_audits[0]["detail"]


def test_idempotent_replay_does_not_duplicate_event(store):
    key = new_key()
    first = store.record_operational_event(
        "clinic-a", "appointment_booked", source="staff",
        idempotency_key=key,
    )
    second = store.record_operational_event(
        "clinic-a", "appointment_booked", source="staff",
        idempotency_key=key,
    )

    assert first == second
    assert len(store.list_operational_events("clinic-a")) == 1


def test_reused_idempotency_key_with_different_payload_is_rejected(store):
    key = new_key()
    store.record_operational_event(
        "clinic-a", "missed_call", source="phone", idempotency_key=key,
    )
    with pytest.raises(OperationalEventConflictError):
        store.record_operational_event(
            "clinic-a", "appointment_booked", source="staff",
            idempotency_key=key,
        )


def test_unknown_clinic_cannot_write_operational_event(store):
    with pytest.raises(TenantMismatchError):
        store.record_operational_event(
            "unregistered", "missed_call", source="phone",
            idempotency_key=new_key(),
        )


def test_invalid_event_type_source_and_idempotency_key_are_rejected(store):
    with pytest.raises(ValueError, match="unknown operational event type"):
        store.record_operational_event(
            "clinic-a", "diagnose_patient", source="staff", idempotency_key=new_key(),
        )
    with pytest.raises(ValueError, match="unknown operational event source"):
        store.record_operational_event(
            "clinic-a", "missed_call", source="instagram-dm", idempotency_key=new_key(),
        )
    with pytest.raises(ValueError, match="idempotency key"):
        store.record_operational_event(
            "clinic-a", "missed_call", source="phone",
            idempotency_key="patient:Jane Doe:toothache",
        )


@pytest.mark.parametrize(
    "key",
    [
        "15551234567",
        "demo-v1:2026-11-01:clinic-a:missed_call:1",
        "patient:Jane Doe:toothache",
    ],
)
def test_rejects_non_uuid_or_identifying_idempotency_keys(store, key):
    with pytest.raises(ValueError, match="idempotency key"):
        store.record_operational_event(
            "clinic-a", "missed_call", source="phone", idempotency_key=key,
        )


@pytest.mark.parametrize("actor", ["Dr Jane Smith", "owner@example.com", "+1-555-123-4567", "staff-demo"])
def test_rejects_free_form_or_identifying_actor_values(store, actor):
    with pytest.raises(ValueError, match="actor"):
        store.record_operational_event(
            "clinic-a", "missed_call", source="phone",
            idempotency_key=new_key(), actor=actor,
        )


def test_legacy_free_form_actor_is_redacted_when_events_are_listed(store):
    key = new_key()
    now = time.time()
    store._db.execute(
        """INSERT INTO operational_events
           (event_id, clinic_id, event_type, source, idempotency_key,
            occurred_at, created_at, actor)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("evt_legacy", "clinic-a", "missed_call", "phone", key, now, now, "Dr Jane Smith"),
    )
    store._db.execute(
        """INSERT INTO audit_log
           (clinic_id, actor, action, target, detail, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("clinic-a", "Dr Jane Smith", "operational_event.recorded",
         "evt_legacy", "type=missed_call; source=phone", now),
    )
    store._db.commit()

    events = store.list_operational_events("clinic-a")
    audit = store.audit_trail("clinic-a", target="evt_legacy")

    assert len(events) == 1
    assert events[0]["actor"] == "unknown"
    assert len(audit) == 1
    assert audit[0]["actor"] == "unknown"


def test_daily_scorecard_is_scoped_and_uses_event_occurrence_window(store):
    now = time.time()
    start = now - 3600
    end = now + 60
    store.record_operational_event(
        "clinic-a", "missed_call", source="phone",
        idempotency_key=new_key(), occurred_at=now - 600,
    )
    store.record_operational_event(
        "clinic-a", "missed_call_recovered", source="phone",
        idempotency_key=new_key(), occurred_at=now - 300,
    )
    store.record_operational_event(
        "clinic-a", "appointment_booked", source="staff",
        idempotency_key=new_key(), occurred_at=now - 7200,
    )
    store.record_operational_event(
        "clinic-b", "missed_call", source="phone",
        idempotency_key=new_key(), occurred_at=now - 500,
    )

    report = store.daily_scorecard("clinic-a", start, end)

    assert report["clinic_id"] == "clinic-a"
    assert report["event_count"] == 2
    assert report["counts"]["missed_call"] == 1
    assert report["counts"]["missed_call_recovered"] == 1
    assert report["counts"].get("appointment_booked", 0) == 0
    assert report["synthetic_event_count"] == 0
    assert report["limitations"]


def test_scorecard_marks_synthetic_events_separately(store):
    store.record_operational_event(
        "clinic-a", "intake_completed", source="demo_synthetic",
        idempotency_key=new_key(), occurred_at=time.time(),
        actor="demo_synthetic",
    )

    report = store.daily_scorecard("clinic-a", time.time() - 60, time.time() + 60)

    assert report["event_count"] == 1
    assert report["synthetic_event_count"] == 1
    assert report["data_mode"] == "synthetic_demo"
