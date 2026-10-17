# Dr. Mia Clinical Information Centers

**Status:** source-routing plan and candidate directory, October 2026. This document does not make Mia a validated prescribing system. The machine-readable catalog is `ai_front_desk/clinical/clinical_information_centers.json`.

## The principle

Mia needs different information centers for different questions. A dental guideline answers a clinical-scope question; a drug label provides product-specific warnings and contraindications; RxNorm resolves medicine identity; an interaction service checks a defined list of medicines; and a country's regulator helps establish local regulatory context. None can safely replace the others.

All listed sources start as candidates. A respected organization, a public page, or a new edition does not by itself make any derived card clinically approved or legally reusable. No source in this directory is silently promoted to a recommendation source.

## Priority centers

### United States dental guidance

- **ADA — acute dental pain management guideline:** https://www.ada.org/resources/research/science/evidence-based-dental-research/pain-management-guideline/  
  Entry point for age- and procedure-specific acute dental pain guidance. Select the actual adult/adolescent or pediatric resource that matches the case.
- **ADA — antibiotic use for dental pain and swelling:** https://www.ada.org/resources/research/science/evidence-based-dental-research/antibiotics-for-dental-pain-and-swelling/  
  A defined guideline for a defined clinical question, not a universal antibiotic guide.
- **ADA — clinical practice guideline index and 2026 antibiotic-stewardship statement:** https://www.ada.org/resources/research/science/evidence-based-dental-research  
  Track individual statements and chairside tools as separate versioned sources.
- **CDC — dental pain and swelling materials:** https://www.cdc.gov/antibiotic-use/communication-resources/dentists-be-antibiotics-aware-pain-swelling.html  
  The official page reports an update on September 17, 2026. Recheck it for changes; review the exact fact sheet and any embedded third-party rights before deriving content.
- **AAPD — pediatric acute pain management:** https://www.aapd.org/research/oral-health-policies--recommendations/pain-management-in-infants-children-adolescents-and-individuals-with-special-health-care-needs/ and **pediatric antibiotic therapy:** https://www.aapd.org/research/oral-health-policies--recommendations/use-of-antibiotic-therapy-for-pediatric-dental-patients/  
  Pediatric source set; not to be mixed with adult pathways.
- **AAE — endodontic guidelines and position statements:** https://www.aae.org/specialty/clinical-resources/guidelines-position-statements/  
  Specialty-specific reference for in-scope endodontic questions.

These are currently source links/candidates. Before any derived recommendation is enabled, confirm the current artifact and scope, content rights, effective/version date, exact section, conflicts/supersession, and qualified dental review.

### Medicine identity, labels, and US regulatory context

- **NLM RxNorm:** https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html  
  Normalize ingredient/product identity and reduce name ambiguity. RxNorm is not a comprehensive interaction checker, and the old RxNav drug-interaction API was discontinued in 2024.
- **DailyMed:** https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm  
  Resolve product-specific Structured Product Labels and version history. Do not treat all products with the same ingredient as one label. Keep record-level reuse checks and show exact product/version.
- **FDA openFDA drug labeling:** https://open.fda.gov/apis/drug/label/  
  Useful for label-record metadata and discovery. FDA warns the dataset has limitations and may not match currently distributed product labeling; do not use it alone to make care decisions.
- **Drugs@FDA:** https://www.fda.gov/drugs/drug-approvals-and-databases/about-drugsfda and https://open.fda.gov/apis/drug/drugsfda/  
  Regulatory-approval history for the US, not evidence that a product is registered or available in Egypt.

### Egypt-specific medicine information

- **Egyptian Drug Authority — Egyptian Drug Register:** https://www.edaegypt.gov.eg/ar/المرجع-التنظيمي-لهيئة-الدواء-المصرية/سجل-الدواء-المصري/  
  Official country-specific drug-register chapters. The public pages do not establish a supported API contract, so do not assume automated querying or bulk scraping is authorized.
- **EDA periodic pharmaceutical lists:** https://www.edaegypt.gov.eg/ar/إصدارات-وتقارير-الهيئة-في-أرقام/إصدارات/قوائم-دورية/  
  Includes national essential-medicine, high-risk-medicine, do-not-crush, non-prescription, and pharmacovigilance-related list links. Capture the exact edition/date and review it before use.
- **Egyptian Pharmaceutical Information Center at EDA:** https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/inquire-about-reliable-drug-information/  
  A human-expert escalation route for difficult drug-information questions, not an API and not a bulk corpus.
- **WHO — Egypt National Essential Medicine List 2025:** https://www.who.int/publications/m/item/egypt--national-essential-medicine-list-2025-%28english%29  
  Country formulary/policy context only. It is not a patient-specific prescription guideline or proof of current stock.
- **WHO Model List of Essential Medicines:** https://www.who.int/publications/i/item/B09474  
  Global policy context, not a replacement for the local country's register or clinical guideline.

Mia must not infer Egyptian registration, product availability, local dosing, or legal prescribing scope from a US label or from the WHO list. The Egyptian lists and any EDA product information need a qualified local pharmacist/dentist review and rights assessment.

### Interaction and literature services

- **DrugBank Clinical API:** https://docs.drugbank.com/api-docs  
  Shortlisted as a licensed interaction/medication-data provider. It is **not integrated or configured**. Before use, validate Egypt and US coverage as relevant, licensing and clinical display rights, data retention, provenance, update process, clinical liability, API reliability, and per-clinic cost. No result or API outage must never be interpreted as “no interaction.”
- **PubMed / PubMed Central:** https://pubmed.ncbi.nlm.nih.gov/ and https://pmc.ncbi.nlm.nih.gov/  
  Literature-discovery centers for systematic reviews and primary evidence. Search results and abstracts alone do not constitute prescribing guidance; evaluate study quality, population, applicability, recency, conflicts, and article-level reuse rights.

## Required retrieval and medication-proposal flow

1. **Choose the jurisdiction first:** US or Egypt. Do not silently mix national formularies, approved products, or guidance.
2. **Require a dentist-entered working assessment and intended treatment context.** Mia must not diagnose from symptoms and then choose a medicine as if the diagnosis were confirmed.
3. **Collect relevant context:** age and weight where relevant; allergies and the actual reactions; current prescription/OTC medicines and supplements; relevant medical history; pregnancy/lactation where applicable; renal/hepatic function when relevant; immune status and other red flags; procedure and treatment availability.
4. **Retrieve only approved, current, jurisdiction-matched clinical evidence cards.** A raw web result, book passage, source catalog entry, or LLM memory is not an approved card.
5. **Resolve exact medicine identity and product details.** Use terminology matching, the correct local regulatory source, and the actual product-specific label/version where relevant.
6. **Run a licensed interaction/safety screen** over the complete, reconciled medicine list. Include allergies, contraindications and other clinically relevant factors through validated, scoped rules. A missing result, unmatched medicine, unavailable provider, or incomplete medication list means “not checked,” not “clear.”
7. **Show a shortlist only when the data gates pass:** the indication and patient group are within the reviewed guideline, the clinical card is current and approved, patient-context requirements are complete, product identity is resolved, and the required interaction/contraindication checks have returned interpretable results. Display why a candidate appears, why it may not fit, the exact cited section/version, what was checked, what remains unknown, and the limits of the evidence.
8. **The dentist decides and signs.** Mia must not issue or transmit a prescription. Dose instructions are blocked unless there is a separately reviewed, age/weight/route/formulation-specific dosing source and a validated calculation workflow. Escalate uncertainty or a high-risk case to a supervising dentist/pharmacist.

## Freshness and quality controls

The intended daily process is **change discovery, not blind re-ingestion**. Check source pages/API metadata for a version signal, then compare the actual artifact. For every clinical card keep the source publication/effective date, exact version/section, jurisdiction, content fingerprint, rights decision, reviewer and role, approval rationale, reviewed date, due date, and dependent-card IDs.

If a source changes, becomes unavailable, loses permission, or is superseded, mark dependent cards stale and stop returning them until human review. For licensed commercial APIs, respect the contract's release, caching, and display rules. For sites that expose no supported API, use manual review or a source-provided alert; do not invent an integration or scrape at scale.

## Current implementation boundary

The existing prototype has opt-in RxNorm and openFDA name-only metadata lookup. The catalog adds source discovery and clear roles for future adapters, but ADA/AAPD/AAE/CDC guidance, EDA information, and DrugBank are not yet wired as live recommendation sources. The evidence registry contains no approved medication evidence cards. Therefore Mia must continue to return **no verified medication recommendation** until source-specific, clinician-approved cards and the required safety integrations exist and pass evaluation.

The current app is a local prototype using synthetic data. Do not use it for real patient treatment or real patient data.
