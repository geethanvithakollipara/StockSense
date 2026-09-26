from flask import Blueprint, request, jsonify, g

from app.database import get_db
from app.utils.security import login_required, hash_password, verify_password

bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@bp.get("")
@login_required
def get_profile():
    return jsonify({"user": g.current_user})


@bp.put("")
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    db = get_db()
    user_id = g.current_user["id"]
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    name = data.get("name", user["name"])
    db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    db.commit()
    return jsonify({"user": {"id": user_id, "name": name, "email": user["email"], "role": user["role"]}})


@bp.post("/change-password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_password or not new_password:
        return jsonify({"error": "current_password and new_password are required"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "new_password must be at least 6 characters"}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (g.current_user["id"],)).fetchone()
    if not verify_password(current_password, user["password_hash"]):
        return jsonify({"error": "Current password is incorrect"}), 401

    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user["id"]),
    )
    db.commit()
    return jsonify({"message": "Password updated successfully"})
