# Dr. Mia — Dental Clinical Quality & Prescribing Copilot

**Your AI clinical co-pilot for more confident, consistent dental care.**

Dr. Mia is a character-led clinical support product direction for dental practices. Her core job is to help dentists, especially junior clinicians, review patient-specific medication considerations against reliable, traceable clinical references and support consistent practice standards. The product vision also includes pre-visit patient history, appointment communication, patient feedback, and optional front-desk and growth add-ons.

**The core product is clinical quality and prescribing support.** The AI front desk, retention automation, and Lead Engine are optional expansions, not the product's identity.

> **Current status:** this repository contains reference communication workflows, testable administrative logic, a local clinical-intake demo, and an initial local medication evidence workbench using synthetic data. The workbench can retrieve only approved, current, jurisdiction-matched evidence cards; the registry currently contains candidate source links only and **zero approved medication evidence cards**, so no medication recommendations are available. It does not diagnose, prescribe, calculate doses, or perform comprehensive interaction checks. Live phone answering, production messaging, appointment scheduling, and production clinical decision support are not shipped.

## Core product: Clinical Quality & Prescribing Copilot

The proposed dentist-facing workflow lets a clinician enter their assessment and relevant patient context, including symptoms, allergies and reactions, current medicines, medical history, and other clinically relevant factors. Dr. Mia retrieves applicable evidence from approved, current dental and medication references and presents a structured review for the dentist to assess.

The intended review may include:
- Evidence-linked medication options relevant to the clinician-entered assessment.
- A plain-language explanation of why each option may be considered and what the source says.
- Patient-specific safety considerations, such as recorded allergy conflicts, possible interactions, contraindications, dose-relevant factors, and missing information.
- Reference title, edition/version and section or page where available, with publication/effective date and jurisdiction where relevant.
- A clear indication of uncertainty or when a supervising clinician or other qualified professional should review the case.

Dr. Mia supports the dentist's reasoning; she does not independently diagnose, issue a prescription, sign or transmit medication orders, or replace clinical judgment. A disclaimer alone is not a safety system: real-world use requires qualified clinical governance, source licensing and currency controls, rigorous evaluations, access controls, auditability, and jurisdiction-specific review.

### Quality assurance and supervision

The broader quality-assurance layer can help a practice standardize its workflows: clinic-approved protocols, evidence-linked checklists, review of missing information, clear escalation to a lead dentist, and auditable records of what the assistant surfaced. Any performance or prescribing-quality analytics must use defined, validated measures and appropriate access controls. Mia must not silently judge clinicians or turn unvalidated AI outputs into quality scores.

### Scope the first release

Start with a narrow, clinician-reviewed set of common dental medication scenarios and sources, then expand based on dentist feedback and clinical review capacity. Do not claim to cover every medication or every medical specialty on day one.

## Expansion modules (upsells)

- **Smart Patient Intake — prototype:** pre-visit dental history and a dentist-facing summary. The questionnaire remains a draft awaiting qualified dentist review.
- **Patient Retention & Feedback — planned:** booking confirmations and reminders from verified scheduling events, post-visit feedback, appropriate follow-up and clinic-approved recall messages. Marketing permission and opt-out must be handled separately from care communications.
- **AI Front Desk — optional add-on, planned:** after-hours and overflow inquiry capture, including a future voice/phone integration, with callback summaries and human handoff. A request must never be described as a confirmed booking unless a trusted scheduling workflow confirms it.
- **Growth / Lead Engine — optional add-on, proposed:** campaign inquiry capture, callback routing, source tracking and verifiable outcomes. Marketing contacts require appropriate permission; clinical data must not be repurposed as a marketing list.

## What's in this repository today

- `ai_front_desk/logic.py`: generic qualification state machine as pure, importable Python.
- `ai_front_desk/webhook.py`: local development/test harness for the Meta webhook contract. `DRY_RUN=1` by default.
- `ai_front_desk/n8n_workflow.json`: reference WhatsApp Cloud API workflow.
- `ai_front_desk/dental_logic.py`: early dental administrative intake logic, approved FAQ handling, and human handoff.
- `ai_front_desk/clinical/question_bank.py`: versioned conditional question bank and FHIR R4 Questionnaire export.
- `ai_front_desk/clinical/dental_intake_v1.json`: dental health-history form, currently a draft awaiting qualified dentist review.
- `ai_front_desk/clinical/intake.py`: validation, missing-answer and contradiction checks, FHIR QuestionnaireResponse export.
- `ai_front_desk/clinical/store.py`: local SQLite development store with clinic scoping and an audit log.
- `ai_front_desk/clinical/dashboard.py`: dentist-facing history brief with patient-reported answers, system-check flags, and a deterministic structured rollup. It is not AI-generated clinical interpretation.
- `ai_front_desk/clinical/mia_shell.py`: Dr. Mia character manifest and task-stage model.
- `ai_front_desk/clinical/server.py`: local demo server with patient intake, dentist dashboard, record review, corrections, audit history, and FHIR export endpoints.
- `ai_front_desk/clinical/medication_support.py`: versioned source/evidence models, source eligibility checks, exact-phrase retrieval, source provenance, baseline medication-history prompts, and a non-scoring clinical-completeness checklist. It is not a drug-interaction or dosage engine.
- `ai_front_desk/clinical/medication_workbench.py`: local clinician-facing synthetic-case UI at port 8767; no case persistence, no external calls by default, and opt-in name-only queries to NLM RxNorm/openFDA for metadata.
- `ai_front_desk/clinical/medication_evidence_registry.json`: candidate clinical reference links only; no approved evidence cards are enabled.
- `ai_front_desk/clinical/pharmacology_learning_library.json`: open-license pharmacology books and reuse/attribution constraints.
- `ai_front_desk/clinical/drug_data_sources.json`: drug-data sources, terms, API scope, and known limitations.
- `ai_front_desk/clinical/public_drug_data.py`: opt-in name-only metadata lookup through NLM RxNorm and openFDA. It does not fetch or transmit the clinical case, and it is not an interaction checker.
- `ai_front_desk/clinical/pharmacology_education.py`: local keyword retrieval over original, source-linked educational notes; no external calls and no patient-specific prescribing advice.
- `ai_front_desk/clinical/pharmacology_education_cards.json`: educational summaries attributed to open-license pharmacology books and linked public sources; these are not approved prescribing recommendations.
- `docs/DENTAL_AI_MVP_BUILD_SPEC.md`, `docs/DENTAL_AI_GITHUB_RESEARCH.md`, `docs/DENTAL_AI_PRODUCTION_REFERENCE.md`: scope, research, and production architecture notes.
- `docs/MIA_CLINICAL_PLATFORM_BUILD_PLAN.md`: multi-app Mia runtime and multi-specialty clinical platform plan.
- `docs/DR_MIA_PRODUCT_POSITIONING.md`: core strategy, supporting features, upsells, and claims boundaries.
- `docs/DR_MIA_CLINICAL_COPILOT_MVP_SPEC.md`: clinical-first MVP scope, evaluation gates, and pilot boundaries.
- `docs/MEDICATION_SUPPORT_FOUNDATION.md`: workbench architecture and development test instructions.
- `docs/CLINICAL_SOURCE_REGISTER.md`: candidate sources and evidence approval checklist.
- `docs/CLINICAL_DATA_PROVIDER_OPTIONS.md`: source/terminology/interaction-provider comparison and integration decision criteria.
- `docs/OPEN_PHARMACOLOGY_AND_DRUG_DATA.md`: open book licenses, public drug-data options, attribution, and reuse guardrails.
- `docs/adr/001-clinical-data-store.md`: development storage decision and production prerequisites.

## Run the Mia Clinical intake demo

Requires Python 3.9 or newer. From the repository root:

```bash
python -m pip install -e .
python -m ai_front_desk.clinical.server
```

Open **http://127.0.0.1:8766**. Pick a fictional demo clinic, submit a fictional history, and inspect the dentist dashboard. The server deliberately binds to loopback only.

The demo database is stored at `~/.mia-clinical-demo/clinical-demo.sqlite3` by default. Set `CLINICAL_DB` to override the local path. This is a development prototype, not an EHR.

**Do not enter real patient data.** The questionnaire is marked draft and must be reviewed and approved by a qualified dentist before clinical use. The prototype has no production authentication, does not send messages or book appointments, and does not provide medication recommendations or autonomous clinical decisions. The Mia help conversation uses fixed local responses and is explicitly not a connected live AI model.

## Run the Dr. Mia Evidence Workbench demo

After installing the project, run:

```bash
dr-mia-workbench
# or
python -m ai_front_desk.clinical.medication_workbench
```

Open **http://127.0.0.1:8767**. The workbench uses synthetic cases only and stores no submissions. By default it makes no external API calls. The candidate evidence registry has zero approved medication evidence cards, so it intentionally returns **No verified evidence found**.

The form includes an optional public drug-data lookup. It remains off unless you check the box, and you should enter only one medicine name or active ingredient. The app then sends **only that standalone name** to NLM RxNorm and openFDA to retrieve identity/label metadata. The clinical case, symptoms, allergies, medications in the case, and medical history are not sent to those APIs. Do not enter real patient data anywhere in this prototype.

This lookup normalizes medication names and finds label metadata; it does not recommend medicines, calculate doses, assess interactions, or establish safety. Use the linked source labels and appropriate clinical guidelines, and require clinician review.

See [Free and Open-Licensed Pharmacology Knowledge](docs/OPEN_PHARMACOLOGY_AND_DRUG_DATA.md) for textbook licenses, API limitations, and required attribution.

## Test

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest -q
```

Check the actual workflow status before claiming a build is green.

## Safety and claims

This repository is a reference build, not a managed service. Do not claim that it is compliant with a healthcare privacy regime, clinically validated, or safe for production patient data without evidence. The dental questionnaire remains a draft pending qualified dentist review. It captures and organizes information; it does not diagnose, prescribe, recommend medicines, or replace a clinician. No clinical-support feature should be marketed as available until implemented and appropriately evaluated.

## License

MIT — Mohammed Abdelshafy.
