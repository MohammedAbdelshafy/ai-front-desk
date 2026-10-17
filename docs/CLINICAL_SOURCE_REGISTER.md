# Dr. Mia Clinical Source Register

## Purpose and state

This is a **candidate-source register**, not a clinical knowledge base. The initial jurisdiction is the United States. Candidate links below are not approved for clinical retrieval, and no medication recommendations or source-derived treatment content have been loaded into the evidence registry.

Every new source must be assessed for clinical scope, currentness, jurisdiction, reuse rights, product terms, and review requirements by an appropriate owner. Each specific evidence card needs review and approval by a qualified dental clinician before it can be retrieved by the prototype. Do not confuse public page access with permission to bulk-copy content or redistribute protected full text.

## Candidate sources

| Candidate | What it may support | Current status |
| --- | --- | --- |
| [ADA 2026 antibiotic-stewardship clinical practice statement](https://jada.ada.org/article/S0002-8177(26)00470-8/fulltext) | Current professional guidance and practice-level stewardship principles for dental antibiotic decisions. The ADA’s official page reports publication online on August 7, 2026. | Candidate only. Rights, exact scope, updates, and card-level clinical review not yet recorded. |
| [ADA antibiotic guideline for dental pain and swelling](https://www.ada.org/resources/research/science/evidence-based-dental-research/antibiotics-for-dental-pain-and-swelling) | Guideline-specific source for its defined patient population and clinical questions; not a universal antibiotic guide. | Candidate only. Confirm current status, scope, supersession, and reuse rights before deriving any cards. |
| [CDC Checklist for Antibiotic Prescribing in Dentistry](https://www.cdc.gov/antibiotic-use/media/pdfs/dental-fact-sheet-508.pdf) | A concise stewardship checklist for dental settings, including important history and risk factors. | Candidate only. Confirm the current version, scope, and permitted uses before indexing. |
| [DailyMed, US National Library of Medicine](https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm) | FDA-submitted labeling for marketed medicines, useful for label-specific indications, warnings, contraindications, and other product information. Label content is not by itself a patient-specific treatment decision. | Candidate only. Each product label/version needs explicit resolution and review. Do not treat a generic drug name as a single universal label. |
| [FDA Clinical Decision Support Software guidance, issued January 29, 2026](https://www.hhs.gov/guidance/document/clinical-decision-support-software-guidance-industry-and-food-and-drug-administration) | Product intended-use and functionality assessment for US regulatory planning. | Candidate governance reference only. Requires product/legal review; not a source of medication treatment recommendations. |

Candidate records are also listed in `ai_front_desk/clinical/medication_evidence_registry.json` with `approval_status: candidate` and `content_rights: unknown`. The runtime must continue to exclude all of them.

## Approval checklist

Before a specific evidence card can become available:

1. **Source rights:** identify the owner, terms, licence or API agreement, attribution requirements, and whether storing a summary or derived card is permitted.
2. **Clinical scope:** record which question, population, condition, procedure, and care setting the source actually addresses. Document exclusions and known limits.
3. **Version and jurisdiction:** identify publication/version/effective date and the US applicability. Check for updates, corrections, living recommendations, and superseding guidance.
4. **Qualified review:** record reviewer name/role, review date, due date, decision, and rationale in an auditable system.
5. **Evidence card:** cite the exact section/table/page where possible; distinguish the source's statement from the reviewer-authored summary; avoid extrapolating beyond the source.
6. **Safety evaluation:** test on clinician-authored synthetic scenarios, including incomplete histories, allergy conflicts, relevant interactions, contraindications, dosage context, contradictory facts, and no-match cases.
7. **Monitoring:** define who reviews the source when updated, how stale cards are disabled, and how clinicians see the source version they reviewed.

The initial workbench does not yet perform comprehensive drug interaction screening, dose calculations, diagnosis, or prescription generation. A source match only means that a reviewed phrase matched an evidence-card term; it does not mean the medication is appropriate or safe for a patient.

## Update procedure

Use versioned additions to the registry. Do not switch a candidate to approved merely because it is from a prestigious organization or has a public URL. A reviewer must evaluate the exact card and permitted use. If the source or evidence-card review date expires, the application should exclude the entry until it is re-reviewed. Keep the live clinical registry empty until the approval workflow is in place and the necessary qualified review has actually occurred.
