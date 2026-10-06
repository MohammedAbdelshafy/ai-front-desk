"""ai_front_desk — WhatsApp AI front-desk: pure qualification state machine,
local Meta-webhook dev harness, and the n8n production workflow."""
from .logic import new_session, process_message

__version__ = "0.1.0"
__all__ = ["new_session", "process_message"]
