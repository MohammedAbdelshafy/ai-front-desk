"""Billing — provider-independent interface, MANUAL NETELLER live path.

Live billing is manual: the dentist sends the subscription amount via
Neteller to NETELLER_EMAIL, marks "I've paid" in the app, and the founder
activates the account with the admin CLI. No provider API keys, no
webhooks, no automatic charges — every activation is a deliberate,
audited human decision.

TestBillingProvider remains for the test suite only; the app never
auto-subscribes from it anymore.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol

from .trial import SUBSCRIPTION_PRICE_USD

# Manual Neteller is the live billing path. TEST_MODE stays True only for the
# legacy test stub (kept for tests); the app no longer auto-subscribes.
TEST_MODE = True


@dataclass
class CheckoutSession:
    session_id: str
    price_usd: int
    test_mode: bool = True
    fake_checkout_url: str = ""
    created_at: float = field(default_factory=time.time)


class BillingProvider(Protocol):
    """Implement this to wire a real billing provider later."""

    def create_checkout(self, clinic_id: str, price_usd: int) -> CheckoutSession:
        ...

    def cancel_subscription(self, clinic_id: str, subscription_ref: str) -> bool:
        ...


class TestBillingProvider:
    """Test-mode stub. Never touches a real provider."""

    def __init__(self):
        self._subscriptions: dict[str, dict] = {}

    def create_checkout(self, clinic_id: str, price_usd: int) -> CheckoutSession:
        session_id = f"test_chk_{uuid.uuid4().hex[:12]}"
        return CheckoutSession(
            session_id=session_id,
            price_usd=price_usd,
            test_mode=True,
            fake_checkout_url=f"/billing/test-checkout/{session_id}",
        )

    def start_test_subscription(self, clinic_id: str) -> str:
        """Simulate a completed test checkout. Test mode only."""
        sub_ref = f"test_sub_{uuid.uuid4().hex[:12]}"
        self._subscriptions[clinic_id] = {
            "ref": sub_ref,
            "price_usd": SUBSCRIPTION_PRICE_USD,
            "started_at": time.time(),
            "test_mode": True,
        }
        return sub_ref

    def cancel_subscription(self, clinic_id: str, subscription_ref: str) -> bool:
        sub = self._subscriptions.get(clinic_id)
        if sub and sub["ref"] == subscription_ref:
            sub["cancelled_at"] = time.time()
            return True
        return False

    def subscription_for(self, clinic_id: str) -> dict | None:
        sub = self._subscriptions.get(clinic_id)
        if sub and "cancelled_at" not in sub:
            return sub
        return None


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# FOUNDER'S CALL — where dentists send subscription payments.
NETELLER_EMAIL = "abdelshafyclapps@gmail.com"
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


class ManualNetellerProvider:
    """Manual billing via Neteller wallet transfer.

    Flow: dentist sends SUBSCRIPTION_PRICE_USD via Neteller to NETELLER_EMAIL,
    clicks "I've paid" in the app -> account becomes payment-pending ->
    founder runs `python -m ai_front_desk.clinical.prescribe.admin activate
    <email>` -> account subscribed. No API keys, no webhooks, no chargebacks
    to handle in code. Honest and auditable.
    """

    def create_checkout(self, clinic_id: str, price_usd: int) -> CheckoutSession:
        # No hosted checkout — the "checkout" is the Neteller instruction page.
        return CheckoutSession(
            session_id=f"neteller_{uuid.uuid4().hex[:12]}",
            price_usd=price_usd,
            test_mode=False,
            fake_checkout_url="/subscribe",
        )

    def cancel_subscription(self, clinic_id: str, subscription_ref: str) -> bool:
        # Manual: founder cancels via the admin CLI.
        return False


# The app uses this instance; swap for a real provider implementation later.
# Manual Neteller is the live path — no test-mode auto-subscribe anymore.
provider: BillingProvider = ManualNetellerProvider()
