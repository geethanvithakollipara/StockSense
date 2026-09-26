import hashlib
import hmac
import os
import random
import string
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, current_app, g

from app.database import get_db

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 hash with a random salt. No external deps required."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        iterations = int(iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(dk, expected)


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def generate_reference_no(prefix: str) -> str:
    """e.g. RCPT-20260926-4821"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{prefix}-{ts}-{suffix}"


def create_token(user_id: int, email: str) -> str:
    expires_minutes = current_app.config["JWT_EXPIRES_MINUTES"]
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token: str):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def login_required(fn):
    """Decorator: requires a valid `Authorization: Bearer <token>` header."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        db = get_db()
        user = db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?", (payload["sub"],)
        ).fetchone()
        if user is None:
            return jsonify({"error": "User no longer exists"}), 401

        g.current_user = dict(user)
        return fn(*args, **kwargs)

    return wrapper
