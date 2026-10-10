# Dental AI Clinic Assistant (MVP module)

This package adds a **dental-specific administrative workflow** to AI Front Desk. It is intentionally not a clinical decision support product. It is not yet a managed or production-ready dental service.

## Module
- `ai_front_desk/dental_logic.py`: pure, testable appointment-request/intake logic, clinic-approved FAQ answers, conservative human escalation, explicit follow-up permission, and clinic-tenant mismatch fail-closed behavior.
- `tests/test_dental_logic.py`: regression tests for the module.

## Demo usage
```python
from ai_front_desk.dental_logic import ClinicConfig, new_dental_session, process_dental_message

clinic = ClinicConfig(
    clinic_id="demo-clinic",
    name="Demo Dental",
    timezone="America/Chicago",
    phone="+15551234567",
    address="DEMO ONLY",
    hours="DEMO ONLY",
    approved_faqs={"hours": "DEMO: hours must be supplied and approved by clinic staff."},
)

state = new_dental_session("synthetic-demo-sender", clinic.clinic_id)
state, reply, handoff, stage = process_dental_message(state, "hello", clinic)
print(reply, stage, handoff)
```

All identity/contact/location data in this example is synthetic. Do not replace it with a real clinic configuration until approved by that clinic.

## Important boundary
This module only computes replies and state. It does not send messages, schedule appointments, persist patient data, or call any external service. The current WhatsApp webhook and n8n workflow remain reference implementations and must be hardened before clinical production: persistent tenant-scoped state, webhook signature verification, message deduplication, robust event parsing, controlled outbox, clinic-level feature flags, privacy/security review, staff queue, retention/deletion policy, approved vendor contracts, and an approved live deployment plan.

## Pilot principle
Sell and validate the smallest workflow with a real clinic before adding integrations, autonomous voice, recall campaigns, clinical recommendations, or multi-location rollout.
