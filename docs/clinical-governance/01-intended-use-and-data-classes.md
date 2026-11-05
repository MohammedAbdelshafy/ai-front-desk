# 01 · Intended Use and Data Classes

> **DRAFT — PROFESSIONAL REVIEW REQUIRED**

**Document owner:** Product owner + OB-GYN clinical lead  
**Scope:** Mia OB-GYN prototype; Egypt-first; one clinic/specialty per app instance  
**Status:** Draft; not approved for clinical use  
**Version/date:** 0.1 / 2026-10-18

## 1. Intended purpose

Mia OB-GYN is a software prototype designed to help a clinician organize a synthetic appointment workflow, review patient-reported pre-visit questionnaire concepts, and find links to relevant obstetrics/gynaecology reference sources.

The current release is a **non-clinical demonstrator**. It is not a validated clinical decision-support product and is not intended to support diagnosis, triage, prescribing, dose calculation, medication selection, delivery decisions, or autonomous care.

## 2. Intended users and setting

- Intended demonstrator users: developers, reviewers, OB-GYN clinicians and pharmacists assessing the user experience using fictional data.
- Initial geography considered for eventual deployment: Egypt.
- Other jurisdiction views in the reference directory are explicitly scoped; US/UK sources do not become Egyptian policy.
- Patients may not use the publicly hosted prototype to submit real information. Patient-facing intake is a simulated browser flow only.

**Named clinical owner:** [Name/role]  
**Intended clinical workflow after validation:** [Complete and approve]  
**Target population and exclusions:** [Complete with clinical/regulatory counsel]  
**Jurisdictions to be supported at launch:** [Complete]

## 3. Data classes

| Class | Examples | Permitted in phase one? | Controls / note |
| --- | --- | --- | --- |
| Public reference metadata | Source title, publisher, canonical public link | Yes | Respect source access terms; no blanket copying of full text |
| Fictional records | Demo Patient A, fake IDs, synthetic history | Yes | Keep visibly labelled synthetic |
| User settings | Interface language, avatar preset | Local UI only | No account sync or cross-device persistence |
| Avatar image | User-selected portrait | Local preview only | No upload or AI processing |
| Identifiable patient data | Name, phone, address, MRN, contact details | **No** | Do not enter, upload, or send |
| Protected/sensitive health data | Diagnoses, allergies, medicine lists, obstetric records, notes, images and investigations | **No** | Requires approved architecture and reviews before collection |
| External model inputs | Chat prompt containing chart context | **No real data** | No external model call is enabled |
| Credentials/secrets | API tokens, signing keys, database credentials | Never in front-end/browser/source | Future server-side secret manager only |

## 4. Prohibited uses

- Do not enter, import, screenshot or upload real patient data into the public prototype.
- Do not rely on Mia to decide the correct medicine or act as an autonomous prescriber.
- Do not use a missing source, failed request or an empty result as evidence of no risk.
- Do not treat a source directory, educational textbook, model output or keyword match as a clinically approved pathway.
- Do not publish or promote the app as certified, clinically validated, compliant, or ready for live patient care.
- Do not reuse one clinic's real patient data in another clinic/specialty application.

## 5. Required reconsideration before production

Revisit this statement whenever intended use expands to any of the following: real patient records; recommendations linked to diagnosis or medication selection; dose/route/formulation support; patient-specific risk scoring; automated triage; external LLM processing; clinical communication; EHR integration; or a new country.

**Approvals required before scope expansion:**  
- Product owner: [name/date]  
- OB-GYN clinical lead: [name/date]  
- Pharmacist / medication-safety reviewer: [name/date]  
- Privacy/legal counsel: [name/date]  
- Regulatory lead: [name/date]
