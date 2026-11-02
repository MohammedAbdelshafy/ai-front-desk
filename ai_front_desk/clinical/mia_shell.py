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
    role="Clinic intake guide; specialty-specific forms are supplied by the clinic profile",
    greeting=(
        "Hi, I'm Dr. Mia. I'll guide you through the clinic's pre-visit history. "
        "Answer what you know, and ask the clinic team for help when needed."
    ),
    allowed_actions=("guide_intake", "answer_faq", "request_handoff"),
    domain_pack_ids=("dental-intake@1.0.0",),
    handoff_rules=(
        "On any request for a person, clinical question, or emergency wording: "
        "stop guiding, show handoff state, and direct the patient to clinic staff."
    ),
    safety_boundaries=(
        "Never diagnose, never recommend medication, never confirm appointments.",
        "Identify as an AI assistant, not a clinician.",
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
