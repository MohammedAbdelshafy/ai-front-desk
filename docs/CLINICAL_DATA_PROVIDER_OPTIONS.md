# Dr. Mia — Clinical Data Provider Options

## Decision

Keep Dr. Mia's evidence and drug-data integration behind replaceable adapters. Separate three different jobs:

1. **Clinical guidance** explains what evidence-based recommendations apply to a defined clinical question and patient group.
2. **Drug labeling** provides a versioned product label, including indicated use, contraindications, warnings, and label-specific information.
3. **Medication terminology and interaction checking** identify products/ingredients reliably and flag potential drug-drug or other medication safety issues.

No single website should be treated as all three. A drug-interaction checker is not a substitute for a dental clinical guideline; a guideline is not a complete patient-specific interaction engine.

## First-party candidates to assess

| Provider/source | Best-fit role | Evidence from official information | Decision |
| --- | --- | --- | --- |
| [ADA clinical guidance and antibiotic stewardship](https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-stewardship) | Dentistry-specific guidance, practice standards, and scope-specific clinical recommendations. | The ADA's official page includes its antibiotic stewardship material and cites the 2026 Clinical Practice Statement plus the 2019 guideline for urgent management of pulpal/periapical pain and swelling. | Preferred clinical-guidance starting point for relevant US dental workflows. Review exact scope and licensing before copying or transforming content. |
| [CDC dental antibiotic prescribing checklist](https://www.cdc.gov/antibiotic-use/media/pdfs/dental-fact-sheet-508.pdf) | Practice checklist and stewardship factors for dental antibiotic workflows. | CDC publishes a dentistry-specific checklist and related resources. | Use as a candidate checklist source after current-version and reuse-rights review. Not a comprehensive medication database. |
| [DailyMed](https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm) | Versioned US drug labels supplied to FDA by manufacturers/labelers. | NLM says DailyMed contains labeling submitted to FDA by companies for marketed products. | Useful for label-level retrieval. Resolve the exact product label and version; do not infer patient-specific treatment suitability from label text alone. |
| [RxNorm / RxNav APIs](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html) | Normalize medication concepts and product/ingredient identifiers to reduce name-matching errors. | NLM documents RxNorm APIs for normalized drug terminology. NLM also explicitly says RxNav's Drug-Drug Interaction API was discontinued on January 2, 2024. | Evaluate for terminology matching only. **Do not build a new interaction checker on the discontinued RxNav DDI API.** |
| [DrugBank Clinical API](https://docs.drugbank.com/v1/) and [Drug-Drug Interaction Checker](https://go.drugbank.com/clinical/drug_drug_interaction_checker/) | Commercially licensed medication search and potential drug-drug interaction data. | DrugBank describes APIs for drug/products/interactions and an interaction checker that returns severity, mechanism, and management information. | Shortlist for a technical and commercial evaluation. Confirm access terms, allowed display/storage, coverage, update process, and clinical-use licensing before integration. |
| [Wolters Kluwer Medi-Span](https://www.wolterskluwer.com/en/solutions/medi-span) | Commercial drug databases and APIs for healthcare medication workflows and clinical safety screening. | The vendor describes APIs and drug data used for clinical safety screenings and medication workflows. | Shortlist as an enterprise-grade alternative; request a demo/quote and compare coverage, contractual terms, integration, and operating cost. |
| [FDA Clinical Decision Support Software guidance](https://www.hhs.gov/guidance/document/clinical-decision-support-software-guidance-industry-and-food-and-drug-administration) | US intended-use/functionality assessment for software that informs clinical decisions. | The HHS guidance portal lists the FDA guidance issue date as January 29, 2026. | Governance reference, not clinical prescribing content. The actual product needs an intended-use and regulatory assessment by qualified counsel. |

## Recommended integration path

1. **Now:** retain the current evidence-card adapter and registry; only reviewer-approved, in-date, jurisdiction-matched records can be retrieved. It currently has zero approved evidence cards.
2. **Run a vendor discovery:** request current developer documentation, sandbox access, pricing, update/correction SLA, coverage statements, and written permission for the intended clinical use from DrugBank and Medi-Span. Ask about medication identity normalization and any interaction alerts/codes.
3. **Separate product IDs from clinical guidance:** use a supported terminology service or licensed identity mapping to match clinician-entered medicines to canonical ingredients/products; never match on free-text drug names alone for a production interaction check.
4. **Keep clinical guideline cards separate:** an evidence card must cite a guideline/reference section and be reviewed by a qualified dental clinician. The vendor's interaction result is another independent source, not the guideline.
5. **Use explicit failure states:** unknown drug, ambiguous product, missing strength/route, unavailable vendor, stale data, or uncertain patient factors must yield a visible “not checked / needs review” state, never a silent green check.
6. **Validate in shadow mode first:** have qualified dentists compare the system's retrieved evidence and alerts against prewritten synthetic test cases. Track citation accuracy, missed critical risks, false alerts, correct no-answer behavior, staleness handling, and review time. Do not use the first prototype as the basis for a live prescription.

## Contract and operating questions for vendors

- Does the license permit use inside a clinician-facing AI copilot, and what may be displayed, summarized, cached, or logged?
- What regions and product identifiers are covered, and how are combination products, brand/generic mappings, route, strength, and formulation handled?
- What exactly constitutes a drug interaction alert, what are severity/evidence definitions, and how frequently are the data refreshed?
- Can the product pass a non-identifying patient medication list and patient factors without persisting data or training provider models on it?
- What are the uptime, latency, versioning, audit, incident response, support, and deprecation commitments?
- What data processing, security, privacy, and healthcare-contract obligations apply to the clinic and to each vendor?
- What are the true per-clinic and per-query costs at pilot and scale?

## Sources reviewed

- American Dental Association, [Antibiotic Stewardship](https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-stewardship) and its linked [2026 clinical practice statement](https://jada.ada.org/article/S0002-8177(26)00470-8/fulltext).
- CDC, [Checklist for Antibiotic Prescribing in Dentistry](https://www.cdc.gov/antibiotic-use/media/pdfs/dental-fact-sheet-508.pdf).
- US National Library of Medicine, [DailyMed about page](https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm), [RxNorm APIs](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html), and [RxNav FAQ](https://lhncbc.nlm.nih.gov/RxNav/information/FAQs.html).
- DrugBank, [API documentation](https://docs.drugbank.com/v1/) and [interaction API product page](https://go.drugbank.com/clinical/drug_drug_interaction_checker/).
- Wolters Kluwer, [Medi-Span](https://www.wolterskluwer.com/en/solutions/medi-span).
- FDA, [Clinical Decision Support Software guidance](https://www.hhs.gov/guidance/document/clinical-decision-support-software-guidance-industry-and-food-and-drug-administration).

These are candidate providers and sources, not endorsements. Access, licensing, scope, and current contract terms need confirmation before implementation. Nothing from these pages has been promoted to an approved medication evidence card in the live registry.
