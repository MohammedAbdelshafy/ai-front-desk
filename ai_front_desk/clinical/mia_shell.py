"""MiaShell — reusable character + task-stage component (server side).

MiaShell separates the character presentation from permissions and data
access. A character manifest declares identity, theme, greeting, allowed
actions, domain packs, handoff rules and safety boundaries. Changing the
manifest never changes what the underlying system is allowed to do.

Task stages are honest: each stage transition must correspond to a real
application event. The shell never reports success before verification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


STAGES = (
    "idle",
    "listening",
    "planning",
    "working",
    "waiting_for_input",
    "awaiting_approval",
    "handing_off",
    "completed",
    "failed",
)


@dataclass(frozen=True)
class CharacterManifest:
    character_id: str
    name: str
    role: str
    greeting: str
    theme: str = "clinical"
    languages: tuple[str, ...] = ("en",)
    tone: str = "warm, professional, concise"
    allowed_actions: tuple[str, ...] = ()
    domain_pack_ids: tuple[str, ...] = ()
    handoff_rules: str = ""
    safety_boundaries: tuple[str, ...] = ()
    visual_asset: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "role": self.role,
            "greeting": self.greeting,
            "theme": self.theme,
            "languages": list(self.languages),
            "tone": self.tone,
            "allowed_actions": list(self.allowed_actions),
            "domain_pack_ids": list(self.domain_pack_ids),
            "handoff_rules": self.handoff_rules,
            "safety_boundaries": list(self.safety_boundaries),
            "visual_asset": self.visual_asset,
        }


DENTAL_MIA = CharacterManifest(
    character_id="dental-mia-v1",
    name="Dr. Mia",
    role="Dental clinical quality and evidence-linked prescribing copilot; supports patient intake workflows",
    greeting=(
        "Hi, I'm Dr. Mia, your AI dental assistant. I can guide you through "
        "pre-visit history or help a dentist review approved evidence. I'm an AI "
        "assistant, not a clinician, and I don't independently diagnose or prescribe. "
        "For personal clinical questions, please contact your dentist or clinic staff."
    ),
    allowed_actions=(
        "guide_intake", "answer_faq", "request_handoff",
        "prepare_quality_checklist", "retrieve_approved_evidence",
    ),
    domain_pack_ids=("dental-intake@1.0.0", "medication-evidence-review@0.1.0"),
    handoff_rules=(
        "Ask for human review on clinical questions, missing critical patient context, "
        "no verified evidence, or any request to independently choose or issue a prescription. "
        "Never represent an appointment request as a confirmed booking."
    ),
    safety_boundaries=(
        "Never independently diagnose, prescribe, calculate doses, or conclude a medicine is safe.",
        "Retrieve only approved, current, jurisdiction-matched evidence with source provenance; no approved evidence means no recommendation.",
        "Require treating/supervising dentist review for every clinical decision.",
        "Identify as an AI assistant, not a licensed clinician.",
        "Patient answers are recorded verbatim; summaries are labeled as AI-generated.",
    ),
)


class TaskStage:
    """Honest task-stage tracker. Transitions are recorded with timestamps and
    reasons; the UI renders these, never invented progress."""

    def __init__(self, manifest: CharacterManifest):
        self.manifest = manifest
        self.stage = "idle"
        self.history: list[dict[str, Any]] = []
        self.transition("idle", reason="initialized")

    def transition(self, stage: str, reason: str = "") -> None:
        if stage not in STAGES:
            raise ValueError(f"unknown stage: {stage}")
        self.stage = stage
        self.history.append({"stage": stage, "reason": reason, "at": time.time()})

    def to_dict(self) -> dict[str, Any]:
        return {
            "character": self.manifest.to_dict(),
            "stage": self.stage,
            "history": self.history,
        }
