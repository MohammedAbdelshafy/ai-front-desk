# 07 · Source Rights Register and Clinical Evidence Card Template

> **DRAFT — RIGHTS, CLINICAL AND PHARMACY REVIEW REQUIRED**

**Owner:** Clinical content lead  
**Status:** The directory is not an approved clinical knowledge base  
**Version/date:** 0.1 / 2026-10-18

## 1. Source-rights register

Keep one row per source and, where rights differ, per specific work or record. Source discovery does not prove permission to reuse, adapt, redistribute, commercially exploit, or train on the content.

| Field | Required entry |
| --- | --- |
| Source ID / title | [Unique ID and canonical title] |
| Issuer / authors / publisher | [Entity] |
| Canonical URL and version | [URL, edition, published/updated date] |
| Access date / checked date | [Date] |
| Jurisdiction and clinical scope | [Country/population/indication] |
| License / terms / third-party rights | [Exact terms and URL] |
| Allowed activities | [Link only / display metadata / quote limited passages / adapt / commercial use / other] |
| Attribution requirement | [Exact attribution language and placement] |
| Rights reviewer / decision / date | [Name, rationale and evidence link] |
| Clinical reviewer / status | [Not reviewed / draft / approved for named scope / retired] |
| Update/expiry trigger | [Date, update check, withdrawal notice or other condition] |
| Integrity | [Version identifier or content hash if content is indexed] |

**Rights rule:** Never ingest or redistribute full text by default. Review source-specific licensing and third-party rights before copying or adapting content. In particular, WHO publications that use CC BY-NC-SA are not automatically available for commercial adaptation. Link to the canonical work when rights are uncertain.

## 2. Evidence lifecycle

Use these states; do not skip a review stage:

1. **Discovered:** source URL recorded, not evaluated.
2. **Rights-reviewed:** permitted use and attribution recorded.
3. **Clinical-review draft:** relevant passages/version identified; content not usable for a clinical recommendation.
4. **Approved for named scope:** qualified reviewer approved the exact card, population, jurisdiction and version.
5. **Needs re-review:** source updated, card expired, conflicting guidance found or reviewer requests reassessment.
6. **Retired:** no longer applicable or source/card withdrawn.

Automated version monitoring may raise an alert but may never auto-approve an update.

## 3. Clinical evidence card template

**Card ID:** [Unique stable ID]  
**Clinical question/indication:** [Specific question]  
**Jurisdiction:** [Required]  
**Patient group / exclusions:** [Required]  
**Intended user/action:** [Clinician-facing only / define]  
**Status:** [Must begin as clinical-review draft]  
**Version / effective date / review-by date:** [Required]  
**Owner:** [OB-GYN clinical lead]  
**Clinical reviewer / approver:** [Name, qualification, date]  
**Pharmacist/medication-safety reviewer:** [Name, qualification, date]

### Evidence and rationale
- Supported facts / recommendation basis: [Only what the reviewed sources support]
- Supporting sources and relevant sections: [Citation records]
- Evidence certainty or strength: [Only a source-supported rating; otherwise state not graded]
- Alternatives and why each may/may not apply: [Required]
- Source conflict / uncertainty / evidence gap: [Required]
- Current local guideline and product-label alignment: [Required]

### Safety rules
- Required patient-specific inputs: [Allergies and reaction; current medicines; relevant pregnancy/postpartum/lactation state; age/weight/renal/hepatic/lab data when relevant; diagnosis/indication; formulation/route; other necessary factors]
- Contraindications and exclusions: [Required]
- Interactions and screen limitations: [Required; identify validated service and coverage if used]
- Monitoring / follow-up: [Required]
- Dose, route, formulation or duration: [Leave blank unless specifically supported by an approved source and patient criteria; qualified reviewers must verify]
- Red flags / escalation: [Local approved pathway]
- Abstention conditions: [Required]
- What Mia must not say or do: [Required]

### Approval record
- [ ] Rights and attribution approved
- [ ] Source version confirmed and applicability checked
- [ ] Clinical review complete
- [ ] Pharmacist/medication safety review complete where appropriate
- [ ] Jurisdiction and local-protocol review complete
- [ ] Test cases passed, including missing-data and wrong-jurisdiction cases
- [ ] Human factors and output wording reviewed
- [ ] Release/change-control approval recorded

Until all applicable approvals are complete, the card is non-operative: the app may show source links for manual clinician review but may not output the card as a treatment recommendation.
