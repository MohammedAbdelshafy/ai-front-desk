# 04 · Vendor, Processor and Cross-Border Review

> **DRAFT — PROFESSIONAL REVIEW REQUIRED**

**Owner:** Product/security/privacy leads  
**Status:** Not approved for live patient data  
**Version/date:** 0.1 / 2026-10-18

## 1. Vendor register

Complete one record for every system that may process, store, transmit or support personal/health information.

| Vendor/service | Function | Data exposed | Region(s) and support access | Contract / DPA | Retention/training | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AppDeploy prototype hosting | Public front-end delivery | Current app code; synthetic-only demo data | Verify current contract and operational locations | Not reviewed here | No health data permitted | Prototype only |
| GitHub repository/CI | Source hosting/build checks | Source code and build logs; no patient data | Verify organization settings and logs | Review required before sensitive content | Keep secrets out of repository | Code-only |
| Future clinic identity provider | Authentication/authorization | Account and audit metadata | Not selected | Required before production | Not selected | Not approved |
| Future database/file store | Clinical records and attachments | Potentially sensitive health data | Not selected | Required before production | Not selected | Not approved |
| Future AI/model provider | Retrieval synthesis/generation | **No patient context permitted until approved** | Not selected | Required before production | Must review retention/training/model terms | Disabled |
| Public evidence sources | External source pages opened by browser | Ordinary web request metadata to source site | Source-dependent | Source terms apply | Source-dependent | Links only |

Do not assume a vendor is suitable for clinical data simply because it is popular, offers encryption, or supports a healthcare use case in another country.

## 2. Required due diligence for each vendor

- Legal entity, data-processing role, subprocessors and responsibilities.
- Processing countries, storage regions, backup region, support access and government-request process.
- Contract/DPA, breach notice SLA, audit rights, deletion support, return/export support and service termination assistance.
- Encryption at rest/in transit, key control, authentication/MFA, access logs, vulnerability management, incident history and certifications where applicable.
- Whether content is logged, retained, sampled for support, used for training, shared with subprocessors or used to improve services.
- If AI is enabled: model-specific retention/training terms, prompt caching/logging, file/vector-store retention, abuse monitoring, region control, safety/logging identifiers, deletion semantics and provider failover.
- Availability, RTO/RPO, backups, support SLA, service changes, model changes and rollback.
- Applicable business associate or other statutory agreement, only where that law actually applies.

## 3. Cross-border decision record

**Clinic/controller country:** [Confirm]  
**Patient locations:** [Confirm]  
**Hosting and backup region(s):** [Confirm]  
**AI inference region(s):** [Confirm or not applicable]  
**Support access countries:** [Confirm]  
**Applicable law(s):** [Local counsel to determine]  
**Transfer mechanism / adequacy / authorization required:** [Counsel to determine]  
**DPIA / transfer risk assessment completed:** [Evidence link]  
**Decision:** [Blocked / approved for named scope / rejected]  
**Approver/date:** [Name/date]

## 4. Default decision for this release

No real patient data, AI-provider call, database, file store, authentication service or patient portal is enabled. This prototype is not a vendor or hosting approval. Select architecture only after the clinic/controller and local counsel review the proposed flows and contractual terms.
