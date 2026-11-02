"""Reference v2 — standard dental prescribing references with cited sources.

Conservative by design: only well-established dosing, contraindication,
and interaction facts are included. Anything uncertain is omitted.
Every entry is reference information, not a recommendation.

v2 changes (2026-10-11):
- Every drug now carries cited public sources (NIH DailyMed FDA-approved
  labels, ADA guidance, WHO AWaRe) with exact URLs and access dates.
- Antibiotic-prophylaxis guidance updated per the 2021 AHA scientific
  statement (via ADA): clindamycin is no longer a recommended prophylaxis
  alternative for penicillin-allergic patients.
"""
from __future__ import annotations

# drug_key -> reference entry. Doses are standard ADULT dental references.
DRUGS: dict[str, dict] = {
    "amoxicillin": {
        "display": "Amoxicillin",
        "aliases": ["amoxil"],
        "classes": ["penicillin", "beta-lactam"],
        "category": "Antibiotic",
        "standard_adult": "500 mg three times daily, 3–5 days",
        "max_daily_mg": 3000,
        "notes": "First-line for most dental infections in non-allergic adults.",
    },
    "metronidazole": {
        "display": "Metronidazole",
        "aliases": ["flagyl"],
        "classes": ["nitroimidazole"],
        "category": "Antibiotic",
        "standard_adult": "400 mg three times daily, 3–5 days",
        "max_daily_mg": 2400,
        "notes": "Anaerobic cover; often combined with amoxicillin.",
    },
    "azithromycin": {
        "display": "Azithromycin",
        "aliases": ["zithromax"],
        "classes": ["macrolide"],
        "category": "Antibiotic",
        "standard_adult": "500 mg on day 1, then 250 mg daily on days 2–5",
        "max_daily_mg": 500,
        "notes": "Option for penicillin-allergic patients.",
    },
    "erythromycin": {
        "display": "Erythromycin",
        "aliases": [],
        "classes": ["macrolide"],
        "category": "Antibiotic",
        "standard_adult": "250–500 mg four times daily",
        "max_daily_mg": 4000,
        "notes": "Penicillin-allergy alternative; take on empty stomach.",
    },
    "clindamycin": {
        "display": "Clindamycin",
        "aliases": ["cleocin"],
        "classes": ["lincosamide"],
        "category": "Antibiotic",
        "standard_adult": "300 mg four times daily, 3–5 days",
        "max_daily_mg": 1800,
        "notes": "Reserve for true penicillin allergy; counsel on diarrhoea risk.",
    },
    "doxycycline": {
        "display": "Doxycycline",
        "aliases": ["vibramycin"],
        "classes": ["tetracycline"],
        "category": "Antibiotic",
        "standard_adult": "100 mg twice on day 1, then 100 mg daily",
        "max_daily_mg": 200,
        "notes": "Avoid in pregnancy and children under 8 (tooth discoloration).",
    },
    "ibuprofen": {
        "display": "Ibuprofen",
        "aliases": ["advil", "nurofen", "brufen"],
        "classes": ["nsaid"],
        "category": "Analgesic",
        "standard_adult": "400 mg three times daily with food",
        "max_daily_mg": 2400,
        "notes": "First-line dental pain; avoid in significant renal impairment.",
    },
    "paracetamol": {
        "display": "Paracetamol (acetaminophen)",
        "aliases": ["acetaminophen", "tylenol", "panadol"],
        "classes": ["analgesic-antipyretic"],
        "category": "Analgesic",
        "standard_adult": "500–1000 mg every 4–6 hours as needed",
        "max_daily_mg": 4000,
        "notes": "Reduce maximum in liver disease or chronic alcohol use.",
    },
    "naproxen": {
        "display": "Naproxen",
        "aliases": ["naprosyn"],
        "classes": ["nsaid"],
        "category": "Analgesic",
        "standard_adult": "500 mg twice daily with food",
        "max_daily_mg": 1000,
        "notes": "Longer-acting NSAID alternative to ibuprofen.",
    },
    "diclofenac": {
        "display": "Diclofenac",
        "aliases": ["voltarol"],
        "classes": ["nsaid"],
        "category": "Analgesic",
        "standard_adult": "50 mg three times daily with food",
        "max_daily_mg": 150,
        "notes": "Use lowest effective dose for shortest duration.",
    },
    "triazolam": {
        "display": "Triazolam",
        "aliases": ["halcion"],
        "classes": ["benzodiazepine"],
        "category": "Anxiolytic",
        "standard_adult": "0.25 mg orally, 1 hour before appointment (single dose)",
        "max_daily_mg": 1,  # mg, not per-day dosing — single preoperative dose
        "notes": "Conscious-sedation anxiolytic; single preoperative dose only.",
    },
    "diazepam": {
        "display": "Diazepam",
        "aliases": ["valium"],
        "classes": ["benzodiazepine"],
        "category": "Anxiolytic",
        "standard_adult": "5 mg the night before and/or 1 hour before appointment",
        "max_daily_mg": 20,
        "notes": "Anxiolytic for dental anxiety; avoid with alcohol.",
    },
}

REFERENCE_VERSION = "reference v2"
REFERENCE_DATE = "2026-10-11"
# Every safety flag cites this dataset as e.g.
# "reference v2 (2026-10-11) — drug interaction".

ACCESS_DATE = "2026-10-11"  # when the public sources below were verified


def _dailymed(setid: str) -> str:
    return f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}"


# Cited public sources per drug. Each entry: name, exact URL, access date,
# and what it supports. Public labels/guidance only — no paywalled content.
# drug_key -> list of source dicts.
SOURCES: dict[str, list[dict]] = {
    "amoxicillin": [
        {"name": "NIH DailyMed — Amoxicillin Capsule label",
         "url": _dailymed("1d978882-d938-40cf-96be-59052d9599fe"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, warnings, drug interactions."},
        {"name": "ADA — Antibiotic Prophylaxis Prior to Dental Procedures",
         "url": "https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis",
         "accessed": ACCESS_DATE,
         "supports": "2021 AHA scientific statement via ADA: single-dose amoxicillin prophylaxis for at-risk patients; prophylaxis limited to defined high-risk cardiac conditions."},
    ],
    "metronidazole": [
        {"name": "NIH DailyMed — Metronidazole Tablet label",
         "url": _dailymed("cc004be0-da13-4b6b-83d5-d45b23fd37c9"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, warnings (incl. alcohol interaction), drug interactions."},
    ],
    "azithromycin": [
        {"name": "NIH DailyMed — Azithromycin Tablet label",
         "url": _dailymed("5f144e92-c9eb-420a-9bb8-4265a9f20a98"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, warnings, drug interactions."},
        {"name": "ADA — Antibiotic Prophylaxis Prior to Dental Procedures",
         "url": "https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis",
         "accessed": ACCESS_DATE,
         "supports": "2021 AHA scientific statement via ADA: azithromycin listed among oral alternatives for penicillin-allergic patients needing prophylaxis."},
    ],
    "erythromycin": [
        {"name": "NIH DailyMed — Erythromycin Ethylsuccinate Tablet label",
         "url": _dailymed("49b3ca93-43cc-439c-8f5d-e3ea2e87ad2f"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, warnings, drug interactions."},
    ],
    "clindamycin": [
        {"name": "NIH DailyMed — Clindamycin Hydrochloride Capsule label",
         "url": _dailymed("2367340c-d297-4a3f-8253-6d27a0ed39cb"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, warnings (incl. C. difficile-associated diarrhea), drug interactions."},
        {"name": "ADA — Antibiotic Prophylaxis Prior to Dental Procedures",
         "url": "https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis",
         "accessed": ACCESS_DATE,
         "supports": "2021 AHA scientific statement via ADA: clindamycin NO LONGER recommended as a prophylaxis alternative for penicillin-allergic patients (more frequent/severe reactions incl. C. difficile)."},
    ],
    "doxycycline": [
        {"name": "NIH DailyMed — Doxycycline Hyclate Capsule/Tablet label",
         "url": _dailymed("3e7cf78f-3b48-4614-9fa4-c6d1e0c05a35"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, warnings (incl. tooth discoloration, pregnancy), drug interactions."},
        {"name": "ADA — Antibiotic Prophylaxis Prior to Dental Procedures",
         "url": "https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis",
         "accessed": ACCESS_DATE,
         "supports": "2021 AHA scientific statement via ADA: doxycycline listed among oral alternatives for penicillin-allergic patients needing prophylaxis."},
    ],
    "ibuprofen": [
        {"name": "NIH DailyMed — Ibuprofen Tablet label",
         "url": _dailymed("8804564c-9e1b-43c1-8b58-fd6ace645f00"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, NSAID warnings (cardiovascular, GI, renal), drug interactions."},
    ],
    "paracetamol": [
        {"name": "NIH DailyMed — Acetaminophen Tablet label",
         "url": _dailymed("6176f9a2-6f2a-dcf6-e053-2a91aa0aee34"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, liver warnings, maximum daily dose, drug interactions."},
    ],
    "naproxen": [
        {"name": "NIH DailyMed — Naproxen Tablet label",
         "url": _dailymed("5ca1d392-ee02-3ce3-e063-6394a90a7827"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, NSAID warnings (cardiovascular, GI, renal), drug interactions."},
    ],
    "diclofenac": [
        {"name": "NIH DailyMed — Diclofenac Sodium Delayed-Release Tablet label",
         "url": _dailymed("5cd83a0b-d2ef-7c21-e063-6294a90a63fd"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, NSAID warnings (cardiovascular, GI, renal), drug interactions."},
    ],
    "triazolam": [
        {"name": "NIH DailyMed — Triazolam Tablet label",
         "url": _dailymed("5add318e-11b9-42f8-b052-0d8cebb32fcf"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, CNS-depression warnings, drug interactions."},
    ],
    "diazepam": [
        {"name": "NIH DailyMed — Diazepam (Valium) Tablet label",
         "url": _dailymed("260e2041-2bb3-482f-850e-b5d47a7bdbe6"),
         "accessed": ACCESS_DATE,
         "supports": "FDA-approved labeling: approved indications, dosing, contraindications, CNS-depression warnings, drug interactions."},
    ],
}

# Guidance-level sources cited by indication panels and cautions.
GENERAL_SOURCES: list[dict] = [
    {"name": "ADA — Antibiotic Prophylaxis Prior to Dental Procedures",
     "url": "https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis",
     "accessed": ACCESS_DATE,
     "supports": "2021 AHA scientific statement on infective-endocarditis prophylaxis: patient selection, regimens, clindamycin removal, cephalosporin caution."},
    {"name": "WHO — The AWaRe Antibiotic Book",
     "url": "https://www.who.int/publications/i/item/9789240062382",
     "accessed": ACCESS_DATE,
     "supports": "WHO AWaRe (Access, Watch, Reserve) antibiotic book: global guidance on first-line (Access) antibiotic selection for common infections."},
    {"name": "SDCEP — Antibiotic Prophylaxis Against Infective Endocarditis",
     "url": "https://www.sdcep.org.uk/published-guidance/antibiotic-prophylaxis/",
     "accessed": ACCESS_DATE,
     "supports": "Scottish Dental Clinical Effectiveness Programme implementation advice (2nd ed., March 2026) for dental teams on NICE CG64 prophylaxis against infective endocarditis."},
]


# Indication-based prescribing guidance. EDUCATES the choice; the dentist
# always selects and decides. Every item is reference info, source-cited.
INDICATIONS: dict[str, dict] = {
    "infection": {
        "display": "Dental infection",
        "first_line": [
            {"drug": "amoxicillin", "dosing": "500 mg three times daily, 3–5 days",
             "note": "First-line for odontogenic infections in non-allergic adults."},
        ],
        "alternatives": [
            {"drug": "azithromycin", "dosing": "500 mg day 1, then 250 mg days 2–5",
             "when": "Penicillin allergy."},
            {"drug": "clindamycin", "dosing": "300 mg four times daily, 3–5 days",
             "when": "True penicillin allergy (reserve; counsel on diarrhoea risk)."},
            {"drug": "metronidazole", "dosing": "400 mg three times daily, 3–5 days",
             "when": "Anaerobic cover; often added to amoxicillin."},
        ],
        "cautions": [
            "Confirm penicillin-allergy history before choosing a macrolide or clindamycin.",
            "Metronidazole: patient must avoid alcohol during treatment and 48h after.",
        ],
    },
    "prophylaxis": {
        "display": "Antibiotic prophylaxis (e.g. endocarditis-risk procedures)",
        "first_line": [
            {"drug": "amoxicillin", "dosing": "2 g orally, single dose 30–60 min before procedure",
             "note": "Standard single-dose prophylaxis in non-allergic adults. Source: ADA — Antibiotic Prophylaxis Prior to Dental Procedures."},
        ],
        "alternatives": [
            {"drug": "azithromycin", "dosing": "500 mg orally, single dose 30–60 min before",
             "when": "Penicillin allergy. Listed by the 2021 AHA statement (via ADA) among oral alternatives for penicillin-allergic patients."},
        ],
        "cautions": [
            "Prophylaxis is indicated only for defined at-risk patients — confirm the indication, not just the drug.",
            "Per the 2021 AHA scientific statement (via ADA), clindamycin is NO LONGER recommended as a prophylaxis alternative for penicillin-allergic patients — more frequent and severe reactions, including C. difficile infection.",
            "AHA-listed oral alternatives for penicillin-allergic patients: cephalexin (or other 1st/2nd-gen cephalosporin), azithromycin, clarithromycin, or doxycycline — confirm current dosing with the cited source; only azithromycin is covered in this reference panel.",
            "Do not use cephalosporins in patients with a history of anaphylaxis, angioedema, or urticaria with penicillin (2021 AHA statement via ADA).",
        ],
    },
    "post_op_pain": {
        "display": "Post-operative pain",
        "first_line": [
            {"drug": "ibuprofen", "dosing": "400 mg three times daily with food, shortest course",
             "note": "First-line dental pain control."},
        ],
        "alternatives": [
            {"drug": "paracetamol", "dosing": "500–1000 mg every 4–6 hours as needed (max 4 g/day)",
             "when": "NSAID contraindicated or not tolerated."},
            {"drug": "naproxen", "dosing": "500 mg twice daily with food",
             "when": "Longer-acting NSAID preferred."},
        ],
        "cautions": [
            "Avoid NSAIDs with anticoagulants, significant renal impairment, or active ulcer disease.",
            "Paracetamol: reduce maximum in liver disease.",
        ],
    },
    "anxiety": {
        "display": "Dental anxiety (conscious sedation)",
        "first_line": [
            {"drug": "triazolam", "dosing": "0.25 mg orally, 1 hour before appointment (single dose)",
             "note": "Short-acting; patient must be escorted."},
        ],
        "alternatives": [
            {"drug": "diazepam", "dosing": "5 mg the night before and/or 1 hour before",
             "when": "Longer anxiolytic effect desired."},
        ],
        "cautions": [
            "Single preoperative dosing only. Patient must not drive for 24 hours.",
            "Avoid combining with alcohol (additive CNS depression).",
        ],
    },
    "other": {
        "display": "Other / not listed",
        "first_line": [],
        "alternatives": [],
        "cautions": [
            "No indication-specific guidance in reference v2 — use the full reference panel and your clinical judgment.",
        ],
    },
}

INDICATION_ORDER = ["infection", "prophylaxis", "post_op_pain", "anxiety", "other"]


# name -> drug_key lookup including aliases
NAME_INDEX: dict[str, str] = {}
for _key, _entry in DRUGS.items():
    NAME_INDEX[_key] = _key
    for _alias in _entry["aliases"]:
        NAME_INDEX[_alias] = _key

# Common current-medication name -> class, for interaction matching.
MED_CLASS_MAP: dict[str, str] = {
    "warfarin": "anticoagulant",
    "apixaban": "anticoagulant",
    "rivaroxaban": "anticoagulant",
    "dabigatran": "anticoagulant",
    "edoxaban": "anticoagulant",
    "heparin": "anticoagulant",
    "aspirin": "antiplatelet",
    "clopidogrel": "antiplatelet",
    "ticagrelor": "antiplatelet",
}

# Interaction / condition rules. Each rule:
#   match: {"drug": key} | {"drug_class": class}
#   against: {"med": name} | {"med_class": class} | {"condition": name} | {"reports": field}
# Severity: "red" (do not proceed as entered) | "yellow" (caution / counsel).
RULES: list[dict] = [
    {
        "id": "nsaid-anticoagulant",
        "match": {"drug_class": "nsaid"},
        "against": {"med_class": "anticoagulant"},
        "severity": "red",
        "reason": "NSAIDs increase bleeding risk when combined with anticoagulants.",
        "source": "reference v2 — drug interaction",
    },
    {
        "id": "nsaid-antiplatelet",
        "match": {"drug_class": "nsaid"},
        "against": {"med_class": "antiplatelet"},
        "severity": "yellow",
        "reason": "Additive bleeding risk with antiplatelet therapy — use lowest effective NSAID dose and shortest course.",
        "source": "reference v2 — drug interaction",
    },
    {
        "id": "metronidazole-alcohol",
        "match": {"drug": "metronidazole"},
        "against": {"reports": "alcohol_use"},
        "severity": "red",
        "reason": "Disulfiram-like reaction risk: patient must avoid alcohol during treatment and for 48 hours after the last dose.",
        "source": "reference v2 — drug interaction",
    },
    {
        "id": "metronidazole-warfarin",
        "match": {"drug": "metronidazole"},
        "against": {"med_class": "anticoagulant"},
        "severity": "red",
        "reason": "Metronidazole can raise INR in patients on warfarin — monitor closely and consider alternative.",
        "source": "reference v2 — drug interaction",
    },
    {
        "id": "nsaid-renal",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "chronic kidney disease"},
        "severity": "red",
        "reason": "Avoid NSAIDs in significant renal impairment — risk of further kidney injury.",
        "source": "reference v2 — condition caution",
    },
    {
        "id": "nsaid-renal-2",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "renal impairment"},
        "severity": "red",
        "reason": "Avoid NSAIDs in significant renal impairment — risk of further kidney injury.",
        "source": "reference v2 — condition caution",
    },
    {
        "id": "nsaid-ulcer",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "stomach ulcer"},
        "severity": "yellow",
        "reason": "NSAIDs increase ulcer and GI-bleed risk — consider alternative or gastroprotection.",
        "source": "reference v2 — condition caution",
    },
    {
        "id": "nsaid-gibleed",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "gastrointestinal bleeding"},
        "severity": "yellow",
        "reason": "NSAIDs increase ulcer and GI-bleed risk — consider alternative or gastroprotection.",
        "source": "reference v2 — condition caution",
    },
    {
        "id": "tetracycline-pregnancy",
        "match": {"drug_class": "tetracycline"},
        "against": {"condition": "pregnancy"},
        "severity": "red",
        "reason": "Tetracyclines are contraindicated in pregnancy (risk of tooth discoloration and bone effects).",
        "source": "reference v2 — condition caution",
    },
    {
        "id": "paracetamol-liver",
        "match": {"drug": "paracetamol"},
        "against": {"condition": "liver disease"},
        "severity": "yellow",
        "reason": "Reduce the maximum daily paracetamol dose in liver disease and monitor.",
        "source": "reference v2 — condition caution",
    },
    {
        "id": "benzo-alcohol",
        "match": {"drug_class": "benzodiazepine"},
        "against": {"reports": "alcohol_use"},
        "severity": "yellow",
        "reason": "Additive CNS depression when benzodiazepines are combined with alcohol.",
        "source": "reference v2 — drug interaction",
    },
    {
        "id": "aspirin-allergy-nsaid",
        "match": {"drug_class": "nsaid"},
        "against": {"allergy": "aspirin"},
        "severity": "yellow",
        "reason": "Possible cross-reactivity in aspirin-sensitive patients — use NSAIDs with caution.",
        "source": "reference v2 — allergy cross-reactivity",
    },
]

# Counseling flags attached whenever these drugs are prescribed (informational).
COUNSEL_FLAGS: dict[str, str] = {
    "clindamycin": (
        "Counsel the patient: stop the drug and contact the clinic promptly if "
        "significant diarrhoea develops (C. difficile risk)."
    ),
    "metronidazole": (
        "Counsel the patient: avoid alcohol during treatment and for 48 hours "
        "after the last dose."
    ),
    "triazolam": (
        "Single preoperative dose only. Patient must be escorted and must not "
        "drive for 24 hours."
    ),
    "diazepam": (
        "Patient must not drive or operate machinery after dosing."
    ),
}


def lookup_drug(name: str) -> tuple[str, dict] | tuple[None, None]:
    """Normalize a drug name to (drug_key, entry), or (None, None)."""
    key = NAME_INDEX.get(name.strip().lower())
    if key is None:
        return None, None
    return key, DRUGS[key]


def med_class(med_name: str) -> str | None:
    return MED_CLASS_MAP.get(med_name.strip().lower())
