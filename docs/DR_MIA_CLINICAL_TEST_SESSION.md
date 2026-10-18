# Dr. Mia prototype — dentist test session

**Purpose:** a short, source-cited workbench walkthrough for synthetic cases. This is not a live-patient prescribing tool and the draft cards must not be used to make treatment decisions.

## Launch locally

From a machine with Python 3.10+ and Git:

\`\`\`bash
git clone https://github.com/MohammedAbdelshafy/ai-front-desk.git
cd ai-front-desk
git fetch origin docs/dr-mia-product-positioning
git checkout docs/dr-mia-product-positioning
python -m pip install -e .
dr-mia-download-sources --list
dr-mia-workbench --port 8767
\`\`\`

Open http://127.0.0.1:8767. All scenarios below are synthetic. Never enter a real patient name, date of birth, chart number, symptoms, allergy history, current medication list or any identifiable health information.

If you have reviewed the CC BY 4.0 terms and attribution notes and want the two eligible education book files downloaded to \`~/.mia-dental-os/source-files/\`, run this separately:

\`\`\`bash
dr-mia-download-sources --all-eligible --confirm-rights-review
\`\`\`

This may download a large Open RN PDF and a smaller pharmacy education casebook. Files are stored outside the repository with \`.source.json\` provenance sidecars. The downloader does not index the books or make any passage an approved clinical evidence card. Restricted ADA/CDC materials remain linked references.

## Five test cases

### 1. Adult/adolescent acute dental pain

- Jurisdiction: \`US\`
- Assessment: \`acute dental pain after tooth extraction\`
- Symptoms: \`synthetic post-extraction pain\`
- Leave the optional public drug lookup unchecked.

**Expected behavior:** Mia shows a draft acute-pain evidence card, cites official ADA sources, identifies NSAID and acetaminophen/paracetamol pathways as candidates for dentist review, and does not pick an option for the synthetic case. There should be no dose, frequency, duration, patient-safety conclusion, or interaction result. Check age/procedure scope and all exclusions.

### 2. Dental swelling / suspected pulpal-periapical problem

- Jurisdiction: \`US\`
- Assessment: \`dental abscess and swelling\`
- Symptoms: \`synthetic localized swelling\`

**Expected behavior:** Mia shows the antibiotic-stewardship draft, including the source-linked treatment-first/antibiotic-stewardship context. Amoxicillin and penicillin V are presented only as source-named candidates for clinician review in specific guideline-defined situations, not as a selected medication. The 2019 ADA guideline summary must be reconciled with the 2026 ADA stewardship statement and current exact source versions before the card can be approved.

### 3. Reported penicillin/amoxicillin allergy

- Jurisdiction: \`US\`
- Assessment: \`penicillin allergy\`
- Symptoms: \`synthetic allergy-history review scenario\`

**Expected behavior:** Mia should show a “stop and verify” draft and offer no substitute antibiotic. It should ask for clinician review of the exact medicine, reaction, severity and source guidance. No allergy phenotype should be inferred from a label alone.

### 4. Same pain scenario in Egypt

- Jurisdiction: \`EG\`
- Assessment: \`acute dental pain after tooth extraction\`

**Expected behavior:** Mia displays Egypt's EDA/WHO reference links and shows no US draft candidates. It must not infer current Egyptian registration, local availability, local dosing, or prescribing scope from FDA/ADA resources. Egypt has no approved medication cards in this prototype.

### 5. Official label reference lookup

- Jurisdiction: \`US\` for the current FDA/openFDA source connection.
- Medicine name: \`ibuprofen\` (a source lookup term only).
- Check both **Look up medication identity and label metadata** and **Also retrieve key FDA label sections**.

**Expected behavior:** if the public service is reachable, Mia shows RxNorm identity metadata, openFDA product-label records/versions, selected label sections with truncation status, and a DailyMed link. It must state that only the standalone medicine name was sent externally. It must not claim it compared a patient medicine list, checked interactions, confirmed the locally available product, or judged the medicine safe. A failed/no-match API result must stay a failure/no-match, not be interpreted as a “clear” result.

## What the reviewer should record

For each synthetic test, write down:
- Does every claim have an exact, relevant source link and the correct jurisdiction?
- Is the patient's population / procedure / clinical question inside that source's actual scope?
- Is a draft option clearly separated from an approved recommendation?
- Does the interface expose missing context, version uncertainty and unavailable-provider states?
- Does Mia ever invent an option, dose, alternative for allergy, negative interaction result, or safety conclusion?
- Are source text reuse rights clear for the intended commercial use?

If anything is out of date, out of scope, legally unclear or clinically questionable, record the source and section, mark the card blocked, and do not use it clinically. Only a qualified dental clinician (and pharmacist where appropriate) should approve the dental medication cards. Passing a software test does not prove clinical safety.

## Current hard boundaries

- The approved medication evidence registry contains **zero approved evidence cards**.
- Three draft source summaries are available for synthetic UI testing only, all rights-review pending and not approved for clinical use.
- No comprehensive drug-interaction service is configured.
- No diagnosis engine, dose calculator, prescription generation/transmission, or real-patient chart integration is implemented.
- The current workbench is local-only and unauthenticated; do not expose it publicly or enter real patient data.
