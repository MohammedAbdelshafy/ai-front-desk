# 05 · Security Threat Model and Incident Response

> **DRAFT — SECURITY REVIEW REQUIRED. Controls listed here are requirements, not claims that they are deployed.**

**Owner:** Security lead  
**Status:** Draft  
**Scope:** Future hosted patient and clinical-record environment; prototype uses synthetic data only

## 1. Assets and trust boundaries

Assets to protect in a production system: identities/sessions, patient records, appointment history, questionnaires, notes, attachments, allergies, medication lists, clinical chat, evidence cards, source credentials, encryption keys, audit logs and backup copies.

Trust boundaries: clinician browser ↔ app API; patient device ↔ patient portal; app API ↔ database/object store; app ↔ model provider; app ↔ public evidence sites; clinic instance ↔ separate clinic instance; staff device ↔ administrative console.

## 2. Threat register

| Threat / hazard | Possible impact | Mandatory control | Evidence required |
| --- | --- | --- | --- |
| Wrong patient or appointment context | Clinical information attributed to the wrong person | Stable opaque IDs; server-side ownership checks; context preview; explicit context reset on switch | Automated cross-patient isolation tests |
| Broken object-level authorization | One clinic/staff member views another record | Deny-by-default authorization for every read/write/export; least privilege; tenant isolation | Adversarial permission tests |
| Stolen session or weak credentials | Unauthorized patient access | MFA for staff where feasible; short-lived secure sessions; session revocation; rate limits | Auth configuration and test report |
| Leaked database/service key | Bulk data exposure | Server-side secret manager; key rotation; never place privileged keys in frontend or Git | Secret scan and rotation evidence |
| Prompt injection or hallucinated drug advice | Incorrect clinical action | Retrieval allow-list; source-cited outputs; abstention; no autonomous actions; clinician review | Clinical test-set report |
| Stale or wrong-jurisdiction source | Unsupported or inappropriate recommendations | Source version/jurisdiction labels; review dates; conflict/staleness banner; approved-card release gate | Source audit |
| Incomplete allergy/medicine history | Contraindication missed | Unknown must remain distinct from negative; reconciliation prompts; block validated pathway if required data are missing | Regression tests |
| Malicious upload/document | Malware or unauthorized disclosure | File type and size controls, malware scan, private object permissions, safe preview and retention | Upload test and scan configuration |
| Accidental export or wrong recipient | Data disclosure | Export permission, confirmation, scoped export, watermark where suitable, audit event | Export access tests |
| Lost device / exposed browser | Session or record exposure | Session timeout, revocation, device policies, no PHI in local storage by default | Security test/evidence |
| Vendor breach / cross-border leakage | Data subject harm and legal exposure | Contract review, minimal data, approved region, incident notification terms, vendor inventory | Vendor approval record |
| Backup restore failure | Loss of clinical records | Encrypted backups, restore rehearsal, approved recovery targets | Restore exercise report |

## 3. Required controls before live data

- [ ] Threat model approved by security and clinic owner.
- [ ] Authentication, MFA policy, role/permission model and session revocation implemented.
- [ ] Server-side record authorization tested on every endpoint and storage object.
- [ ] Encryption in transit/at rest and key management reviewed.
- [ ] Secrets scanning, dependency scanning, vulnerability management and security updates configured.
- [ ] Secure coding review, penetration test and remediation of critical/high findings.
- [ ] Audit trails cover sensitive view/change/export/delete, consent/notice change, model call, source-card approval and break-glass events.
- [ ] Logs redact access tokens, secrets and unnecessary clinical content.
- [ ] Backup, restore, deletion and incident exercises completed.
- [ ] Approved hosting and data flow match the signed privacy assessment.

## 4. Incident response checklist

**Reporting channel:** [Fill]  
**Incident commander:** [Fill]  
**Privacy/legal contact:** [Fill]  
**Clinical safety contact:** [Fill]  
**Hosting/vendor escalation:** [Fill]

1. Protect people first. If a clinical safety issue affects a current patient, contact the responsible clinician and follow the clinic's approved escalation policy.
2. Contain the technical event: disable affected access/integration, revoke credentials/tokens, isolate affected systems and preserve evidence.
3. Establish scope: which clinic instance, records, staff, subjects, data fields, times, vendors and jurisdictions are involved.
4. Preserve logs/evidence safely with restricted access and chain-of-custody notes.
5. Escalate promptly to the controller, privacy/legal counsel, security lead, clinical lead and vendor incident contact.
6. Counsel determines legally required notification, recipients, deadlines and content for the applicable jurisdiction.
7. Recover from a known-good state, rotate secrets, patch the cause and verify isolation.
8. Complete root-cause review, patient-safety review, corrective actions and lessons learned.

**Incident record fields:** reference ID, detection time, reporter, affected instance, affected data types, containment, impact assessment, decision owner, notifications, corrective action, evidence links and closure sign-off.

## 5. Recovery objectives

RTO, RPO, backup frequency, backup location and recovery-test frequency must be set by the clinic/controller and system owner based on clinical operations and legal requirements. Do not invent a target in this template.

**Approved RTO/RPO:** [Pending decision]  
**Approved by:** [Name/date]  
**Restore test evidence:** [Link]
