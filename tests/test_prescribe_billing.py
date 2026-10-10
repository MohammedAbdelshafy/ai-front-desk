"""Billing is TEST MODE ONLY — no live charges, no provider keys."""
from ai_front_desk.clinical.prescribe import billing
from ai_front_desk.clinical.prescribe.trial import SUBSCRIPTION_PRICE_USD


def test_test_mode_flag():
    assert billing.TEST_MODE is True


def test_checkout_is_fake():
    s = billing.provider.create_checkout("clinic-a", SUBSCRIPTION_PRICE_USD)
    assert s.test_mode is True
    assert s.price_usd == 99
    assert "test" in s.fake_checkout_url
    assert "http" not in s.fake_checkout_url  # never a real provider URL


def test_test_subscription_lifecycle():
    p = billing.TestBillingProvider()
    ref = p.start_test_subscription("clinic-a")
    assert p.subscription_for("clinic-a")["ref"] == ref
    assert p.cancel_subscription("clinic-a", ref) is True
    assert p.subscription_for("clinic-a") is None
