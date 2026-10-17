# Dr. Mia Evidence Workbench — First Engineering Slice

## Status

This is the initial backend foundation for the dentist-facing clinical quality and prescribing copilot. It is an evidence-retrieval workbench foundation, **not a clinical decision engine**. The source registry is intentionally empty until source rights, jurisdiction, and qualified clinical review are established.

## Added components

- `ai_front_desk/clinical/medication_workbench.py`: local synthetic-case web UI at `http://127.0.0.1:8767`. It binds only to loopback, does not persist cases, and makes no external requests. The review screen surfaces a completeness checklist and requires a supervising-dentist review state; it does not record a prescription or clinical approval.
- `ai_front_desk/clinical/medication_support.py`
  - Versioned source and evidence-card data models.
  - A curator-controlled approval state and mandatory source review due date.
  - Rights, reviewer, version, URL, review-date, and jurisdiction checks.
  - Exact-phrase retrieval against the clinician-entered assessment and symptoms.
  - Source provenance on every returned evidence card.
  - Baseline prompts for allergy/reaction and current-medication review, shown even when no source card matches.
  - A deterministic clinical-completeness checklist for assessment, symptoms, allergies, current medicines, history, evidence state, and required supervising-dentist review. It is not a clinical quality score.
  - Reviewer-configured patient-factor prompts and caution-tag prompts.
  - Explicit response fields stating that prescribing, dose calculation, and comprehensive interaction checking are not performed.
  - Empty, stale, unapproved, rights-uncleared, and wrong-jurisdiction content fails closed.
- `ai_front_desk/clinical/medication_evidence_registry.json`
  - Versioned registry currently lists five candidate source links for qualified review, all marked `candidate` with unknown use rights. It contains zero evidence cards, and all candidates are excluded from clinical retrieval.
- `docs/CLINICAL_SOURCE_REGISTER.md`
  - Describes what each candidate source may support and the human approval checklist.
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

The local UI is a form-and-results workbench, not a production clinical service. There is no general-purpose drug database, external reference integration, automated drug-interaction checker, dose calculation, prescription writing, EHR/PMS integration, real-patient storage, authentication, or clinical validation. It accepts a non-identifying case reference and is intended for synthetic development cases only.

Run it with `dr-mia-workbench` or `python -m ai_front_desk.clinical.medication_workbench`; open `http://127.0.0.1:8767`. It intentionally returns “No verified evidence found” while the registry has no approved cards.

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
