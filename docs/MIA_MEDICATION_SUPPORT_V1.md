# Mia medication review scaffold v1

**Status: engineering prototype, clinician review required, no medication entries enabled.**

This work adds a shared, deterministic medication-review engine for the Mia dental and gynecology projects. It is a foundation for transparent clinician decision support, not a production clinical system.

## Where the code lives

- `ai_front_desk/clinical/medication_support.py`: catalogue loading and rule-based filtering.
- `ai_front_desk/clinical/medication_catalog_v1.json`: intentionally draft and empty central catalogue.
- `ai_front_desk/clinical/specialty_packs/dentistry_medication_v1.json`: dental scope and approval checklist.
- `ai_front_desk/clinical/specialty_packs/gynecology_medication_v1.json`: gynecology scope and approval checklist.
- `ai_front_desk/clinical/server.py`: local synthetic demo page at `/medication-review?clinic=demo-smile-arts` and JSON endpoint `POST /api/medication-review`.
- `tests/test_medication_support.py` and `tests/test_medication_review_server.py`: rule-contract and HTTP smoke tests.

The existing local demo starts with:

```bash
python -m pip install -e .
python -m ai_front_desk.clinical.server
```

Open `http://127.0.0.1:8766/medication-review?clinic=demo-smile-arts`. The server is intentionally loopback-only. Use only fictional test cases. The review endpoint does not persist the submission or create, sign, or transmit an order.

## Current behaviour

The engine:

1. Accepts only the configured specialty values `dentistry` or `gynecology`.
2. Requires an explicit clinician-entered diagnosis code and matches it exactly. It does not infer the diagnosis from symptoms or match fuzzy text.
3. Requires age, clinician-reviewed allergies and medication reconciliation before evaluating options.
4. Requires gynecology pregnancy and lactation context to be explicitly established or marked not applicable by the clinician. Unknown status blocks the review.
5. Returns an entry only when the catalogue and individual source metadata are approved and within the review period, and specialty/diagnosis match exactly.
6. Withholds an entry when a configured patient factor is missing, a configured contraindication or allergy term matches, a configured medication interaction matches, or the patient's age is outside the entry's reviewed population.
7. Includes teaching topics and source provenance for a clinician's independent review. It does not rank one “best” medicine, calculate a new dose, diagnose, prescribe, or transmit an order.

**No candidate returned is not a recommendation to withhold treatment.** It may simply mean the catalogue has no matching entry, the entry is out of date, or required context is missing. The clinician must continue using approved clinical guidance.

## Catalogue contract

The catalogue is empty and `status: draft`. Its loader exposes zero entries unless the catalogue's top-level status is `approved`. Each entry additionally requires:

- the intended specialty and exact diagnosis codes;
- the reviewed patient population and required patient facts;
- explicit rules for configured contraindications, allergy terms and medication interactions;
- teaching fields for rationale, mechanism, evidence, alternatives, adverse effects, serious warnings, reproductive safety, monitoring, counseling and official-label dosing context;
- source title, HTTPS URL, jurisdiction, source type, version, effective date, named reviewer, review date, review due date and `review_status: approved`.

These are engineering gates, not proof that the rule set is medically complete. Exact-name interaction matching only tests explicit rules in this catalogue; it is not a complete drug-interaction database, and lack of a warning does not establish safety. The UI must never imply otherwise.

## Source registry and clinical governance

Before adding real content, select the jurisdiction and legal data-use terms. Candidate authoritative source types include current official product labeling (for example, DailyMed and the FDA's openFDA drug-label interface), specialty-specific professional guidelines and an interaction resource licensed for the intended use. They are inputs to clinician-authored entries, not automatic approval. Verify the currentness, scope, completeness, and redistribution rights of each source.

Each entry must be reviewed by a practicing clinician qualified in the relevant specialty and by a qualified medication-safety reviewer. Gynecology entries additionally require reproductive-safety review. Create evaluation cases for contraindications, common and serious interactions, missing factors, children, pregnancy/lactation, renal/hepatic impairment, comorbidities, conflicting source statements, and stale references. Store the provenance and clinician approval with a versioned release. Do not populate the catalogue with generated drug advice or unreviewed web content.

## Production blockers

This feature is not ready for real patient data or clinical deployment. The existing repository is a local demo, not an EHR or managed medical service. The following remain required:

- qualified clinical and pharmacy review of the specialty packs and each medication entry;
- jurisdiction-specific intended-use and medical-device/CDS regulatory review, including legal review before marketing;
- authenticated users, least privilege, clinic tenant isolation, durable audit trails, retention/deletion controls, encryption, secret management and independent security/privacy testing;
- a trusted, licensed knowledge/interaction source pipeline with update alerts, versioning, rollback, attribution and licence review;
- validation of clinical rules and end-to-end tests with representative edge cases;
- clinician sign-off, source display, uncertainty display, and operational incident/escalation workflows.

The FDA's January 2026 Clinical Decision Support Software guidance is a relevant starting point for a U.S. product, not a blanket approval. Regulatory classification depends on actual functionality, intended users, intended use, and whether a clinician can independently review the basis for recommendations. Requirements differ by market; obtain qualified advice for the target jurisdiction.

## Explicit non-goals

- autonomous diagnosis;
- autonomous “best medication” selection;
- autonomous prescription signing or transmission;
- patient-directed changes to medication;
- claims of clinical validation, HIPAA compliance, patient-time savings, safety, accuracy, or treatment outcome;
- using actual patient data in the demo.

A safe next release is a source registry and clinician-reviewed, narrow use case for one diagnosis per specialty, rather than broad unsupervised medication coverage.
