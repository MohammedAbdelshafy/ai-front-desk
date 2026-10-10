"""Mia Dental OS — entry module: Mia Dental Prescribing Copilot.

Assistive reference aid for dentists. The dentist always decides and
prescribes; this module surfaces reference information and flags only.
Never autonomously prescribes, transmits, or fills a prescription.

Reference dataset lives in .reference_data (single source of truth);
this module re-exports the version and disclaimer so they cannot drift.
"""
from .reference_data import REFERENCE_VERSION, REFERENCE_DATE  # noqa: F401

REFERENCE_DISCLAIMER = (
    "Reference aid only — not a substitute for clinical judgment. "
    f"Dataset: {REFERENCE_VERSION}, requires dentist review before clinical use."
)
