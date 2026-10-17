# Mia Searchable Clinical Knowledge Library

## Purpose

Mia should help dental students and new clinicians learn how to reason through medication questions, find the right reference, and understand why a medicine may or may not be appropriate. The product needs a searchable library, not a model that merely tries to recall an answer from memory.

The library has two deliberately separate modes:

1. **Study mode:** search rights-cleared textbooks, pharmacology notes, and research passages to explain concepts with source citations.
2. **Clinical evidence mode:** retrieve only specific evidence cards that have passed source-rights checks, jurisdiction/scope checks, currentness checks, and qualified dental review. A textbook paragraph is never promoted to a clinical recommendation merely because retrieval found it.

The first corpus is for US dental education. Keep patient examples synthetic until privacy, security, clinical governance, and applicable regulatory requirements have been reviewed.

## Source tiers and ingestion policy

| Tier | Starting sources | What Mia may do | Current ingestion policy |
| --- | --- | --- | --- |
| Open educational textbooks | [Nursing Pharmacology, 2e](https://www.ncbi.nlm.nih.gov/books/NBK595000/); [UIC Essentials of Pharmacology](https://med.libretexts.org/Courses/University_of_Illinois_Chicago/Essentials_of_Pharmacology) | Explain basic concepts and retrieve passages with edition/section citations | Open RN is CC BY 4.0 and its book text says it is not a drug-reference book. UIC has CC BY 4.0 source metadata; verify the exact selected chapters and third-party elements before ingestion. |
| Candidate open textbook | [Microbiology, Pharmacology, and Immunology for Pre-Clinical Students](https://open.umn.edu/opentextbooks/textbooks/1778) | Potentially support infectious-disease and drug-mechanism education | The Open Textbook Library listing does not establish the exact CC BY version. Confirm the publisher's source license before any ingestion. |
| Noncommercial textbook | [OpenStax Pharmacology for Nurses](https://openstax.org/books/pharmacology/pages/preface) | Link-only independent reading | CC BY-NC-SA 4.0 is not approved for use in a commercial product without permission. Never ingest it through the standard importer. |
| Research articles | [PMC Open Access Subset](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/) | Retrieve reusable research passages and paper metadata | Rights are article-specific. Prefer CC BY or CC0; review share-alike implications before CC BY-SA. Exclude NC and ND material from the commercial derived-text index unless permissions explicitly allow the intended use. Use NCBI-approved retrieval services; do not scrape the website. |
| Dental guidelines | [CDC dental pain and swelling materials](https://www.cdc.gov/antibiotic-use/communication-resources/dentists-be-antibiotics-aware-pain-swelling.html); [ADA clinical practice guideline collection](https://www.ada.org/resources/research/science/evidence-based-dental-research) | Identify relevant source sections, then create reviewed clinical cards | Check exact version, patient population, scope, and embedded third-party rights. ADA materials remain link-only until applicable reuse rights are confirmed. CDC material still needs scope review and qualified clinical approval before it supports product recommendations. |
| UK dental guidance | [SDCEP Drug Prescribing for Dentistry](https://www.sdcep.org.uk/published-guidance/drug-prescribing/) | Link to the up-to-date reference for a user who works under the relevant jurisdiction | SDCEP states commercial use requires written permission. Do not ingest for commercial use without permission. |
| General guidelines | [NICE content reuse terms](https://www.nice.org.uk/reusing-our-content/nice-uk-open-content-licence) | Source discovery and linking | NICE's standard content licence explicitly does not cover AI use; international use has additional restrictions. Link-only until written permission or an appropriate agreement is obtained. |
| Drug identity and product labels | [RxNorm](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm), [openFDA labels](https://open.fda.gov/apis/drug/label/) | Normalize a name, discover an identifier, find a product-specific label and version | Keep identity/label metadata separate from the evidence corpus. Check record rights, currentness, jurisdiction, and product specificity. Do not claim an interaction check merely because drug names were normalized. |

**Rules of thumb:** free to read is not the same as reusable; public access is not a commercial licence; and a legally reusable book is not automatically a clinically appropriate prescribing source. NCBI Bookshelf says the license statement on each work controls reuse and restricts systematic downloads except through its specified Open Access retrieval route. PMC likewise states that rights vary by article and automated retrieval must use its approved services.

## How the index works

The workbench now has a local, offline full-text search path:

- An operator obtains a source text file through a permitted method and checks its exact license and selected content.
- `dr-mia-index-library` accepts only a source ID in the licensed pharmacology source catalog, rejects sources marked link-only/noncommercial/unknown, and requires an explicit rights-review confirmation for catalog entries with chapter or third-party-content caveats.
- The source text stays on the operator's machine. The index is written outside the repository by default at `~/.mia-dental-os/knowledge-library.jsonl`.
- The index preserves source title, source URL, license and license URL, attribution, edition/year, section heading, date indexed, source-file SHA-256, and use scope for each chunk.
- The search uses offline BM25-style lexical ranking. It does not send the query or source text to an external service.
- Re-indexing a source replaces that source's previous local chunks rather than showing the old and new edition as duplicate matches.
- Retrieved textbook passages are tagged `education_only` and `not_clinically_approved`. The clinical-evidence search excludes them by construction.

This first implementation accepts UTF-8 plain text rather than scraping or downloading books automatically. Convert only the rights-cleared source selection to text using a permitted workflow. The current source catalog is small and intentionally conservative.

## Example import workflow

Install the project in the local environment, then index a UTF-8 text extraction from a rights-cleared Open RN source:

```bash
dr-mia-index-library \
  --source-id openrn-nursing-pharmacology-2e \
  --file /path/to/rights-cleared-openrn-extract.txt
```

For a source with a chapter/third-party rights caveat, review the exact selected content first, exclude anything not covered by the license, then add `--confirm-rights-review`. The flag records the operator's confirmation; it does not replace legal advice or prove that a selection is reusable.

The workbench's local learning search checks both its concise source-linked education notes and any text indexed on that machine. With no imported book text, it clearly reports that the full-text index is empty instead of pretending the books have been loaded.

## Clinical retrieval rules

A future clinical suggestion must be built from approved clinical evidence cards, not raw book search alone. Every card needs:

- Source title, author/publisher, URL, exact section/table/page, edition/version, published/effective/retrieved dates, and a content fingerprint.
- Jurisdiction, indication, intended population, setting, inclusion criteria, exclusions, and any known exceptions.
- Evidence type and quality, limitations, conflicts with other sources, and known supersession/withdrawal status.
- A license and reuse decision for the source material and the exact derived content.
- Qualified reviewer role, review date, due date, rationale, approval ID, and a stale-source invalidation process.
- Test cases written or approved by dental clinicians, including missing context, allergy and reaction differences, concurrent medication issues, relevant conditions, pregnancy where applicable, organ-function context where relevant, out-of-scope conditions, conflicting sources, and no-match cases.

The retrieval response should make these distinctions clear:

1. **What the source says:** short passage or careful summary, with the exact citation and version.
2. **Why it might be relevant:** only within the indication/population the source actually covers.
3. **What is missing or conflicts:** unknown allergies, medication history, clinical findings, jurisdiction, or contradictory references must remain visible.
4. **What the source cannot establish:** never extrapolate a textbook teaching note into a patient-specific decision.
5. **When Mia must stop:** if there is no approved evidence, the patient context is incomplete, the evidence is stale, or the source does not match the case, return no recommendation and direct the learner to an appropriate supervisor/current reference.

A full drug-interaction checker, dose calculator, or independent medication selection engine is a separate workstream. No complete free, commercially reusable interaction source has yet been verified. A confident language-model answer is not a substitute for that missing data and validation.

## Roadmap

### Phase 1 — Foundation (in progress)
- Source catalog with explicit license states and conservative defaults.
- Local full-text ingestion for explicitly reusable foundational texts.
- Offline searchable index with section citations, edition, attribution, and content hash.
- Separate education search from clinical evidence retrieval.
- Unit tests that reject noncommercial sources and prove textbook chunks cannot satisfy the clinical-evidence gate.

### Phase 2 — Expand the library
- Confirm and ingest selected chapters from additional commercial-reuse open textbooks.
- Build an article-level PMC Open Access manifest and import only eligible license classes after a rights-policy decision.
- Add a refresh workflow that records source changes, flags superseded editions, and asks for re-review when content changes.
- Add hybrid semantic retrieval only if it improves measured retrieval recall; keep exact-phrase/BM25 search and source filters as a transparent fallback.

### Phase 3 — Clinician-reviewed dental evidence
- Prioritize bounded dental use cases selected with practicing dentists.
- Confirm reuse rights for each source before deriving cards.
- Turn carefully scoped evidence into versioned, reviewer-approved cards with deterministic inclusion/exclusion checks.
- Build a synthetic evaluation set for relevant evidence retrieval, citation precision, false reassurance, and correct abstention.

### Phase 4 — Medication-specific checking
- Evaluate licensed and open drug-interaction sources separately from learning books.
- Test medication names and ingredients, formulations, strength, route, patient factors, label versions, and interactions against an independently specified clinical reference set.
- Do not market comprehensive checking until coverage, omissions, and performance have been validated and applicable clinical, legal, privacy, and regulatory requirements have been addressed.

## Current state and limits

This repository contains the indexing/search code and a source-linked learning-note shelf. The index stores operator-provided licensed text locally; no complete book has been bundled in the repository and no book corpus is populated by default. The clinical evidence registry still has no approved medication evidence cards. The prototype is not deployed or approved for real-patient use.

The long-term product goal is a reliable *clinical librarian plus a tightly governed reasoning layer*: the library helps Mia find the relevant knowledge; a separate review and validation system determines whether any part of that knowledge can support a clinical suggestion.
