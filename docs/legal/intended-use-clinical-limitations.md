# Intended Use & Clinical Limitations — Mia Dental Prescribing Copilot

> **DRAFT v0.1 — 2026-10-11 — requires qualified legal review before production use or real patient data.**
> This is a starting draft, not legal advice. It has not been reviewed by an attorney.

## What the copilot is

Mia Dental Prescribing Copilot is an **assistive reference workspace** for licensed dentists. It helps you:

- Organize the patient facts relevant to a prescribing decision (allergies, medications, conditions, patient factors) through guided questions;
- Consult source-cited dental prescribing references (each item names its source, version, and date);
- Run a structured safety check of an **intended prescription you choose** against the recorded patient context, with every flag citing its rule;
- Document **your own** review conclusion with a timestamp and audit history.

## What the copilot is NOT

- It is **not a diagnostic tool**. It does not diagnose conditions.
- It **does not prescribe**. It never selects, issues, signs, or transmits a prescription. Only you do.
- It is **not a substitute for clinical judgment**, dental education, or consultation with colleagues, pharmacists, or physicians.
- It is **not a comprehensive drug-interaction database**. Reference items come from cited public sources (e.g., FDA-approved labeling via DailyMed, ADA/WHO/SDCEP guidance); absence of a flag is **not** proof of safety — especially when patient information is missing or uncertain. Unknown safety is shown as "cannot verify," never as verified-safe.

## Regulatory status

- The copilot has **not** received FDA clearance and is **not** marketed as a medical device.
- It has **not** undergone clinical validation. Synthetic test cases demonstrate software behavior only — they do not establish clinical performance or safety.
- The reference dataset is labeled by version and **requires qualified dentist review before clinical use**.

## Dentist responsibility

By using the copilot you acknowledge:

1. Every prescribing decision is yours alone.
2. You will verify reference information against current authoritative sources before acting.
3. You will not rely on the copilot where patient information is incomplete — the tool flags missing information precisely so you can resolve it.
4. You comply with the prescribing laws, regulations, and professional standards of your jurisdiction (U.S. state laws vary).

## Demo notice

The current deployment is a **demonstration using synthetic data only**. It is not HIPAA-compliant. **Do not enter real patient information** until compliant hosting is confirmed in writing.
