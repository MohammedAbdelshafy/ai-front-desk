"""Billing — provider-independent interface, TEST MODE ONLY.

No live charges are possible from this module. Every provider method
runs against a test stub. The founder wires a real provider (Whop,
Stripe, …) later by implementing BillingProvider; the app code calls
only this interface.

Test mode guarantees:
- create_checkout() returns a fake checkout URL, never a real one.
- No provider keys are read, stored, or required.
- subscribe()/cancel() flip local test-mode state only.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol

from .trial import SUBSCRIPTION_PRICE_USD

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


# The app uses this instance; swap for a real provider implementation later.
provider: BillingProvider = TestBillingProvider()
