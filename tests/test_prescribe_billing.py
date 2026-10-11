"""Manual Neteller billing — no provider API, no automatic charges.

Flow: dentist sends the subscription amount via Neteller to NETELLER_EMAIL,
clicks "I've paid" -> account is payment-pending -> founder activates via
the admin CLI. Every activation is a deliberate, audited human decision.
"""
from ai_front_desk.clinical.prescribe import billing
from ai_front_desk.clinical.prescribe.trial import SUBSCRIPTION_PRICE_USD


def test_neteller_email_is_set():
    assert billing.NETELLER_EMAIL == "abdelshafyclapps@gmail.com"
    assert "@" in billing.NETELLER_EMAIL


def test_live_provider_is_manual_neteller():
    assert isinstance(billing.provider, billing.ManualNetellerProvider)


def test_manual_checkout_points_at_subscribe_page():
    s = billing.provider.create_checkout("clinic-a", SUBSCRIPTION_PRICE_USD)
    assert s.test_mode is False
    assert s.price_usd == SUBSCRIPTION_PRICE_USD
    assert s.fake_checkout_url == "/subscribe"
    assert "http" not in s.fake_checkout_url  # never a real provider URL


def test_manual_provider_never_auto_subscribes():
    # The live provider has no start_test_subscription — the app cannot
    # subscribe anyone by itself.
    assert not hasattr(billing.provider, "start_test_subscription")


def test_test_stub_still_exists_for_tests():
    p = billing.TestBillingProvider()
    ref = p.start_test_subscription("clinic-a")
    assert p.subscription_for("clinic-a")["ref"] == ref
    assert p.cancel_subscription("clinic-a", ref) is True
    assert p.subscription_for("clinic-a") is None
