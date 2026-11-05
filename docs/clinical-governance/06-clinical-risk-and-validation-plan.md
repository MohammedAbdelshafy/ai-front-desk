# 06 · Clinical Risk and Validation Plan

> **DRAFT — OB-GYN CLINICAL LEAD, PHARMACIST AND REGULATORY REVIEW REQUIRED**

**Owner:** OB-GYN clinical lead + medication-safety pharmacist  
**Status:** No clinical pathways approved  
**Version/date:** 0.1 / 2026-10-18

## 1. Intended clinical role

The current app performs local reference discovery and demonstrates an appointment/questionnaire experience. It does not diagnose, triage, recommend/select a medicine, calculate doses, prescribe or perform interactions screening. No recommendation should be inferred from the order of search results.

Before any clinical decision-support function is enabled, the team must define its exact intended use, users, patient population, indications, excluded populations, jurisdiction, clinical actions, failure modes and required human oversight. Regulatory classification must be assessed against that actual intended function.

## 2. Minimum medication evidence record

Each proposed clinical evidence card must identify:

- Unique ID, title, scope, jurisdiction, version, status and review/expiry date.
- Clinical question/indication and supporting diagnosis criteria, including who establishes the diagnosis.
- Target population and explicit exclusions.
- Evidence source(s): title, issuing body, publication/update date, relevant section/page, canonical URL, access/rights status and date checked.
- Evidence certainty/strength only where an applicable authoritative system/source provides it; never fabricate an evidence grade.
- Supported options and their rationale; why an option might not apply; alternatives; contraindications; adverse effects; monitoring; interaction checks and the validated service/source used.
- Required inputs: allergy status and reactions, current medicines, pregnancy/postpartum/lactation status where relevant, age, weight/renal/hepatic function/labs when relevant, formulation/route and relevant comorbidities.
- Local approved protocol and product label applicable to the deployment jurisdiction.
- Clinical reviewer and pharmacist/medication-safety reviewer; decision, date and review frequency.
- Conflict handling, known limitations, prohibited outputs, fallback/abstention behavior and post-release monitoring metrics.

**No card can be approved from keyword matching, a model-generated summary, a textbook alone or a single product label without a complete clinical review.**

## 3. Critical hazards to assess

| Hazard | Expected safe behavior | Required test |
| --- | --- | --- |
| Severe bleeding, seizure, collapse or other emergency described | Prominent prompt to follow local emergency pathway; never delay care for a search | Clinical review of all emergency messages |
| Allergy status unknown | Keep unknown distinct; do not assume no known allergies; request clinician confirmation | Missing-allergy regression case |
| Medicine identity ambiguous | Ask for ingredient/formulation/product details; abstain from candidate choice | Similar-name and combination-product cases |
| Pregnancy week or postpartum/lactation context missing | State which facts are required and abstain where they materially affect safety | Missing-context tests |
| Wrong jurisdiction source | Exclude or clearly label nonlocal sources; never present US guidance as Egyptian regulation | Cross-jurisdiction tests |
| Interaction checker unavailable or incomplete | Say the check was not completed; never imply “no interactions” | Failure/incomplete coverage test |
| Stale or withdrawn source | Flag the source and withhold approval until reviewer decision | Stale source and supersession test |
| Evidence conflict | Show the disagreement and escalate for clinician review | Conflicting guidance test |
| Model hallucination / unsupported statement | Refuse to state unsupported clinical fact as verified; cite retrieved evidence | Grounding and citation audit |
| Wrong patient context | Clear previous patient context when switching appointments; show exactly what data is attached | Cross-patient isolation test |
| Incorrect dose/route/formulation | No dose unless an approved protocol and patient-specific criteria explicitly support it | Dose boundary tests |
| Model/API failure or no result | Explicit unavailable/insufficient evidence state | Empty/error response test |

## 4. Validation approach

1. Build a version-controlled reference test set approved by the OB-GYN lead and pharmacist; use synthetic cases only.
2. Include normal, edge, missing-data, contradiction, emergency, wrong-jurisdiction, medication-name ambiguity, source update and vendor failure cases.
3. Define scoring before testing: citation correctness, evidence support, correct jurisdiction, missing-data detection, contraindication coverage, calibration/abstention, unsafe recommendation rate and response time.
4. Have qualified reviewers independently assess correctness and severity; resolve disagreements and document rationale.
5. Test updates whenever the model, prompt, retrieval algorithm, source corpus, evidence card, jurisdiction or UI changes.
6. Perform usability/human-factors checks with intended clinicians, including workload, over-reliance and distinction between patient-reported facts and clinician-confirmed findings.
7. Set acceptance thresholds before the test run. Critical safety failures block release regardless of average accuracy.
8. Run a controlled pilot only after legal/regulatory approval, clinical approval, security completion and informed operational sign-off.
9. Monitor unsafe outputs, omissions, clinician overrides, source failures and incidents after release; maintain rollback and emergency disablement.

## 5. Current release result

- Approved medication pathways: **0**.
- Approved patient-specific prescribing recommendations: **0**.
- Live patient data: prohibited.
- External AI model call: disabled.
- Comprehensive drug-interaction screening: not implemented.
- Clinical validation for patient care: not performed.

**Clinical sign-off:** [Pending]  
**Pharmacy/medication-safety sign-off:** [Pending]  
**Human-factors review:** [Pending]  
**Regulatory assessment:** [Pending]
