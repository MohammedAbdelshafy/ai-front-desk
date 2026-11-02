"""Founder admin CLI for Mia Dental OS billing.

Manual Neteller billing means every subscription activation is a deliberate
human decision. Commands:

    python -m ai_front_desk.clinical.prescribe.admin list-pending
    python -m ai_front_desk.clinical.prescribe.admin status <email>
    python -m ai_front_desk.clinical.prescribe.admin activate <email>
    python -m ai_front_desk.clinical.prescribe.admin cancel <email>
    python -m ai_front_desk.clinical.prescribe.admin backup <dest-dir>

Run these on the machine hosting the app (same PRESCRIBE_DB).

Restore: stop the app, copy the backup file back over the live database
path, restart. One paragraph, full procedure — see
docs/engineering/RELIABILITY.md ("Can't lose info").
"""
from __future__ import annotations

import datetime
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path

from .accounts import AccountStore
from .trial import SUBSCRIPTION_PRICE_USD


def _db_path() -> Path:
    # Same default as server.DB_PATH — accounts and clinical data share one file.
    return Path(
        os.environ.get(
            "PRESCRIBE_DB",
            os.path.expanduser("~/.mia-prescribe/prescribe-demo.sqlite3"),
        )
    ).expanduser()


def _store() -> AccountStore:
    return AccountStore(_db_path())


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


def cmd_backup(store: AccountStore, dest: str) -> int:
    """Hot backup via the SQLite backup API (safe while the app is running).

    Copies the live database — including WAL content — into a single
    self-contained file. Works while the server is serving traffic.
    """
    dest_path = Path(dest).expanduser()
    if dest_path.is_dir():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        dest_path = dest_path / f"mia-dental-os-backup-{stamp}.sqlite3"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(_db_path()), timeout=10.0)
    try:
        dst = sqlite3.connect(str(dest_path))
        try:
            # pages=-1 copies everything; sleep keeps the lock short per step.
            src.backup(dst, pages=-1, sleep=0.05)
        finally:
            dst.close()
    finally:
        src.close()
    # Verify the backup opens and has our tables.
    chk = sqlite3.connect(str(dest_path))
    try:
        tables = {
            r[0]
            for r in chk.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        chk.close()
    missing = {"prescribe_accounts", "prescribe_patients"} - tables
    if missing:
        print(f"Backup written but missing tables: {sorted(missing)}")
        return 1
    print(f"Backup OK: {dest_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in (
        "list-pending",
        "status",
        "activate",
        "cancel",
        "backup",
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
        if argv[0] == "backup":
            if len(argv) < 2:
                print("Usage: admin.py backup <dest-dir-or-file>")
                return 2
            return cmd_backup(store, argv[1])
    finally:
        store.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
