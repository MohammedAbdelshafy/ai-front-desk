# 08 · Regulatory Classification and Production Launch Gates

> **DRAFT — LOCAL LEGAL AND REGULATORY REVIEW REQUIRED**

**Owner:** Product owner + local regulatory counsel  
**Status:** No live-use approval  
**Version/date:** 0.1 / 2026-10-18

## 1. Classification memo

The applicable classification depends on the product’s actual intended purpose, functionality, users, marketing claims and output. A disclaimer alone does not decide whether a function is regulated.

**Product/build being assessed:** [Version, URL and release hash]  
**Intended purpose and user:** [Specify]  
**Clinical functions in scope:** [Specify]  
**Functions expressly out of scope:** [Specify]  
**Output types:** [Reference links / summaries / patient-specific suggestions / dose or treatment details]  
**Role of clinician in workflow:** [Specify]  
**Patient harm if output is wrong/missing:** [Assess]  
**Jurisdictions where offered/marketed:** [List]  
**Regulatory definitions/guidance assessed:** [Cite current official sources]  
**Classification conclusion for each jurisdiction:** [Counsel to complete]  
**Registration/authorization/quality-system obligations:** [Counsel to complete]  
**Reviewer and date:** [Name/date]  
**Reassessment trigger:** new function, new model, new claim, new jurisdiction, new target population, new level of automation or major evidence/workflow change.

## 2. Official starting points

Use current official sources and confirm the exact version at review time:
- Egypt Personal Data Protection Center material: https://pdpc.gov.eg/assets/pdf-data/Guidelines/DPO.pdf
- Egyptian Drug Authority regulatory material for software as a medical device / unique device identification: https://www.edaegypt.gov.eg/media/goxpgwu3/8_regulatory-guideline-on-requirements-for-unique-device.pdf
- FDA Clinical Decision Support Software guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- HHS HIPAA Security Rule risk analysis guidance where HIPAA applies: https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html
- EU GDPR Regulation (EU) 2016/679 where EU scope applies: https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
- WHO maternal-health and PPH sources for clinical content: https://www.who.int/publications/b/59332 and https://www.who.int/publications/i/item/9789240115637

The inclusion of a link is not a conclusion about applicability or compliance.

## 3. Launch gate tracker

A release that collects real patient information or exposes clinical decision support is blocked until every applicable row has evidence.

| Gate | Required evidence | Owner | Status |
| --- | --- | --- | --- |
| Intended use locked | Approved product specification and prohibited-use statement | Product + clinical lead | Blocked |
| Jurisdictional privacy review | Data-flow inventory, lawful basis, notice, rights, retention and transfer assessment | Local counsel/privacy lead | Blocked |
| Vendor contracts | Approved processor/subprocessor contracts; model-specific terms if used | Privacy/security lead | Blocked |
| Production identity | Role matrix, MFA/session rules, clinic isolation and authorization tests | Security lead | Blocked |
| Secure storage | Approved location, encryption, key management, backup and restore test | Security lead | Blocked |
| Clinical source rights | Source-level rights register and attribution review | Content/legal owner | Blocked |
| Clinical pathways | Approved evidence cards/pathways for exact scope | OB-GYN lead + pharmacist | Blocked |
| Safety validation | Clinical gold set, abstention/citation/unsafe-output metrics and resolved critical failures | Clinical safety lead | Blocked |
| Usability/human factors | Intended-user evaluation and resolved critical usability hazards | Clinical UX lead | Blocked |
| Regulatory classification | Written assessment and required registration/authorization plan | Regulatory counsel | Blocked |
| Incident readiness | Contact tree, notification workflow and tabletop exercise | Security/privacy/clinical leads | Blocked |
| Staff training | Approved SOPs, acceptable-use training and completion evidence | Clinic lead | Blocked |
| Production approval | Signed release review; open exceptions accepted by authorized owner | Accountable executive | Blocked |

## 4. Minimum launch rule

No real health data, live patient links, production authentication/storage or model call until applicable legal, privacy, security, clinical and regulatory gates are approved. No medication selection, dose support, interaction clearance or autonomous clinical action until the exact function is validated and approved for the intended population and jurisdiction.

**Release decision:** [Blocked / approved for named scope]  
**Release version/hash:** [Fill]  
**Approving owner(s):** [Names and dates]  
**Open exceptions and mitigations:** [Document]  
