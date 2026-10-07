"""Password hashing and signed-cookie sessions for Campus Customs."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

try:
    from . import db
except ImportError:  # Running directly from the backend directory.
    import db

# Passwords use a self-describing PBKDF2-HMAC-SHA256 format:
#   pbkdf2_sha256$<iterations>$<salt>$<hex>
# The seeded test account is migrated to this format so the assignment
# login fixture works through the same verifier as newly created accounts.
ITERATIONS = 240_000
SESSION_TTL = 60 * 60 * 24 * 14  # 14 days
# Set SESSION_SECRET in deployment. The per-process fallback keeps local development
# usable while avoiding a predictable signing key in source control.
_SECRET = (os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)).encode()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False  # legacy/unknown format: not verifiable
    _, iterations, salt, digest = parts
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(candidate, digest)


def issue_token(user_id: int) -> str:
    """Create a signed, expiring session token: <user_id>.<expiry>.<signature>."""
    expiry = int(time.time()) + SESSION_TTL
    payload = f"{user_id}.{expiry}"
    signature = hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def read_token(token: str | None) -> int | None:
    """Return the user id for a valid, unexpired token, else None."""
    if not token:
        return None
    try:
        user_id, expiry, signature = token.rsplit(".", 2)
    except ValueError:
        return None
    expected = hmac.new(_SECRET, f"{user_id}.{expiry}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    if int(expiry) < time.time():
        return None
    return int(user_id)


def register(first_name: str, last_name: str, email: str, password: str) -> dict:
    if db.get_user_by_email(email):
        raise ValueError("An account with that email already exists.")
    user_id = db.create_user(first_name, last_name, email, hash_password(password))
    return db.get_user(user_id)


def authenticate(email: str, password: str) -> dict | None:
    user = db.get_user_by_email(email)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None
