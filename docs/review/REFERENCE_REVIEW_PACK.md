# Mia Dental OS — Clinical Reference Review Pack

**Dataset:** reference v2 (2026-10-11)
**Generated:** from `ai_front_desk/clinical/prescribe/reference_data.py` — do not hand-edit this file; regenerate with `python -m ai_front_desk.clinical.prescribe.export_review_pack`.

> **For the reviewing dentist:** you are reviewing the *accuracy of the reference content* below against current guidance. This is not an endorsement of the software, a clinical validation of outcomes, or a regulatory clearance. See `REVIEW_CHECKLIST.md` for instructions.

## Contents

1. Drug reference entries (by category)
2. Indication guidance
3. Safety rules (interactions / contraindications)
4. Counseling flags
5. Guidance-level sources

---

## 1. Drug reference entries

Standard **adult** dental references. Every entry below is reference information, not a prescribing recommendation.

## Analgesic

### Ibuprofen

- **Aliases:** advil, nurofen, brufen
- **Classes:** nsaid
- **Standard adult dosing:** 400 mg three times daily with food
- **Max daily:** 2400 mg
- **Notes:** First-line dental pain; avoid in significant renal impairment.
- **Cited sources:**
  1. **NIH DailyMed — Ibuprofen Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8804564c-9e1b-43c1-8b58-fd6ace645f00
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, NSAID warnings (cardiovascular, GI, renal), drug interactions.

### Paracetamol (acetaminophen)

- **Aliases:** acetaminophen, tylenol, panadol
- **Classes:** analgesic-antipyretic
- **Standard adult dosing:** 500–1000 mg every 4–6 hours as needed
- **Max daily:** 4000 mg
- **Notes:** Reduce maximum in liver disease or chronic alcohol use.
- **Cited sources:**
  1. **NIH DailyMed — Acetaminophen Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6176f9a2-6f2a-dcf6-e053-2a91aa0aee34
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, liver warnings, maximum daily dose, drug interactions.

### Naproxen

- **Aliases:** naprosyn
- **Classes:** nsaid
- **Standard adult dosing:** 500 mg twice daily with food
- **Max daily:** 1000 mg
- **Notes:** Longer-acting NSAID alternative to ibuprofen.
- **Cited sources:**
  1. **NIH DailyMed — Naproxen Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5ca1d392-ee02-3ce3-e063-6394a90a7827
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, NSAID warnings (cardiovascular, GI, renal), drug interactions.

### Diclofenac

- **Aliases:** voltarol
- **Classes:** nsaid
- **Standard adult dosing:** 50 mg three times daily with food
- **Max daily:** 150 mg
- **Notes:** Use lowest effective dose for shortest duration.
- **Cited sources:**
  1. **NIH DailyMed — Diclofenac Sodium Delayed-Release Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5cd83a0b-d2ef-7c21-e063-6294a90a63fd
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, NSAID warnings (cardiovascular, GI, renal), drug interactions.

## Antibiotic

### Amoxicillin

- **Aliases:** amoxil
- **Classes:** penicillin, beta-lactam
- **Standard adult dosing:** 500 mg three times daily, 3–5 days
- **Max daily:** 3000 mg
- **Notes:** First-line for most dental infections in non-allergic adults.
- **Cited sources:**
  1. **NIH DailyMed — Amoxicillin Capsule label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1d978882-d938-40cf-96be-59052d9599fe
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, warnings, drug interactions.
  2. **ADA — Antibiotic Prophylaxis Prior to Dental Procedures**
     - URL: https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis
     - Accessed: 2026-10-11
     - Supports: 2021 AHA scientific statement via ADA: single-dose amoxicillin prophylaxis for at-risk patients; prophylaxis limited to defined high-risk cardiac conditions.

### Metronidazole

- **Aliases:** flagyl
- **Classes:** nitroimidazole
- **Standard adult dosing:** 400 mg three times daily, 3–5 days
- **Max daily:** 2400 mg
- **Notes:** Anaerobic cover; often combined with amoxicillin.
- **Cited sources:**
  1. **NIH DailyMed — Metronidazole Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=cc004be0-da13-4b6b-83d5-d45b23fd37c9
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, warnings (incl. alcohol interaction), drug interactions.

### Azithromycin

- **Aliases:** zithromax
- **Classes:** macrolide
- **Standard adult dosing:** 500 mg on day 1, then 250 mg daily on days 2–5
- **Max daily:** 500 mg
- **Notes:** Option for penicillin-allergic patients.
- **Cited sources:**
  1. **NIH DailyMed — Azithromycin Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5f144e92-c9eb-420a-9bb8-4265a9f20a98
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, warnings, drug interactions.
  2. **ADA — Antibiotic Prophylaxis Prior to Dental Procedures**
     - URL: https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis
     - Accessed: 2026-10-11
     - Supports: 2021 AHA scientific statement via ADA: azithromycin listed among oral alternatives for penicillin-allergic patients needing prophylaxis.

### Erythromycin

- **Aliases:** —
- **Classes:** macrolide
- **Standard adult dosing:** 250–500 mg four times daily
- **Max daily:** 4000 mg
- **Notes:** Penicillin-allergy alternative; take on empty stomach.
- **Cited sources:**
  1. **NIH DailyMed — Erythromycin Ethylsuccinate Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=49b3ca93-43cc-439c-8f5d-e3ea2e87ad2f
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, warnings, drug interactions.

### Clindamycin

- **Aliases:** cleocin
- **Classes:** lincosamide
- **Standard adult dosing:** 300 mg four times daily, 3–5 days
- **Max daily:** 1800 mg
- **Notes:** Reserve for true penicillin allergy; counsel on diarrhoea risk.
- **Cited sources:**
  1. **NIH DailyMed — Clindamycin Hydrochloride Capsule label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2367340c-d297-4a3f-8253-6d27a0ed39cb
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, warnings (incl. C. difficile-associated diarrhea), drug interactions.
  2. **ADA — Antibiotic Prophylaxis Prior to Dental Procedures**
     - URL: https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis
     - Accessed: 2026-10-11
     - Supports: 2021 AHA scientific statement via ADA: clindamycin NO LONGER recommended as a prophylaxis alternative for penicillin-allergic patients (more frequent/severe reactions incl. C. difficile).

### Doxycycline

- **Aliases:** vibramycin
- **Classes:** tetracycline
- **Standard adult dosing:** 100 mg twice on day 1, then 100 mg daily
- **Max daily:** 200 mg
- **Notes:** Avoid in pregnancy and children under 8 (tooth discoloration).
- **Cited sources:**
  1. **NIH DailyMed — Doxycycline Hyclate Capsule/Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3e7cf78f-3b48-4614-9fa4-c6d1e0c05a35
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, warnings (incl. tooth discoloration, pregnancy), drug interactions.
  2. **ADA — Antibiotic Prophylaxis Prior to Dental Procedures**
     - URL: https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis
     - Accessed: 2026-10-11
     - Supports: 2021 AHA scientific statement via ADA: doxycycline listed among oral alternatives for penicillin-allergic patients needing prophylaxis.

## Anxiolytic

### Triazolam

- **Aliases:** halcion
- **Classes:** benzodiazepine
- **Standard adult dosing:** 0.25 mg orally, 1 hour before appointment (single dose)
- **Max daily:** 1 mg
- **Notes:** Conscious-sedation anxiolytic; single preoperative dose only.
- **Cited sources:**
  1. **NIH DailyMed — Triazolam Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5add318e-11b9-42f8-b052-0d8cebb32fcf
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, CNS-depression warnings, drug interactions.

### Diazepam

- **Aliases:** valium
- **Classes:** benzodiazepine
- **Standard adult dosing:** 5 mg the night before and/or 1 hour before appointment
- **Max daily:** 20 mg
- **Notes:** Anxiolytic for dental anxiety; avoid with alcohol.
- **Cited sources:**
  1. **NIH DailyMed — Diazepam (Valium) Tablet label**
     - URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=260e2041-2bb3-482f-850e-b5d47a7bdbe6
     - Accessed: 2026-10-11
     - Supports: FDA-approved labeling: approved indications, dosing, contraindications, CNS-depression warnings, drug interactions.

---

## 2. Indication guidance

Indication panels shown to the dentist to *educate* the choice. The dentist always selects and decides.

### Dental infection

**First-line:**
- Amoxicillin — 500 mg three times daily, 3–5 days
  - First-line for odontogenic infections in non-allergic adults.
**Alternatives:**
- Azithromycin — 500 mg day 1, then 250 mg days 2–5
  - When: Penicillin allergy.
- Clindamycin — 300 mg four times daily, 3–5 days
  - When: True penicillin allergy (reserve; counsel on diarrhoea risk).
- Metronidazole — 400 mg three times daily, 3–5 days
  - When: Anaerobic cover; often added to amoxicillin.
**Cautions:**
- Confirm penicillin-allergy history before choosing a macrolide or clindamycin.
- Metronidazole: patient must avoid alcohol during treatment and 48h after.

### Antibiotic prophylaxis (e.g. endocarditis-risk procedures)

**First-line:**
- Amoxicillin — 2 g orally, single dose 30–60 min before procedure
  - Standard single-dose prophylaxis in non-allergic adults. Source: ADA — Antibiotic Prophylaxis Prior to Dental Procedures.
**Alternatives:**
- Azithromycin — 500 mg orally, single dose 30–60 min before
  - When: Penicillin allergy. Listed by the 2021 AHA statement (via ADA) among oral alternatives for penicillin-allergic patients.
**Cautions:**
- Prophylaxis is indicated only for defined at-risk patients — confirm the indication, not just the drug.
- Per the 2021 AHA scientific statement (via ADA), clindamycin is NO LONGER recommended as a prophylaxis alternative for penicillin-allergic patients — more frequent and severe reactions, including C. difficile infection.
- AHA-listed oral alternatives for penicillin-allergic patients: cephalexin (or other 1st/2nd-gen cephalosporin), azithromycin, clarithromycin, or doxycycline — confirm current dosing with the cited source; only azithromycin is covered in this reference panel.
- Do not use cephalosporins in patients with a history of anaphylaxis, angioedema, or urticaria with penicillin (2021 AHA statement via ADA).

### Post-operative pain

**First-line:**
- Ibuprofen — 400 mg three times daily with food, shortest course
  - First-line dental pain control.
**Alternatives:**
- Paracetamol (acetaminophen) — 500–1000 mg every 4–6 hours as needed (max 4 g/day)
  - When: NSAID contraindicated or not tolerated.
- Naproxen — 500 mg twice daily with food
  - When: Longer-acting NSAID preferred.
**Cautions:**
- Avoid NSAIDs with anticoagulants, significant renal impairment, or active ulcer disease.
- Paracetamol: reduce maximum in liver disease.

### Dental anxiety (conscious sedation)

**First-line:**
- Triazolam — 0.25 mg orally, 1 hour before appointment (single dose)
  - Short-acting; patient must be escorted.
**Alternatives:**
- Diazepam — 5 mg the night before and/or 1 hour before
  - When: Longer anxiolytic effect desired.
**Cautions:**
- Single preoperative dosing only. Patient must not drive for 24 hours.
- Avoid combining with alcohol (additive CNS depression).

### Other / not listed

**Cautions:**
- No indication-specific guidance in reference v2 — use the full reference panel and your clinical judgment.

---

## 3. Safety rules

Each rule fires a flag when a dentist's intended prescription matches. Severity: **RED** = do not proceed as entered; **YELLOW** = caution / counsel.

| ID | Severity | Trigger | Reason | Source |
|----|----------|---------|--------|--------|
| `nsaid-anticoagulant` | RED | drug class = nsaid + current medication class = anticoagulant | NSAIDs increase bleeding risk when combined with anticoagulants. | reference v2 — drug interaction |
| `nsaid-antiplatelet` | YELLOW | drug class = nsaid + current medication class = antiplatelet | Additive bleeding risk with antiplatelet therapy — use lowest effective NSAID dose and shortest course. | reference v2 — drug interaction |
| `metronidazole-alcohol` | RED | drug = Metronidazole + patient-reported = alcohol_use | Disulfiram-like reaction risk: patient must avoid alcohol during treatment and for 48 hours after the last dose. | reference v2 — drug interaction |
| `metronidazole-warfarin` | RED | drug = Metronidazole + current medication class = anticoagulant | Metronidazole can raise INR in patients on warfarin — monitor closely and consider alternative. | reference v2 — drug interaction |
| `nsaid-renal` | RED | drug class = nsaid + patient condition = chronic kidney disease | Avoid NSAIDs in significant renal impairment — risk of further kidney injury. | reference v2 — condition caution |
| `nsaid-renal-2` | RED | drug class = nsaid + patient condition = renal impairment | Avoid NSAIDs in significant renal impairment — risk of further kidney injury. | reference v2 — condition caution |
| `nsaid-ulcer` | YELLOW | drug class = nsaid + patient condition = stomach ulcer | NSAIDs increase ulcer and GI-bleed risk — consider alternative or gastroprotection. | reference v2 — condition caution |
| `nsaid-gibleed` | YELLOW | drug class = nsaid + patient condition = gastrointestinal bleeding | NSAIDs increase ulcer and GI-bleed risk — consider alternative or gastroprotection. | reference v2 — condition caution |
| `tetracycline-pregnancy` | RED | drug class = tetracycline + patient condition = pregnancy | Tetracyclines are contraindicated in pregnancy (risk of tooth discoloration and bone effects). | reference v2 — condition caution |
| `paracetamol-liver` | YELLOW | drug = Paracetamol (acetaminophen) + patient condition = liver disease | Reduce the maximum daily paracetamol dose in liver disease and monitor. | reference v2 — condition caution |
| `benzo-alcohol` | YELLOW | drug class = benzodiazepine + patient-reported = alcohol_use | Additive CNS depression when benzodiazepines are combined with alcohol. | reference v2 — drug interaction |
| `aspirin-allergy-nsaid` | YELLOW | drug class = nsaid + patient allergy = aspirin | Possible cross-reactivity in aspirin-sensitive patients — use NSAIDs with caution. | reference v2 — allergy cross-reactivity |

---

## 4. Counseling flags

Informational flags attached whenever these drugs are prescribed:

- **Clindamycin:** Counsel the patient: stop the drug and contact the clinic promptly if significant diarrhoea develops (C. difficile risk).
- **Metronidazole:** Counsel the patient: avoid alcohol during treatment and for 48 hours after the last dose.
- **Triazolam:** Single preoperative dose only. Patient must be escorted and must not drive for 24 hours.
- **Diazepam:** Patient must not drive or operate machinery after dosing.

---

## 5. Guidance-level sources

Cited by indication panels and cautions above:

1. **ADA — Antibiotic Prophylaxis Prior to Dental Procedures**
   - URL: https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis
   - Accessed: 2026-10-11
   - Supports: 2021 AHA scientific statement on infective-endocarditis prophylaxis: patient selection, regimens, clindamycin removal, cephalosporin caution.
2. **WHO — The AWaRe Antibiotic Book**
   - URL: https://www.who.int/publications/i/item/9789240062382
   - Accessed: 2026-10-11
   - Supports: WHO AWaRe (Access, Watch, Reserve) antibiotic book: global guidance on first-line (Access) antibiotic selection for common infections.
3. **SDCEP — Antibiotic Prophylaxis Against Infective Endocarditis**
   - URL: https://www.sdcep.org.uk/published-guidance/antibiotic-prophylaxis/
   - Accessed: 2026-10-11
   - Supports: Scottish Dental Clinical Effectiveness Programme implementation advice (2nd ed., March 2026) for dental teams on NICE CG64 prophylaxis against infective endocarditis.

---

## Packet statistics

- Drug entries: 12
- Per-drug cited sources: 16
- Guidance-level sources: 3
- Indication panels: 5
- Safety rules: 12
- Counseling flags: 4

_End of review pack._
