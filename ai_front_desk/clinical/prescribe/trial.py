"""Trial + subscription state machine (server-side).

States: eligible -> active -> expiring -> expired -> subscribed / cancelled.

- eligible:    never activated on this install.
- active:     within the 7-day trial, more than 48h remaining.
- expiring:   trial active with <= 48h remaining (warn, don't surprise).
- expired:    trial over, no subscription. Paid features LOCKED, data
              preserved, upgrade screen shown. No charges, ever, from here.
- subscribed: test-mode subscription active (billing.py, TEST MODE ONLY).
- cancelled:  test-mode subscription was cancelled; back to locked.

All timestamps are server-side in a state file under
~/.mia-prescribe/ (or $PRESCRIBE_STATE_DIR). There is no client-side
state to reset, so reinstalling the client cannot restart the trial.

FOUNDERS CALL: SUBSCRIPTION_PRICE_USD below. Change the one constant.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# FOUNDER'S CALL — subscription price. Change this one constant.
SUBSCRIPTION_PRICE_USD = 99
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

TRIAL_DAYS = 7
EXPIRING_THRESHOLD_HOURS = 48
TRIAL_STATE_FILENAME = "trial.json"


def state_dir() -> Path:
    base = Path(
        os.environ.get("PRESCRIBE_STATE_DIR", str(Path.home() / ".mia-prescribe"))
    )
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return base


def state_path() -> Path:
    return state_dir() / TRIAL_STATE_FILENAME


def _write(payload: dict) -> None:
    path = state_path()
    path.write_text(json.dumps(payload))
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _read() -> dict | None:
    path = state_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (ValueError, TypeError):
        return None


def activate() -> dict:
    """Start the 7-day trial. Idempotent — first activation wins."""
    payload = _read()
    if payload and payload.get("activated_at"):
        return status()
    _write({"activated_at": time.time(), "trial_days": TRIAL_DAYS})
    return status()


def mark_subscribed(subscription_ref: str) -> dict:
    """Record a (test-mode) subscription. Called after billing confirms."""
    payload = _read() or {}
    payload["subscription_ref"] = subscription_ref
    payload["subscribed_at"] = time.time()
    payload.pop("cancelled_at", None)
    _write(payload)
    return status()


def mark_cancelled() -> dict:
    payload = _read() or {}
    payload["cancelled_at"] = time.time()
    _write(payload)
    return status()


def status(now: float | None = None) -> dict:
    """Full state machine. Pure function of the state file + clock."""
    now = time.time() if now is None else now
    return compute_status(_read(), now)


def compute_status(
    payload: dict | None, now: float, price_usd: int = SUBSCRIPTION_PRICE_USD
) -> dict:
    """Pure state machine over a payload dict.

    The file-based status() below and the per-account trial state in
    accounts.py both run through this function, so the semantics are
    identical everywhere. Payload keys: activated_at, trial_days,
    subscription_ref, subscribed_at, cancelled_at.
    """
    base = {"price_usd": price_usd}

    if payload and payload.get("cancelled_at") and not payload.get("subscription_ref"):
        # Cancelled without an active subscription -> locked like expired.
        return {**base, "state": "cancelled", "days_remaining": 0.0}
    if payload and payload.get("subscription_ref") and not payload.get("cancelled_at"):
        return {
            **base,
            "state": "subscribed",
            "days_remaining": 0.0,
            "subscription_ref": payload["subscription_ref"],
        }
    if payload and payload.get("cancelled_at"):
        return {**base, "state": "cancelled", "days_remaining": 0.0}

    if not payload or not payload.get("activated_at"):
        return {**base, "state": "eligible", "days_remaining": 0.0}

    try:
        activated_at = float(payload["activated_at"])
        trial_days = float(payload.get("trial_days", TRIAL_DAYS))
    except (ValueError, TypeError):
        return {**base, "state": "eligible", "days_remaining": 0.0}

    remaining_hours = (activated_at + trial_days * 86400 - now) / 3600.0
    if remaining_hours <= 0:
        return {**base, "state": "expired", "days_remaining": 0.0}
    if remaining_hours <= EXPIRING_THRESHOLD_HOURS:
        return {
            **base,
            "state": "expiring",
            "days_remaining": remaining_hours / 24.0,
            "hours_remaining": remaining_hours,
        }
    return {
        **base,
        "state": "active",
        "days_remaining": remaining_hours / 24.0,
        "hours_remaining": remaining_hours,
    }


def paid_features_unlocked(now: float | None = None) -> bool:
    """Gate for the copilot module. Trial (active/expiring) or subscribed."""
    return status(now)["state"] in ("active", "expiring", "subscribed")


def trial_active(now: float | None = None) -> bool:
    return status(now)["state"] in ("active", "expiring")
