# Free and Open-Licensed Pharmacology Knowledge for Dr. Mia

## The strategy

Use three distinct knowledge layers:

1. **Open educational books** for foundational pharmacology concepts. Reuse only content with a license that supports our commercial product and preserve attribution/version metadata.
2. **Public drug data** for medication identity and label discovery. Prefer NLM RxNorm for normalization and openFDA for label-record metadata; treat DailyMed as a current-label discovery/version source with record-level rights checks.
3. **Clinical practice evidence** for actual dental decisions. Use source-specific guidelines, in-scope official resources, current patient context, qualified dentist approval, and explicit evidence references. A textbook or a label record is not automatically a patient-specific prescribing recommendation.

The source catalogs live in:
- `ai_front_desk/clinical/pharmacology_learning_library.json`
- `ai_front_desk/clinical/drug_data_sources.json`
- `ai_front_desk/clinical/clinical_information_centers.json`
- `ai_front_desk/clinical/clinical_evidence_drafts.json` (draft-only, rights and clinician review pending)

See [Clinical Knowledge Downloads](CLINICAL_KNOWLEDGE_DOWNLOADS.md) for official PDF/archive links, version checks, and reuse restrictions.

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

**Implementation choice:** the default optional lookup displays RxNorm identity and openFDA label metadata. A second opt-in checkbox now retrieves a small whitelist of label sections (indications, dosage, contraindications, boxed warning, warnings, interactions, populations, adverse reactions) truncated to 1,800 characters per section. This sends only the standalone medicine name, does not store the label text, preserves a DailyMed link, and is clearly marked for clinician reference only. It is not a patient-specific safety assessment or interaction checker; openFDA itself warns not to rely on the data alone for medical-care decisions.

### [DailyMed SPL web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm)
DailyMed exposes current Structured Product Labeling (SPL) information and label version history through a free public API. Before storing, redistributing, or adapting any label content, assess record-level rights and source notices. Use it as a label/version discovery and linking source first.

### [CDC dental antibiotic-prescribing checklist](https://www.cdc.gov/antibiotic-use/media/pdfs/dental-fact-sheet-508.pdf)
Useful candidate for the initial dental stewardship workflow and history/risk-factor checklist. Check the exact edition, scope, and embedded third-party content; create product evidence cards only after qualified dental review.

### [ADA antibiotic-stewardship resources](https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-stewardship) and [AAE clinical guidelines](https://www.aae.org/specialty/clinical-resources/guidelines-position-statements/)
Important professional sources for dental decisions and specialty scope. Free online access is not itself a license to copy or embed full text. Keep source links available; index or derive clinical cards only after applicable reuse rights, current version, defined population, and qualified clinical approval are confirmed.

### [CDC Dental Pain and Swelling Materials (page updated September 17, 2026)](https://www.cdc.gov/antibiotic-use/communication-resources/dentists-be-antibiotics-aware-pain-swelling.html)
A timely candidate for dental antibiotic-stewardship learning and the first bounded clinical-quality workflow. Confirm the exact underlying fact sheet, scope, patient population, and third-party elements, and obtain qualified dentist review before enabling any derived recommendation.

### [Egypt National Essential Medicine List 2025 (English)](https://www.who.int/publications/m/item/egypt--national-essential-medicine-list-2025-%28english%29) and [WHO Model List of Essential Medicines 2025](https://www.who.int/publications/i/item/B09474)
Useful links for jurisdiction/formulary context and learning about essential-medicine policy. These lists do not provide patient-specific prescribing recommendations. Rights remain pending for commercial full-text ingestion; keep them link-only until permission is confirmed. Never apply the Egypt list automatically to a US workflow, or a US label automatically to an Egypt workflow.

### [Merck Manual Professional Edition](https://www.merckmanuals.com/professional)
A valuable external clinical reading reference, but Merck's official FAQ says users may share links and must assume the content is copyrighted; reuse for public or commercial purposes requires written permission. Mia's source catalog therefore marks it link-only without written permission.


## Daily refresh and source-quality policy

Not every source is updated daily. Daily freshness checks mean checking the *source for a change*, not copying every source into the index each day.

- openFDA Drug Label API: published updates weekly (the API page currently reports a last update of October 7, 2026); store last-seen update metadata and re-query source versions on schedule.
- openFDA Drugs@FDA: approval information updates daily Monday through Friday; use for approval-record discovery, not as a complete clinical decision engine.
- DailyMed SPL: use current SPL set IDs/version history to detect label changes and store source links plus retrieved timestamps. Before storing/reusing full text, run record-level rights checks.
- PubMed Central OA commercial-use collection: poll the official NCBI file lists or approved API on a scheduled cadence; ingest only articles whose individual reuse license qualifies.
- Guidelines and books: inspect publisher date/version metadata and page/announcement feeds where available; otherwise schedule a lower-frequency manual review. Do not report a source as “updated today” if only our own index timestamp changed.

Every indexed source should carry source_published_or_effective_date (when available), last_checked_at, source_version, content_hash, license_status, jurisdiction, and review_due_at. If the source version changes, mark dependent clinical cards stale until re-reviewed. If the source cannot be reached or its status is uncertain, retain the last verified result with an explicit stale/unverified banner or abstain; never silently treat cached data as current.

The system must also distinguish three independent outcomes: **content changed**, **license/terms changed**, and **clinical recommendation changed**. A new source timestamp alone must not auto-approve or auto-reject treatment content.

## What is still missing for free

I have **not verified a complete, current, commercially reusable free drug-drug interaction database/API** suitable for a clinical prescribing product. RxNorm normalization is free, but its old RxNav interaction feature is retired. Commercial vendors such as DrugBank and Medi-Span require their own licensing arrangements for their comprehensive clinical data.

Do not substitute a scraped drug-interaction web page, an uncited LLM answer, or an incomplete research dataset and call it a validated interaction checker. A safer first step is to make Mia's public-data explorer retrieve drug identifiers and label metadata while the true interaction-checking layer remains explicitly unavailable until a defensible data source is found.

## Implemented first learning slice

The repository now has two local retrieval layers:

- `pharmacology_education_cards.json` and `pharmacology_education.py` provide concise original summaries about ADME, pharmacodynamics, medication-history completeness, adverse outcomes, and antimicrobial concepts.
- `knowledge_library.py` provides an offline full-text indexing/search engine. It chunks operator-supplied UTF-8 text, performs BM25-style lexical ranking, and returns source links, section, edition/version, attribution, license, content hash, and index date. The `dr-mia-index-library` command uses an explicit source allow-list and blocks noncommercial, unknown, or unresolved commercial licenses.

The workbench can search both layers locally. Neither sends learning queries or indexed text to an external service. The engine is implemented and tested, but **the full-text index is empty by default**: no complete book text is bundled in the repository and no source text has been imported yet. An operator must obtain source text through a permitted workflow, verify the selected chapter's rights, then index it locally. The command does not crawl or download books automatically.

The license catalog includes a CC BY pharmacy casebook and CC BY educational-research papers about pharmacology competencies, case-based teaching, and generic-versus-brand education. These are valuable for teaching and curriculum design, not medication-specific treatment instructions. The Virginia Tech preclinical book is blocked from commercial ingestion until its publisher clarifies inconsistent commercial-use wording. The OpenStax nursing pharmacology book remains link-only because its license is noncommercial unless separate permission is obtained.

## How to import and use the local library

After obtaining UTF-8 plain text through a rights-cleared workflow, index it with:

```bash
dr-mia-index-library --source-id openrn-nursing-pharmacology-2e --file /path/to/rights-cleared-extract.txt
```

If a catalog entry has chapter-level or third-party-content caveats, check the exact selected content first and use `--confirm-rights-review` only after excluding any material not covered by the license. The flag is an operator attestation, not legal proof.

## How the intelligence layer should use books

- Ingest only commercially reusable material and preserve attribution, license, edition, chapter/section, source hash, and index date.
- Keep raw educational passages separate from clinical guideline cards and product-label metadata.
- Have a qualified dentist/pharmacist review any derived clinical statement before it can enter the approved evidence registry.
- Link every clinical output to an exact source version and section.
- Track source updates, expiry, corrections, and superseded editions; mark outdated or uncertain information.
- Keep evaluation cases synthetic until privacy, security, clinical governance, and applicable regulatory reviews are complete.

The local search engine is code, not a populated corpus. A textbook or article appearing in the study search must never by itself trigger a medication choice, dose, interaction result, or patient-specific safety conclusion.
