"""Tests for the append-only, clinic-scoped operational event ledger.

The ledger is deliberately count-only: no patient name, health information, message
body, phone number or free-form note belongs in an operational metric event.
"""
import time

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


def test_records_count_only_event_and_audits_without_patient_details(store):
    event_id = store.record_operational_event(
        "clinic-a", "missed_call", source="phone",
        idempotency_key="phone-event-001", actor="staff-demo",
    )

    events = store.list_operational_events("clinic-a")
    assert len(events) == 1
    assert events[0]["event_id"] == event_id
    assert events[0]["event_type"] == "missed_call"
    assert events[0]["source"] == "phone"
    assert "patient_name" not in events[0]
    assert "message_body" not in events[0]

    trail = store.audit_trail("clinic-a")
    event_audits = [item for item in trail if item["action"] == "operational_event.recorded"]
    assert len(event_audits) == 1
    assert "phone-event-001" not in event_audits[0]["detail"]


def test_idempotent_replay_does_not_duplicate_event(store):
    first = store.record_operational_event(
        "clinic-a", "appointment_booked", source="staff",
        idempotency_key="booking-abc",
    )
    second = store.record_operational_event(
        "clinic-a", "appointment_booked", source="staff",
        idempotency_key="booking-abc",
    )

    assert first == second
    assert len(store.list_operational_events("clinic-a")) == 1


def test_reused_idempotency_key_with_different_payload_is_rejected(store):
    store.record_operational_event(
        "clinic-a", "missed_call", source="phone", idempotency_key="event-1",
    )
    with pytest.raises(OperationalEventConflictError):
        store.record_operational_event(
            "clinic-a", "appointment_booked", source="staff",
            idempotency_key="event-1",
        )


def test_unknown_clinic_cannot_write_operational_event(store):
    with pytest.raises(TenantMismatchError):
        store.record_operational_event(
            "unregistered", "missed_call", source="phone",
            idempotency_key="event-unknown-clinic",
        )


def test_invalid_event_type_source_and_idempotency_key_are_rejected(store):
    with pytest.raises(ValueError, match="unknown operational event type"):
        store.record_operational_event(
            "clinic-a", "diagnose_patient", source="staff", idempotency_key="bad-1",
        )
    with pytest.raises(ValueError, match="unknown operational event source"):
        store.record_operational_event(
            "clinic-a", "missed_call", source="instagram-dm", idempotency_key="bad-2",
        )
    with pytest.raises(ValueError, match="idempotency key"):
        store.record_operational_event(
            "clinic-a", "missed_call", source="phone",
            idempotency_key="patient:Jane Doe:toothache",
        )


def test_daily_scorecard_is_scoped_and_uses_event_occurrence_window(store):
    now = time.time()
    start = now - 3600
    end = now + 60
    store.record_operational_event(
        "clinic-a", "missed_call", source="phone",
        idempotency_key="a-missed", occurred_at=now - 600,
    )
    store.record_operational_event(
        "clinic-a", "missed_call_recovered", source="phone",
        idempotency_key="a-recovered", occurred_at=now - 300,
    )
    store.record_operational_event(
        "clinic-a", "appointment_booked", source="staff",
        idempotency_key="a-booked", occurred_at=now - 7200,
    )
    store.record_operational_event(
        "clinic-b", "missed_call", source="phone",
        idempotency_key="b-missed", occurred_at=now - 500,
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
    now = time.time()
    store.record_operational_event(
        "clinic-a", "intake_completed", source="demo_synthetic",
        idempotency_key="demo-intake-1", occurred_at=now,
    )

    report = store.daily_scorecard("clinic-a", now - 60, now + 60)

    assert report["event_count"] == 1
    assert report["synthetic_event_count"] == 1
    assert report["data_mode"] == "synthetic_demo"
