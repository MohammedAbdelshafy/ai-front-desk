# 02 · Data Inventory and Data-Flow Worksheet

> **DRAFT — PROFESSIONAL REVIEW REQUIRED**

**Owner:** Privacy lead / responsible clinic entity  
**Status:** Draft; current app is synthetic-only  
**Version/date:** 0.1 / 2026-10-18

## 1. Current-state flow

1. A browser downloads the deployed front-end bundle.
2. The UI renders fictional demo patient and appointment objects supplied by the app.
3. Questionnaire answers and chat messages live in application/browser memory during the demo session; the app has no patient-record backend.
4. Evidence search is performed locally against a bundled OB-GYN source directory.
5. When the user opens a source, the browser navigates to that public source's website. The selected source website may receive ordinary web request metadata under its own terms.
6. Avatar image selection uses a browser-local preview; the app does not upload the image.

**Current state does not imply the architecture is appropriate for live patient data. Do not put real health information into this flow.**

## 2. Production data inventory: complete before implementation

| Data element | Purpose | Source / data subject | Minimum necessary? | Storage / region | Access role | Retention / deletion | Legal basis / notice |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Patient identity/contact | [Define] | [Define] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Allergies and reactions | [Define] | [Patient/clinician] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Medication statements | [Define] | [Patient/clinician] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Obstetric/gynaecology history | [Define] | [Patient/clinician] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Appointment and encounter | [Define] | [Clinic/clinician] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Questionnaire responses | [Define] | [Patient] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Clinical chat and citations | [Define] | [Clinician] | [Redact/limit] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Documents/images/labs | [Define] | [Patient/lab/clinic] | [Decide] | [Not selected] | [Define] | [Counsel-approved value] | [Counsel to assess] |
| Audit and security events | Security/accountability | System | [Minimize] | [Not selected] | Restricted | [Approve] | [Counsel to assess] |

Do not fill the production columns with guesses. Values must be decided against applicable Egyptian law, the clinic's retention duties, vendor capabilities and the final deployment design.

## 3. Data flow to approve

For each arrow below, identify data fields, purpose, transport, processing location, recipients, retention, contract and legal basis.

- Patient/browser → clinic patient portal: [not implemented]
- Clinician app → patient database: [not implemented]
- App → file/object storage: [not implemented]
- App → AI/model provider: **disabled; no provider selected**
- App → medicine identity/product-label source: **disabled in this prototype**
- App → analytics/error monitoring: [not configured; review before enabling]
- Backup/archive → recovery environment: [not configured]
- Clinic A app ↔ Clinic B app: **prohibited by default; no patient sharing**

## 4. Review checklist

- [ ] Purpose and data fields are necessary and proportionate.
- [ ] Controller/processor roles and patient-facing notices are agreed.
- [ ] Data location, backups, support access and onward transfer are mapped.
- [ ] Retention schedule and deletion/restriction behavior are documented and tested.
- [ ] Model training, request logging, retention and provider support access are explicitly addressed.
- [ ] Audit logs exclude secrets and avoid duplicating full clinical records unnecessarily.
- [ ] DPIA / privacy impact assessment completed where required.
- [ ] Cross-border transfer assessment completed where required.
- [ ] Security lead validates each data flow.
- [ ] Counsel signs off for the exact launch jurisdiction.

**Review result:** [Open / approved with exceptions / rejected]  
**Reviewer(s):** [Name/role]  
**Date:** [Date]  
**Evidence / exceptions:** [Links]  
