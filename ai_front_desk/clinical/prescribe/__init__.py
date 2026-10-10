"""Mia Dental OS — entry module: Mia Dental Prescribing Copilot.

Assistive reference aid for dentists. The dentist always decides and
prescribes; this module surfaces reference information and flags only.
Never autonomously prescribes, transmits, or fills a prescription.

Reference dataset: "reference v1" — standard, well-established dental
prescribing references. Labeled as requiring dentist review before any
clinical use. Uncertain rules are omitted, not guessed.
"""

REFERENCE_VERSION = "reference v1"
REFERENCE_DISCLAIMER = (
    "Reference aid only — not a substitute for clinical judgment. "
    "Dataset: reference v1, requires dentist review before clinical use."
)
