# Free and Open-Licensed Pharmacology Knowledge for Dr. Mia

## The strategy

Use three distinct knowledge layers:

1. **Open educational books** for foundational pharmacology concepts. Reuse only content with a license that supports our commercial product and preserve attribution/version metadata.
2. **Public drug data** for medication identity and label discovery. Prefer NLM RxNorm for normalization and openFDA for label-record metadata; treat DailyMed as a current-label discovery/version source with record-level rights checks.
3. **Clinical practice evidence** for actual dental decisions. Use source-specific guidelines, in-scope official resources, current patient context, qualified dentist approval, and explicit evidence references. A textbook or a label record is not automatically a patient-specific prescribing recommendation.

The source catalogs live in:
- `ai_front_desk/clinical/pharmacology_learning_library.json`
- `ai_front_desk/clinical/drug_data_sources.json`

They record reuse permissions separately from clinical approval. The current evidence registry still has **zero approved medication evidence cards**.

## Open-licensed books suitable for commercial educational reuse

### 1. [Nursing Pharmacology, 2nd edition — NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK595000/)
- **License:** CC BY 4.0.
- **Commercial reuse:** allowed with attribution and license notice.
- **Good for:** pharmacokinetics, pharmacodynamics, drug classes, antimicrobials, adverse effects, and general medication-safety concepts.
- **Critical limitation:** the authors expressly say this is not intended to be used as a drug reference. Use it as foundational educational knowledge, never as the sole authority for a prescription.
- **Attribution:** Ernstmeyer, K., & Christman, E. (Eds.). (2023). *Open RN Nursing Pharmacology* (2nd ed.), Chippewa Valley Technical College, CC BY 4.0.

### 2. [Essentials of Pharmacology — University of Illinois Chicago / Medicine LibreTexts](https://med.libretexts.org/Courses/University_of_Illinois_Chicago/Essentials_of_Pharmacology)
- **License:** CC BY 4.0 per the page's licensing metadata.
- **Commercial reuse:** allowed with attribution, subject to checking individual third-party elements/chapter notices.
- **Good for:** pharmacokinetics, pharmacodynamics, pharmacogenomics, drug development, and unintended medication outcomes.
- **Critical limitation:** educational background only, not a current drug monograph or patient-specific prescribing authority.

### 3. [Microbiology, Pharmacology, and Immunology for Pre-Clinical Students](https://open.umn.edu/opentextbooks/textbooks/1778)
- **License:** Virginia Tech's official announcement identifies CC BY 4.0, but the same page also describes use as "not primarily commercial," which appears inconsistent with the standard CC BY 4.0 license terms.
- **Commercial reuse:** **blocked pending written clarification from the publisher**. The machine-readable source catalog sets commercial reuse to false until the ambiguity is resolved.
- **Good for:** preclinical medical foundations, microbiology, immunology, infections, and broad treatment mechanisms.
- **Critical limitation:** this is not a drug-interaction service or a dental prescribing guideline. Do not ingest the text into the commercial index while reuse terms remain unresolved.

## Free-to-read sources not approved for commercial copying

### [OpenStax Pharmacology for Nurses](https://openstax.org/books/pharmacology/pages/preface)
The license is **CC BY-NC-SA 4.0**, which restricts reuse to noncommercial purposes. It is fine to provide a link for independent reading, but do not ingest, redistribute, adapt, or train the commercial Dr. Mia product on this content unless OpenStax grants permission.

A source being free to view, downloadable, or available in NCBI/LibreTexts does not automatically mean every underlying work is reusable. Check the actual book/article and embedded third-party license.

## Free public drug-data layer

### [RxNorm API — US National Library of Medicine](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html)
NLM's terms state that the RxNorm, RxTerms, Prescribable RxNorm, and RxClass APIs may be used free of charge, with terms and specific third-party vocabulary conditions. The service has a limit of 20 requests/second/IP and recommends 12–24 hour caching. Include NLM's requested attribution statement and do not imply NLM endorsement. This is suitable for name normalization and identifier mapping, **not for a drug-interaction check**.

NLM says the RxNav Drug-Drug Interaction API was discontinued on January 2, 2024. Do not build against it.

### [openFDA drug-label API](https://open.fda.gov/apis/drug/label/)
The openFDA terms state that, unless otherwise noted, their data/documentation is public domain/CC0 and may be used commercially. Some records include private-party material whose rights are limited, so exclude or separately review any record with a third-party-rights warning. FDA also says submitted labels may not match the label for currently distributed products or be identical to the approved label, and it does not guarantee data accuracy or availability.

**Implementation choice:** initially display drug-label metadata and a link to the source record, not copied full label text. Label data is reference information, not an independent prescription decision.

### [DailyMed SPL web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm)
DailyMed exposes current Structured Product Labeling (SPL) information and label version history through a free public API. Before storing, redistributing, or adapting any label content, assess record-level rights and source notices. Use it as a label/version discovery and linking source first.

### [CDC dental antibiotic-prescribing checklist](https://www.cdc.gov/antibiotic-use/media/pdfs/dental-fact-sheet-508.pdf)
Useful candidate for the initial dental stewardship workflow and history/risk-factor checklist. Check the exact edition, scope, and embedded third-party content; create product evidence cards only after qualified dental review.

### [ADA antibiotic-stewardship resources](https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-stewardship)
Important source for US dental guidance, including current ADA content. Free online access is not itself a license to copy or embed the full text. Until applicable reuse rights are confirmed, link to the source and keep derivative clinical cards pending rights review and clinician approval.

## What is still missing for free

I have **not verified a complete, current, commercially reusable free drug-drug interaction database/API** suitable for a clinical prescribing product. RxNorm normalization is free, but its old RxNav interaction feature is retired. Commercial vendors such as DrugBank and Medi-Span require their own licensing arrangements for their comprehensive clinical data.

Do not substitute a scraped drug-interaction web page, an uncited LLM answer, or an incomplete research dataset and call it a validated interaction checker. A safer first step is to make Mia's public-data explorer retrieve drug identifiers and label metadata while the true interaction-checking layer remains explicitly unavailable until a defensible data source is found.

## Implemented first learning slice

The repository now contains `ai_front_desk/clinical/pharmacology_education_cards.json` and a local keyword-retrieval module, `pharmacology_education.py`. The initial set is a handful of original, short educational summaries about pharmacokinetics/ADME, pharmacodynamics, medication-history completeness, adverse medication outcomes, and antimicrobial concepts. Each note keeps source links, license metadata, attribution, and an explicit education-only scope.

The workbench can optionally search this shelf locally. It makes no external call for the learning search, and the notes cannot support a patient-specific diagnosis, medicine selection, dose, interaction result, or safety conclusion.

**What is not yet done:** the full books have not been bulk-downloaded or indexed. We deliberately start with a small, attributed concept set and keep the books linked as sources. Before expanding extraction, verify the exact rights and source version for each chapter and follow source-specific reuse and access rules. For example, the Open Textbook Library listing for the Virginia Tech preclinical book shows CC BY but does not specify a version, so the registry flags the exact version for confirmation before ingestion.

## How the intelligence layer should use books

- Ingest only commercially reusable CC BY material and preserve attribution, license, edition, chapter/section, and a content hash.
- Keep educational passages separate from clinical guideline cards and product-label metadata.
- Have a qualified dentist/pharmacist review any derived clinical statement before it can enter the approved evidence registry.
- Link every clinical output to a specific source version and section.
- Mark outdated or uncertain information as such; avoid unsupported extrapolation.
- Keep evaluation cases synthetic until privacy, security, clinical governance, and applicable regulatory reviews are complete.

This catalog creates a lawful starting library; it does not mean the clinical content has already been ingested, validated, or approved for use in patient care.
