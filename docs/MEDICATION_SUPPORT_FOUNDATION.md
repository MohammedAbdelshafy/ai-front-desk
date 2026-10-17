# Dr. Mia Evidence Workbench — First Engineering Slice

## Status

This is the initial backend foundation for the dentist-facing clinical quality and prescribing copilot. It is an evidence-retrieval workbench foundation, **not a clinical decision engine**. The source registry is intentionally empty until source rights, jurisdiction, and qualified clinical review are established.

## Added components

- `ai_front_desk/clinical/medication_support.py`
  - Versioned source and evidence-card data models.
  - A curator-controlled approval state and mandatory source review due date.
  - Rights, reviewer, version, URL, review-date, and jurisdiction checks.
  - Exact-phrase retrieval against the clinician-entered assessment and symptoms.
  - Source provenance on every returned evidence card.
  - Reviewer-configured patient-factor prompts and risk-tag prompts.
  - Explicit response fields stating that prescribing, dose calculation, and comprehensive interaction checking are not performed.
  - Empty, stale, unapproved, rights-uncleared, and wrong-jurisdiction content fails closed.
- `ai_front_desk/clinical/medication_evidence_registry.json`
  - Empty versioned registry. No unreviewed or invented medication information is shipped as clinical guidance.
- `tests/test_medication_support.py`
  - Synthetic-only tests for source eligibility, traceable references, missing inputs, patient-factor prompts, jurisdiction matching, stale reviews, and fail-closed behavior.

## How evidence gets into the workbench

1. Select a legitimate source and confirm its use rights.
2. Record its title, publisher, version/edition, jurisdiction, URL, reviewer, review date, and review due date.
3. Prepare a short evidence card linked to an exact source section.
4. Have a qualified dental reviewer approve the card and configure any patient factors that must be checked.
5. Validate the card against clinically authored evaluation cases before enabling it in any real workflow.
6. Retire or re-review expired content. The runtime excludes entries that are not currently approved.

An evidence-card match means only that a reviewed entry matched the clinician-entered assessment phrase. It does **not** mean that the medication is appropriate, preferred, effective, or safe for the patient.

## Boundaries and next build steps

This module does not yet provide a user interface, a general-purpose drug database, an external reference integration, an automated drug-interaction checker, dose calculation, prescription writing, EHR/PMS integration, or production patient storage. It accepts a non-identifying case reference and is intended for synthetic development cases until the service is appropriately governed and validated.

Recommended next steps:
1. Build a small local clinician workbench UI for entering an assessment, viewing sources and review prompts, and recording a supervising dentist's review.
2. Research and confirm lawful, current dental prescribing sources for one narrowly defined initial jurisdiction.
3. Write an evaluation set with a qualified dentist and verify every card and expected result.
4. Only after that, consider integrating a maintained interaction/drug-reference provider under its supported terms, with explicit handling of unavailable or stale results.

## Testing note

Run the focused tests with:

```bash
python -m pip install pytest
python -m pytest -q tests/test_medication_support.py
```

Synthetic test fixtures use placeholder sources and explicitly fictitious summaries. They are not clinical examples.
