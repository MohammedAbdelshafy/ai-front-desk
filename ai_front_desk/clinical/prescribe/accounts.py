"""Accounts: sign-up, sign-in, sessions, per-account trial state.

Demo-grade auth (NOT production auth):
- Passwords: PBKDF2-HMAC-SHA256, 200k iterations, per-user random salt.
  Plaintext is never stored or logged.
- Sessions: server-side, token hashed with SHA-256 before storage, 24h
  expiry with sliding refresh, HttpOnly SameSite=Lax cookie.
- Sign-in is rate-limited per email (10 fails / 10 min -> temp lock).
- Trial state lives on the account row (7x24h from sign-up, server clock).

Pre-production follow-ups (NOT built here): email verification,
password reset, 2FA, breach monitoring, production session rotation.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
import uuid
from pathlib import Path
from typing import Any

from . import trial as _trial
from .store import LockedConnection

# --- constants ---------------------------------------------------------

PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_CHARS = 10
SESSION_TTL_SECONDS = 24 * 3600
DEMO_SESSION_TTL_SECONDS = 2 * 3600
# Absolute cap: sliding refresh can never extend a session past this.
SESSION_ABSOLUTE_MAX_SECONDS = 7 * 24 * 3600
SLIDING_REFRESH_SECONDS = 300
SIGNIN_MAX_FAILS = 10
SIGNUP_MAX_PER_HOUR = 5
SIGNIN_WINDOW_SECONDS = 600
SIGNIN_LOCK_SECONDS = 600

DEMO_ACCOUNT_ID = "demo"
DEMO_CLINIC_ID = "demo-explore"
DEMO_CLINIC_NAME = "Explore demo"
DEMO_EMAIL = "demo@localhost"

EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS prescribe_accounts (
    account_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL,          -- stored lowercased; UNIQUE index below
    clinic_name  TEXT NOT NULL,
    clinic_id    TEXT NOT NULL,          -- data namespace: account_id, or demo-explore
    password_hash TEXT NOT NULL,        -- pbkdf2-sha256$iter$salt_hex$hash_hex ('!' for demo)
    is_demo      INTEGER NOT NULL DEFAULT 0,
    trial_activated_at REAL NOT NULL,
    trial_days   REAL NOT NULL DEFAULT 7,
    subscription_ref TEXT,
    subscribed_at REAL,
    cancelled_at REAL,
    created_at   REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pacct_email ON prescribe_accounts(email);
CREATE TABLE IF NOT EXISTS prescribe_sessions (
    token_hash  TEXT PRIMARY KEY,        -- sha256 hex of the bearer token
    account_id  TEXT NOT NULL,
    csrf_token  TEXT NOT NULL DEFAULT '', -- per-session CSRF secret (random)
    created_at  REAL NOT NULL,
    last_seen   REAL NOT NULL,
    expires_at  REAL NOT NULL,
    FOREIGN KEY (account_id) REFERENCES prescribe_accounts(account_id)
);
CREATE INDEX IF NOT EXISTS idx_psess_acct ON prescribe_sessions(account_id);
CREATE TABLE IF NOT EXISTS prescribe_signin_attempts (
    email        TEXT PRIMARY KEY,       -- lowercased
    fails        INTEGER NOT NULL DEFAULT 0,
    first_fail_at REAL NOT NULL DEFAULT 0,
    locked_until REAL NOT NULL DEFAULT 0,
    updated_at   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS prescribe_signup_attempts (
    ip           TEXT PRIMARY KEY,
    count        INTEGER NOT NULL DEFAULT 0,
    window_start REAL NOT NULL DEFAULT 0
);
"""


# --- password hashing ---------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2-sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2-sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"),
            bytes.fromhex(salt_hex), int(iters),
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or "")) and len(email) <= 254


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# --- store ---------------------------------------------------------------

class AccountStore:
    def __init__(self, db_path: str | Path):
        import sqlite3

        self.path = Path(db_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        conn = sqlite3.connect(str(self.path), timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self._db = LockedConnection(conn)
        # Same performance/durability contract as store.py — see
        # docs/engineering/RELIABILITY.md. Both stores share one SQLite file.
        self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("PRAGMA synchronous = NORMAL")
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA busy_timeout = 5000")
        self._db.executescript(SCHEMA)
        self._db.commit()
        self._migrate()
        self.ensure_demo_account()

    def _migrate(self) -> None:
        """Idempotent column migrations."""
        acct_cols = {
            r["name"]
            for r in self._db.execute("PRAGMA table_info(prescribe_accounts)")
        }
        # Manual Neteller billing: dentist paid, awaiting founder activation.
        if "payment_pending_at" not in acct_cols:
            self._db.execute(
                "ALTER TABLE prescribe_accounts ADD COLUMN payment_pending_at REAL"
            )
            self._db.commit()
        sess_cols = {
            r["name"]
            for r in self._db.execute("PRAGMA table_info(prescribe_sessions)")
        }
        # Per-session CSRF secret.
        if "csrf_token" not in sess_cols:
            self._db.execute(
                "ALTER TABLE prescribe_sessions ADD COLUMN csrf_token TEXT NOT NULL DEFAULT ''"
            )
            self._db.commit()
            # Backfill: existing sessions get a fresh random token each.
            for (th,) in self._db.execute("SELECT token_hash FROM prescribe_sessions"):
                self._db.execute(
                    "UPDATE prescribe_sessions SET csrf_token = ? WHERE token_hash = ?",
                    (secrets.token_urlsafe(32), th),
                )
            self._db.commit()
        # Legal acceptance: doc version + timestamp recorded at sign-up.
        if "legal_accepted_version" not in acct_cols:
            self._db.execute(
                "ALTER TABLE prescribe_accounts ADD COLUMN legal_accepted_version TEXT"
            )
            self._db.commit()
        if "legal_accepted_at" not in acct_cols:
            self._db.execute(
                "ALTER TABLE prescribe_accounts ADD COLUMN legal_accepted_at REAL"
            )
            self._db.commit()

    def close(self):
        self._db.close()

    # -- accounts ------------------------------------------------------
    def create_account(self, name: str, email: str, clinic_name: str,
                       password: str, legal_version: str = "") -> dict[str, Any]:
        """Validate + create. Raises ValueError with a user-safe message."""
        name = (name or "").strip()
        email = (email or "").strip().lower()
        clinic_name = (clinic_name or "").strip()
        if not name or len(name) > 80:
            raise ValueError("Please enter your name.")
        if not valid_email(email):
            raise ValueError("That email address doesn't look valid.")
        if not clinic_name or len(clinic_name) > 80:
            raise ValueError("Please enter your clinic name.")
        if len(password or "") < MIN_PASSWORD_CHARS:
            raise ValueError(f"Password needs at least {MIN_PASSWORD_CHARS} characters.")
        if self.get_account_by_email(email) is not None:
            raise ValueError("An account with this email already exists — try signing in.")
        account_id = _new_id("acct")
        now = time.time()
        self._db.execute(
            """INSERT INTO prescribe_accounts
               (account_id, name, email, clinic_name, clinic_id, password_hash,
                is_demo, trial_activated_at, trial_days, created_at,
                legal_accepted_version, legal_accepted_at)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?, 7, ?, ?, ?)""",
            (account_id, name, email, clinic_name, account_id,
             hash_password(password), now, now, legal_version, now),
        )
        self._db.commit()
        return self.get_account(account_id)

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM prescribe_accounts WHERE account_id = ?",
            (account_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_account_by_email(self, email: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM prescribe_accounts WHERE email = ?",
            ((email or "").strip().lower(),),
        ).fetchone()
        return dict(row) if row else None

    def ensure_demo_account(self) -> dict[str, Any]:
        row = self.get_account(DEMO_ACCOUNT_ID)
        if row:
            return row
        now = time.time()
        self._db.execute(
            """INSERT OR IGNORE INTO prescribe_accounts
               (account_id, name, email, clinic_name, clinic_id, password_hash,
                is_demo, trial_activated_at, trial_days, created_at)
               VALUES (?, ?, ?, ?, ?, '!', 1, ?, 7, ?)""",
            (DEMO_ACCOUNT_ID, "Demo Explorer", DEMO_EMAIL,
             DEMO_CLINIC_NAME, DEMO_CLINIC_ID, now, now),
        )
        self._db.commit()
        return self.get_account(DEMO_ACCOUNT_ID)

    # -- trial / subscription (per account) ------------------------------
    @staticmethod
    def _trial_payload(acct: dict[str, Any]) -> dict:
        return {
            "activated_at": acct["trial_activated_at"],
            "trial_days": acct["trial_days"],
            "subscription_ref": acct["subscription_ref"],
            "subscribed_at": acct["subscribed_at"],
            "cancelled_at": acct["cancelled_at"],
            "payment_pending_at": acct["payment_pending_at"]
            if "payment_pending_at" in acct.keys()
            else None,
        }

    def trial_status(self, account_id: str, now: float | None = None) -> dict:
        acct = self.get_account(account_id)
        if acct is None:
            raise KeyError(f"unknown account {account_id}")
        st = _trial.compute_status(
            self._trial_payload(acct), time.time() if now is None else now
        )
        if acct["is_demo"]:
            st = {**st, "state": "active", "days_remaining": float("inf"),
                  "is_demo": True}
        return st

    def trial_unlocked(self, account_id: str, now: float | None = None) -> bool:
        acct = self.get_account(account_id)
        if acct is None:
            return False
        if acct["is_demo"]:
            return True
        return self.trial_status(account_id, now)["state"] in (
            "active", "expiring", "subscribed")

    def mark_payment_pending(self, account_id: str) -> None:
        """Dentist clicked 'I've paid via Neteller' — awaiting founder activation.

        Invalid transition guard: an already-subscribed account can never go
        back to pending (see docs/engineering/RELIABILITY.md).
        """
        acct = self.get_account(account_id)
        if acct is None:
            raise KeyError(f"unknown account {account_id}")
        if acct["subscription_ref"] and not acct["cancelled_at"]:
            raise ValueError("account is already subscribed — cannot go back to pending")
        self._db.execute(
            "UPDATE prescribe_accounts SET payment_pending_at = ? WHERE account_id = ?",
            (time.time(), account_id),
        )
        self._db.commit()

    def clear_payment_pending(self, account_id: str) -> None:
        self._db.execute(
            "UPDATE prescribe_accounts SET payment_pending_at = NULL WHERE account_id = ?",
            (account_id,),
        )
        self._db.commit()

    def pending_activations(self) -> list[dict[str, Any]]:
        """Accounts awaiting founder activation (for the admin CLI)."""
        return [
            dict(r)
            for r in self._db.execute(
                "SELECT account_id, name, email, clinic_name, payment_pending_at, created_at"
                " FROM prescribe_accounts WHERE payment_pending_at IS NOT NULL"
                " AND subscription_ref IS NULL ORDER BY payment_pending_at"
            )
        ]

    def mark_subscribed(self, account_id: str, subscription_ref: str) -> None:
        self._db.execute(
            "UPDATE prescribe_accounts SET subscription_ref = ?, subscribed_at = ?, "
            "cancelled_at = NULL, payment_pending_at = NULL WHERE account_id = ?",
            (subscription_ref, time.time(), account_id),
        )
        self._db.commit()

    def mark_cancelled(self, account_id: str) -> None:
        self._db.execute(
            "UPDATE prescribe_accounts SET cancelled_at = ? WHERE account_id = ?",
            (time.time(), account_id),
        )
        self._db.commit()

    def set_trial_start(self, account_id: str, activated_at: float) -> None:
        """Admin/test helper: move the trial clock for an account."""
        self._db.execute(
            "UPDATE prescribe_accounts SET trial_activated_at = ? WHERE account_id = ?",
            (activated_at, account_id),
        )
        self._db.commit()

    # -- sessions --------------------------------------------------------
    def create_session(self, account_id: str,
                       ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
        # Fresh random bearer token on EVERY signin — a stolen/old token can
        # never be reused to fixate a session (see RELIABILITY.md).
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        now = time.time()
        self._db.execute(
            "INSERT INTO prescribe_sessions (token_hash, account_id, csrf_token, "
            "created_at, last_seen, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (_token_hash(token), account_id, csrf, now, now, now + ttl_seconds),
        )
        self._db.commit()
        return token

    def csrf_token_for(self, token: str) -> str | None:
        """Return the CSRF secret bound to a bearer token (for form builders)."""
        if not token:
            return None
        row = self._db.execute(
            "SELECT csrf_token FROM prescribe_sessions WHERE token_hash = ?",
            (_token_hash(token),),
        ).fetchone()
        return row["csrf_token"] if row and row["csrf_token"] else None

    def session_ctx(self, token: str) -> dict[str, Any] | None:
        """Validate a bearer token -> auth context dict, or None.

        Refreshes the sliding window on activity. Never logs the token.
        """
        if not token:
            return None
        th = _token_hash(token)
        row = self._db.execute(
            "SELECT * FROM prescribe_sessions WHERE token_hash = ?", (th,)
        ).fetchone()
        if row is None:
            return None
        now = time.time()
        if row["expires_at"] <= now or now - row["created_at"] > SESSION_ABSOLUTE_MAX_SECONDS:
            self._db.execute(
                "DELETE FROM prescribe_sessions WHERE token_hash = ?", (th,))
            self._db.commit()
            return None
        acct = self.get_account(row["account_id"])
        if acct is None:
            return None
        if now - row["last_seen"] > SLIDING_REFRESH_SECONDS:
            self._db.execute(
                "UPDATE prescribe_sessions SET last_seen = ?, expires_at = ? "
                "WHERE token_hash = ?",
                (now, now + SESSION_TTL_SECONDS, th),
            )
            self._db.commit()
        trial = self.trial_status(acct["account_id"], now)
        return {
            "csrf_token": row["csrf_token"] or "",
            "account_id": acct["account_id"],
            "clinic_id": acct["clinic_id"],
            "clinic_name": acct["clinic_name"],
            "name": acct["name"],
            "email": acct["email"],
            "is_demo": bool(acct["is_demo"]),
            "trial": trial,
            "unlocked": bool(acct["is_demo"]) or trial["state"] in (
                "active", "expiring", "subscribed"),
        }

    def destroy_session(self, token: str) -> None:
        if token:
            self._db.execute(
                "DELETE FROM prescribe_sessions WHERE token_hash = ?",
                (_token_hash(token),))
            self._db.commit()

    # -- sign-in rate limiting -------------------------------------------
    def signin_allowed(self, email: str) -> tuple[bool, float]:
        """(allowed, seconds_remaining_on_lock)."""
        row = self._db.execute(
            "SELECT * FROM prescribe_signin_attempts WHERE email = ?",
            ((email or "").strip().lower(),),
        ).fetchone()
        if row and row["locked_until"] > time.time():
            return False, row["locked_until"] - time.time()
        return True, 0.0

    def record_signin_failure(self, email: str) -> None:
        key = (email or "").strip().lower()
        now = time.time()
        row = self._db.execute(
            "SELECT * FROM prescribe_signin_attempts WHERE email = ?", (key,)
        ).fetchone()
        if row is None or now - row["first_fail_at"] > SIGNIN_WINDOW_SECONDS:
            fails, first = 1, now
        else:
            fails, first = row["fails"] + 1, row["first_fail_at"]
        locked_until = now + SIGNIN_LOCK_SECONDS if fails >= SIGNIN_MAX_FAILS else 0.0
        self._db.execute(
            "INSERT OR REPLACE INTO prescribe_signin_attempts "
            "(email, fails, first_fail_at, locked_until, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (key, fails, first, locked_until, now),
        )
        self._db.commit()

    def reset_signin_failures(self, email: str) -> None:
        self._db.execute(
            "DELETE FROM prescribe_signin_attempts WHERE email = ?",
            ((email or "").strip().lower(),))
        self._db.commit()

    # -- sign-up rate limiting (per IP, DB-backed so tests stay isolated) --
    def signup_allowed(self, ip: str) -> bool:
        """Allow up to SIGNUP_MAX_PER_HOUR signups per IP per rolling hour."""
        now = time.time()
        row = self._db.execute(
            "SELECT * FROM prescribe_signup_attempts WHERE ip = ?", (ip,)
        ).fetchone()
        if row is None or now - row["window_start"] > 3600:
            self._db.execute(
                "INSERT OR REPLACE INTO prescribe_signup_attempts "
                "(ip, count, window_start) VALUES (?, 1, ?)",
                (ip, now),
            )
            self._db.commit()
            return True
        if row["count"] >= SIGNUP_MAX_PER_HOUR:
            return False
        self._db.execute(
            "UPDATE prescribe_signup_attempts SET count = count + 1 WHERE ip = ?",
            (ip,),
        )
        self._db.commit()
        return True
