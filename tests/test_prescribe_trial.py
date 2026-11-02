"""Tests for the trial state machine (server-side)."""
import time

import pytest

from ai_front_desk.clinical.prescribe import trial


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("PRESCRIBE_STATE_DIR", str(tmp_path / "state"))
    yield


def test_eligible_before_activation():
    s = trial.status()
    assert s["state"] == "eligible"
    assert not trial.paid_features_unlocked()


def test_activation_starts_trial():
    s = trial.activate()
    assert s["state"] == "active"
    assert s["days_remaining"] > 6.9
    assert trial.paid_features_unlocked()
    assert trial.trial_active()


def test_activation_is_idempotent():
    first = trial.activate()
    time.sleep(0.01)
    second = trial.activate()
    assert second["state"] == "active"
    # first activation wins: days remaining did not reset upward materially
    assert abs(first["days_remaining"] - second["days_remaining"]) < 0.01


def test_expiring_within_48h():
    trial.activate()
    # 7 days minus 6 days = 1 day left -> expiring
    s = trial.status(now=time.time() + 6 * 86400)
    assert s["state"] == "expiring"
    assert trial.paid_features_unlocked(now=time.time() + 6 * 86400)


def test_expired_locks_features():
    trial.activate()
    s = trial.status(now=time.time() + 8 * 86400)
    assert s["state"] == "expired"
    assert not trial.paid_features_unlocked(now=time.time() + 8 * 86400)


def test_subscribed_unlocks():
    trial.activate()
    trial.mark_subscribed("test_sub_123")
    s = trial.status()
    assert s["state"] == "subscribed"
    assert trial.paid_features_unlocked()


def test_cancelled_locks_again():
    trial.activate()
    trial.mark_subscribed("test_sub_123")
    trial.mark_cancelled()
    s = trial.status()
    assert s["state"] == "cancelled"
    assert not trial.paid_features_unlocked()


def test_price_constant_is_founder_call():
    assert trial.SUBSCRIPTION_PRICE_USD == 99
