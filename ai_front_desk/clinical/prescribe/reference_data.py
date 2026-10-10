"""Reference v1 — standard dental prescribing references.

Conservative by design: only well-established dosing, contraindication,
and interaction facts are included. Anything uncertain is omitted.
Every entry is reference information, not a recommendation.
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

REFERENCE_VERSION = "reference v1"
REFERENCE_DATE = "2026-10-11"
# Every safety flag cites this dataset as e.g.
# "reference v1 (2026-10-11) — drug interaction".


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
        "source": "reference v1 — drug interaction",
    },
    {
        "id": "nsaid-antiplatelet",
        "match": {"drug_class": "nsaid"},
        "against": {"med_class": "antiplatelet"},
        "severity": "yellow",
        "reason": "Additive bleeding risk with antiplatelet therapy — use lowest effective NSAID dose and shortest course.",
        "source": "reference v1 — drug interaction",
    },
    {
        "id": "metronidazole-alcohol",
        "match": {"drug": "metronidazole"},
        "against": {"reports": "alcohol_use"},
        "severity": "red",
        "reason": "Disulfiram-like reaction risk: patient must avoid alcohol during treatment and for 48 hours after the last dose.",
        "source": "reference v1 — drug interaction",
    },
    {
        "id": "metronidazole-warfarin",
        "match": {"drug": "metronidazole"},
        "against": {"med_class": "anticoagulant"},
        "severity": "red",
        "reason": "Metronidazole can raise INR in patients on warfarin — monitor closely and consider alternative.",
        "source": "reference v1 — drug interaction",
    },
    {
        "id": "nsaid-renal",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "chronic kidney disease"},
        "severity": "red",
        "reason": "Avoid NSAIDs in significant renal impairment — risk of further kidney injury.",
        "source": "reference v1 — condition caution",
    },
    {
        "id": "nsaid-renal-2",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "renal impairment"},
        "severity": "red",
        "reason": "Avoid NSAIDs in significant renal impairment — risk of further kidney injury.",
        "source": "reference v1 — condition caution",
    },
    {
        "id": "nsaid-ulcer",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "stomach ulcer"},
        "severity": "yellow",
        "reason": "NSAIDs increase ulcer and GI-bleed risk — consider alternative or gastroprotection.",
        "source": "reference v1 — condition caution",
    },
    {
        "id": "nsaid-gibleed",
        "match": {"drug_class": "nsaid"},
        "against": {"condition": "gastrointestinal bleeding"},
        "severity": "yellow",
        "reason": "NSAIDs increase ulcer and GI-bleed risk — consider alternative or gastroprotection.",
        "source": "reference v1 — condition caution",
    },
    {
        "id": "tetracycline-pregnancy",
        "match": {"drug_class": "tetracycline"},
        "against": {"condition": "pregnancy"},
        "severity": "red",
        "reason": "Tetracyclines are contraindicated in pregnancy (risk of tooth discoloration and bone effects).",
        "source": "reference v1 — condition caution",
    },
    {
        "id": "paracetamol-liver",
        "match": {"drug": "paracetamol"},
        "against": {"condition": "liver disease"},
        "severity": "yellow",
        "reason": "Reduce the maximum daily paracetamol dose in liver disease and monitor.",
        "source": "reference v1 — condition caution",
    },
    {
        "id": "benzo-alcohol",
        "match": {"drug_class": "benzodiazepine"},
        "against": {"reports": "alcohol_use"},
        "severity": "yellow",
        "reason": "Additive CNS depression when benzodiazepines are combined with alcohol.",
        "source": "reference v1 — drug interaction",
    },
    {
        "id": "aspirin-allergy-nsaid",
        "match": {"drug_class": "nsaid"},
        "against": {"allergy": "aspirin"},
        "severity": "yellow",
        "reason": "Possible cross-reactivity in aspirin-sensitive patients — use NSAIDs with caution.",
        "source": "reference v1 — allergy cross-reactivity",
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
