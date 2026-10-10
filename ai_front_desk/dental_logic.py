"""Dental-specific domain logic for AI Front Desk MVP.

This module is deliberately separate from the generic reference flow and makes
no network calls. It handles administrative intake only, not clinical triage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


URGENT_HANDOFF_TEXT = (
    "I'm an administrative assistant, not a clinician. If you believe this is "
    "a medical emergency, contact local emergency services. For a dental concern, "
    "please call the clinic directly so the team can advise you. I can also ask "
    "the clinic team to contact you."
)


@dataclass(frozen=True)
class ClinicConfig:
    clinic_id: str
    name: str
    timezone: str
    phone: str
    address: str
    hours: str
    booking_url: str = ""
    services: tuple[str, ...] = ()
    languages: tuple[str, ...] = ("en",)
    approved_faqs: dict[str, str] = field(default_factory=dict)
    handoff_message: str = (
        "I'll pass this request to the clinic team. A team member will follow up "
        "using the contact method you provide."
    )


def new_dental_session(sender_id: str, clinic_id: str) -> dict[str, Any]:
    """Create JSON-serializable intake state; do not store the message body here."""
    return {
        "sender_id": sender_id,
        "clinic_id": clinic_id,
        "stage": "welcome",
        "name": "",
        "intent": "",
        "preferred_time": "",
        "callback_method": "",
        "consent_to_follow_up": None,
        "handoff_required": False,
        "failed_attempts": 0,
        "last_message_id": "",
    }


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    lower = text.casefold()
    return any(p.casefold() in lower for p in phrases)


def _approved_faq(text: str, config: ClinicConfig) -> str | None:
    lower = text.casefold()
    # Only return approved clinic-owned content, never fabricated defaults.
    for question, answer in config.approved_faqs.items():
        if question.casefold() in lower and answer.strip():
            return answer
    return None


def process_dental_message(
    state: dict[str, Any], text: str, config: ClinicConfig
) -> tuple[dict[str, Any], str, bool, str]:
    """Return (state, reply, handoff_required, stage), without external side effects."""
    if state.get("clinic_id") != config.clinic_id:
        # Fail closed rather than allowing cross-tenant state reuse.
        clean = new_dental_session(str(state.get("sender_id", "")), config.clinic_id)
        return clean, (
            "I couldn't match this conversation to the right clinic. "
            "I'll ask the team to help."
        ), True, "handoff"

    state = dict(state)
    text = (text or "").strip()
    state["handoff_required"] = False

    if _contains_any(text, (
        "human", "person", "receptionist", "staff", "call me",
        "speak to someone", "talk to someone",
    )):
        state["stage"] = "handoff"
        state["handoff_required"] = True
        return state, config.handoff_message, True, "handoff"

    # Route symptom-like/clinical messages to people. This intentionally is
    # conservative keyword routing, not diagnosis or a validated triage model.
    if _contains_any(text, (
        "toothache", "tooth pain", "swelling", "bleeding", "abscess",
        "injury", "knocked out", "broken tooth", "can't breathe",
        "cannot breathe", "fever", "pain is severe", "severe pain",
    )):
        state["stage"] = "clinical_handoff"
        state["handoff_required"] = True
        return state, URGENT_HANDOFF_TEXT, True, "clinical_handoff"

    faq = _approved_faq(text, config)
    if faq:
        return state, faq, False, state.get("stage", "welcome")

    stage = state.get("stage", "welcome")
    if not text:
        return state, "Please send your question again, or ask for the clinic team.", False, stage

    if stage == "welcome":
        state["stage"] = "collect_intent"
        return state, (
            f"Hello! I'm the administrative assistant for {config.name}. "
            "I can help with clinic information or pass an appointment request "
            "to the team. What can we help you with?"
        ), False, "collect_intent"

    if stage == "collect_intent":
        state["intent"] = text[:300]
        state["stage"] = "collect_time"
        return state, (
            "Thanks. Would you prefer a particular day or time? "
            "Please don't include sensitive medical details here."
        ), False, "collect_time"

    if stage == "collect_time":
        state["preferred_time"] = text[:120]
        state["stage"] = "collect_callback"
        options = "phone or WhatsApp"
        return state, (
            f"Noted as a request, not a confirmed booking. How should the clinic "
            f"team contact you: {options}? Reply 'phone' or 'WhatsApp'."
        ), False, "collect_callback"

    if stage == "collect_callback":
        lower = text.casefold()
        if "phone" not in lower and "whatsapp" not in lower:
            state["failed_attempts"] = int(state.get("failed_attempts", 0)) + 1
            if state["failed_attempts"] >= 2:
                state["stage"] = "handoff"
                state["handoff_required"] = True
                return state, config.handoff_message, True, "handoff"
            return state, "Please choose phone or WhatsApp, or ask for the clinic team.", False, stage
        state["callback_method"] = "WhatsApp" if "whatsapp" in lower else "phone"
        state["stage"] = "consent"
        return state, (
            "May I pass this appointment request and your preferred contact method "
            "to the clinic team so they can follow up? Reply yes or no."
        ), False, "consent"

    if stage == "consent":
        lower = text.casefold()
        if lower in {"yes", "yes please", "i agree", "ok", "okay"}:
            state["consent_to_follow_up"] = True
            state["stage"] = "handoff"
            state["handoff_required"] = True
            return state, (
                "Thank you. Your request will be passed to the clinic team. "
                "This is not a confirmed appointment."
            ), True, "handoff"
        if lower in {"no", "no thanks", "i do not agree", "don't agree"}:
            state["consent_to_follow_up"] = False
            state["stage"] = "done"
            return state, (
                "Understood. I won't submit a follow-up request. You can contact "
                "the clinic directly using its published contact details."
            ), False, "done"
        return state, "Please reply yes or no so I can handle your request correctly.", False, stage

    if stage in {"handoff", "clinical_handoff", "done"}:
        return state, (
            "Your message has been directed to the clinic workflow. "
            "Please contact the clinic directly if you need timely assistance."
        ), bool(state.get("handoff_required")), stage

    state["stage"] = "welcome"
    return state, f"Hello! I'm the administrative assistant for {config.name}.", False, "welcome"
