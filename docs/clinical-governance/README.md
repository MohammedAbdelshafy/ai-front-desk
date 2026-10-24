# Mia OB-GYN Clinical Governance Pack

> **DRAFT — PROFESSIONAL REVIEW REQUIRED. Not a legal opinion, compliance certification, clinical approval, or permission to use real patient data.**

This pack is tailored to the Egypt-first, OB-GYN-only Mia prototype. It is a set of working templates for the product owner, clinic owner, local counsel, security lead, OB-GYN lead and pharmacist. Fill every bracketed item, attach evidence, and record sign-off before a live-data or clinical-use launch.

## Current prototype facts

- Frontend-only hosted prototype; fictional demo records only.
- No backend patient record database, production authentication, external AI/model call, e-prescribing, EHR connection, live patient links, or clinic-to-clinic data exchange.
- The evidence chat performs local keyword/topic matching against a source directory. It does not grade evidence, diagnose, select a medicine, validate doses or establish clinical safety.
- Avatar images are previewed client-side and are not uploaded by the app.
- No source entry is an approved treatment pathway. No real patient information is permitted.

## Required owners

| Role | Accountable decisions |
| --- | --- |
| Product owner | Intended use, release scope, vendor selection and release gate |
| Clinic data controller / responsible entity | Lawful purpose, patient communication, access and retention decisions |
| Egypt-qualified privacy/legal counsel | Local data protection, health-data rules, contracts and transfers |
| Security lead | Threat model, controls, incident readiness and test evidence |
| OB-GYN clinical lead | Specialty pathways, emergency boundaries, validation and clinical approval |
| Pharmacist / medication-safety reviewer | Medicine sources, contraindications, interactions, monitoring and source conflicts |
| Regulatory counsel / responsible regulatory lead | Software/medical-device classification by jurisdiction and intended function |

## Documents

1. [Intended use and data classes](01-intended-use-and-data-classes.md)
2. [Data inventory and data-flow worksheet](02-data-inventory-and-data-flow.md)
3. [Privacy notice and consent/authorization templates](03-privacy-notice-and-consent-template.md)
4. [Vendor, processor and cross-border review](04-vendor-and-cross-border-review.md)
5. [Security threat model and incident response](05-security-threat-model-and-incident-response.md)
6. [Clinical risk and validation plan](06-clinical-risk-and-validation-plan.md)
7. [Source rights and evidence-card template](07-source-rights-and-evidence-card-template.md)
8. [Regulatory classification and launch gates](08-regulatory-classification-and-launch-gates.md)

## Rule for using this pack

A document existing in Git is not evidence that a review occurred. For every approval, record reviewer identity/role, date, the scope and jurisdiction approved, evidence reviewed, open exceptions and next review date. Do not mark a document approved until the responsible reviewer has actually completed and signed the review.
