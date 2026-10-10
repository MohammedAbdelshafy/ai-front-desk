"""Founder admin CLI for Mia Dental OS billing.

Manual Neteller billing means every subscription activation is a deliberate
human decision. Commands:

    python -m ai_front_desk.clinical.prescribe.admin list-pending
    python -m ai_front_desk.clinical.prescribe.admin status <email>
    python -m ai_front_desk.clinical.prescribe.admin activate <email>
    python -m ai_front_desk.clinical.prescribe.admin cancel <email>

Run these on the machine hosting the app (same PRESCRIBE_DB).
"""
from __future__ import annotations

import datetime
import os
import sys
import time
import uuid

from .accounts import AccountStore
from .trial import SUBSCRIPTION_PRICE_USD


def _store() -> AccountStore:
    db = os.environ.get("PRESCRIBE_DB") or os.path.expanduser(
        "~/.mia-prescribe/accounts.sqlite3"
    )
    return AccountStore(db)


def _fmt_ts(ts) -> str:
    if not ts:
        return "—"
    return datetime.datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M")


def cmd_list_pending(store: AccountStore) -> int:
    rows = store.pending_activations()
    if not rows:
        print("No accounts awaiting activation.")
        return 0
    print(f"{'EMAIL':<38} {'NAME':<22} {'CLINIC':<24} PENDING SINCE")
    for r in rows:
        print(
            f"{r['email']:<38} {r['name']:<22} {r['clinic_name']:<24} "
            f"{_fmt_ts(r['payment_pending_at'])}"
        )
    return 0


def cmd_status(store: AccountStore, email: str) -> int:
    acct = store.get_account_by_email(email)
    if acct is None:
        print(f"No account for {email}")
        return 1
    st = store.trial_status(acct["account_id"])
    print(f"Name:      {acct['name']}")
    print(f"Email:     {acct['email']}")
    print(f"Clinic:    {acct['clinic_name']}")
    print(f"Created:   {_fmt_ts(acct['created_at'])}")
    print(f"State:     {st['state']}")
    print(f"Price:     ${st['price_usd']}/month")
    if acct["payment_pending_at"]:
        print(f"Paid flag: {_fmt_ts(acct['payment_pending_at'])} (awaiting activation)")
    if acct["subscription_ref"]:
        print(f"Sub ref:   {acct['subscription_ref']} (since {_fmt_ts(acct['subscribed_at'])})")
    return 0


def cmd_activate(store: AccountStore, email: str) -> int:
    acct = store.get_account_by_email(email)
    if acct is None:
        print(f"No account for {email}")
        return 1
    ref = f"neteller-{uuid.uuid4().hex[:12]}"
    store.mark_subscribed(acct["account_id"], ref)
    print(f"Activated {email} — ref {ref} (${SUBSCRIPTION_PRICE_USD}/mo).")
    print("Confirm the Neteller transfer landed before running this.")
    return 0


def cmd_cancel(store: AccountStore, email: str) -> int:
    acct = store.get_account_by_email(email)
    if acct is None:
        print(f"No account for {email}")
        return 1
    store.mark_cancelled(acct["account_id"])
    print(f"Cancelled subscription for {email}. Records preserved.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in (
        "list-pending",
        "status",
        "activate",
        "cancel",
    ):
        print(__doc__)
        return 2
    store = _store()
    try:
        if argv[0] == "list-pending":
            return cmd_list_pending(store)
        if len(argv) < 2:
            print(f"Usage: admin.py {argv[0]} <email>")
            return 2
        email = argv[1].strip().lower()
        if argv[0] == "status":
            return cmd_status(store, email)
        if argv[0] == "activate":
            return cmd_activate(store, email)
        if argv[0] == "cancel":
            return cmd_cancel(store, email)
    finally:
        store.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
