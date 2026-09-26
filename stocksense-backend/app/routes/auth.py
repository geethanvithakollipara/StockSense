from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, current_app, g

from app.database import get_db
from app.utils.security import (
    hash_password,
    verify_password,
    generate_otp,
    create_token,
    login_required,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "inventory_manager")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if role not in ("inventory_manager", "warehouse_staff"):
        return jsonify({"error": "role must be inventory_manager or warehouse_staff"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "An account with this email already exists"}), 409

    cur = db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, email, hash_password(password), role),
    )
    db.commit()
    user_id = cur.lastrowid
    token = create_token(user_id, email)
    return (
        jsonify(
            {
                "token": token,
                "user": {"id": user_id, "name": name, "email": email, "role": role},
            }
        ),
        201,
    )


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user["id"], user["email"])
    return jsonify(
        {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
            },
            "redirect": "/dashboard",
        }
    )


@bp.post("/forgot-password")
def forgot_password():
    """Generate an OTP for password reset. In production this would be
    sent via SMS/email; here it is returned in the response for the
    frontend to display/consume during development."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        # Do not reveal whether the email exists.
        return jsonify({"message": "If that account exists, an OTP has been sent"}), 200

    otp = generate_otp()
    expires_minutes = current_app.config["OTP_EXPIRES_MINUTES"]
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)).isoformat()

    db.execute(
        "INSERT INTO otp_resets (user_id, otp_code, expires_at) VALUES (?, ?, ?)",
        (user["id"], otp, expires_at),
    )
    db.commit()

    response = {"message": "If that account exists, an OTP has been sent"}
    if current_app.config.get("DEBUG"):
        response["debug_otp"] = otp  # only exposed in debug mode
    return jsonify(response), 200


@bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()
    new_password = data.get("new_password") or ""

    if not email or not otp or not new_password:
        return jsonify({"error": "email, otp and new_password are required"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "new_password must be at least 6 characters"}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        return jsonify({"error": "Invalid OTP"}), 400

    otp_row = db.execute(
        """SELECT * FROM otp_resets
           WHERE user_id = ? AND otp_code = ? AND used = 0
           ORDER BY id DESC LIMIT 1""",
        (user["id"], otp),
    ).fetchone()
    if otp_row is None:
        return jsonify({"error": "Invalid OTP"}), 400

    expires_at = datetime.fromisoformat(otp_row["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return jsonify({"error": "OTP has expired"}), 400

    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user["id"]),
    )
    db.execute("UPDATE otp_resets SET used = 1 WHERE id = ?", (otp_row["id"],))
    db.commit()
    return jsonify({"message": "Password reset successfully"}), 200


@bp.get("/me")
@login_required
def me():
    return jsonify({"user": g.current_user})
