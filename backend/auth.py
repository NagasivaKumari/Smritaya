"""Smritaya auth — real accounts, stdlib only.

Users + sessions + password resets in one SQLite file (auth.db).
No external deps: scrypt for password hashing, secrets for tokens,
hmac.compare_digest for constant-time checks.

ponytail: this is stored identity, not auth-service grade. There is no
email delivery, so reset links are returned in-band for the UI to show.
Upgrade path: move to a real auth provider / queue reset emails via SMTP
and stop returning reset_token in API responses.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time

DB = os.path.join(os.path.dirname(__file__), "auth.db")

SESSION_TTL = 30 * 24 * 3600        # 30 days
RESET_TTL = 30 * 60                  # 30 minutes
MIN_PASSWORD = 8

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY,
                email      TEXT NOT NULL UNIQUE,
                pw_hash    TEXT NOT NULL,
                salt       TEXT NOT NULL,
                uid        TEXT NOT NULL UNIQUE,
                omi_uid    TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reset_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                used       INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        cols = {r["name"] for r in c.execute("PRAGMA table_info(users)")}
        if "omi_uid" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN omi_uid TEXT")


_init()


# ---------------------------------------------------------------- hashing

def _hash_password(password: str, salt: str) -> str:
    return hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    ).hex()


def _check_password(password: str, salt: str, expected: str) -> bool:
    return hmac.compare_digest(_hash_password(password, salt), expected)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _sanitize_email(email: str) -> str:
    return (email or "").strip().lower()


def _validate(email: str, password: str) -> str | None:
    email = _sanitize_email(email)
    if not EMAIL_RE.match(email):
        return "Enter a valid email address."
    if not password or len(password) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters."
    return None


class AuthError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code


# ---------------------------------------------------------------- users

def signup(email: str, password: str) -> dict:
    email = _sanitize_email(email)
    err = _validate(email, password)
    if err:
        raise AuthError(err)
    row = _find_user(email)
    if row:
        raise AuthError("An account with that email already exists.")
    salt = secrets.token_hex(16)
    uid = "user-" + secrets.token_hex(8)
    with _conn() as c:
        c.execute(
            "INSERT INTO users (email, pw_hash, salt, uid, created_at) VALUES (?,?,?,?,?)",
            (email, _hash_password(password, salt), salt, uid, time.time()),
        )
    return _find_user(email)


def login(email: str, password: str) -> dict:
    email = _sanitize_email(email)
    err = _validate(email, password)
    if err:
        raise AuthError(err)
    row = _find_user(email)
    if not row or not _check_password(password, row["salt"], row["pw_hash"]):
        raise AuthError("Wrong email or password.", code=401)
    return row


def _find_user(email: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def user_by_omi_uid(omi_uid: str) -> dict | None:
    """Reverse lookup: Omi appends its own uid to webhooks; map it back to the
    account that claimed it so the deed lands in that account's ledger."""
    if not omi_uid:
        return None
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE omi_uid = ?", (omi_uid,)).fetchone()
    return dict(row) if row else None


def set_omi_uid(user_id: int, omi_uid: str) -> None:
    """Link (or clear, with an empty value) the account's Omi uid for notifications."""
    with _conn() as c:
        c.execute(
            "UPDATE users SET omi_uid = ? WHERE id = ?",
            ((omi_uid or "").strip() or None, user_id),
        )


# -------------------------------------------------------------- sessions

def create_session(user: dict) -> str:
    token = secrets.token_urlsafe(48)
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?,?,?,?)",
            (_hash_token(token), user["id"], now, now + SESSION_TTL),
        )
    return token


def user_for_token(token: str) -> dict | None:
    if not token:
        return None
    with _conn() as c:
        row = c.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > ?""",
            (_hash_token(token), time.time()),
        ).fetchone()
    return dict(row) if row else None


def logout(token: str) -> None:
    if not token:
        return
    with _conn() as c:
        c.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


# ---------------------------------------------------------------- resets

def request_reset(email: str) -> str | None:
    """Create a single-use reset token. Returns the raw token (shown in-app —
    no email delivery in this build) or None when the email is unknown."""
    row = _find_user(_sanitize_email(email))
    if not row:
        return None
    token = secrets.token_urlsafe(32)
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO reset_tokens (token_hash, user_id, created_at, expires_at, used) VALUES (?,?,?,?,0)",
            (_hash_token(token), row["id"], now, now + RESET_TTL),
        )
    return token


def reset_password(token: str, password: str) -> None:
    if not token or not password or len(password) < MIN_PASSWORD:
        raise AuthError(f"Password must be at least {MIN_PASSWORD} characters.")
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM reset_tokens WHERE token_hash = ?",
            (_hash_token(token),),
        ).fetchone()
        if not row:
            raise AuthError("This reset link is invalid.", code=401)
        if row["used"] or row["expires_at"] < time.time():
            raise AuthError("This reset link has expired or was already used.", code=401)
        salt = secrets.token_hex(16)
        c.execute(
            "UPDATE users SET pw_hash = ?, salt = ? WHERE id = ?",
            (_hash_password(password, salt), salt, row["user_id"]),
        )
        c.execute("UPDATE reset_tokens SET used = 1 WHERE token_hash = ?", (_hash_token(token),))
        c.execute("DELETE FROM sessions WHERE user_id = ?", (row["user_id"],))


def public_user(user: dict) -> dict:
    return {"email": user["email"], "uid": user["uid"], "omi_uid": user.get("omi_uid")}