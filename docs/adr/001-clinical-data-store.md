# ADR 001 — Clinical data store for local development

**Date:** 2026-10-11
**Status:** Accepted (development only)

## Context

The Mia Clinical Platform needs a place to persist intake submissions, reviews,
corrections, and audit events. The long-term candidate is Medplum (FHIR R4,
open-source core), but selecting a production clinical store requires a
security, contract, hosting, BAA, and tenant-isolation review that is out of
scope for the first working build.

## Decision

- For local development and demos: SQLite via `ai_front_desk/clinical/store.py`.
  - Tenant isolation enforced in every query (`clinic_id` filter) and verified
    by negative tests (cross-tenant reads raise `TenantMismatchError`).
  - Append-only audit log for submissions, reviews, corrections, and denied
    access attempts.
  - Synthetic data only. The demo server labels every page as non-HIPAA,
    non-production.
- FHIR R4-compatible representations are produced at the boundary:
  `Questionnaire` (question_bank.to_fhir_questionnaire) and
  `QuestionnaireResponse` (intake.to_fhir_questionnaire_response), so a future
  migration to Medplum or another FHIR store does not require re-modeling.
- Medplum remains the leading production candidate. Before any real patient
  data: verify FHIR version support, hosting model, BAA availability, data
  residency, backup/restore, tenant-isolation evidence, and dependency licenses.

## Consequences

- The dev store must never be described as HIPAA-compliant or production-ready.
- Migration path is explicit: the FHIR export functions are the contract.
- Do not build a home-grown EHR beyond this dev store.
