from flask import Blueprint, request, jsonify

from app.database import get_db, rows_to_list
from app.utils.security import login_required

bp = Blueprint("settings", __name__, url_prefix="/api")


# ---------------------------------------------------------------- Warehouses
@bp.get("/warehouses")
@login_required
def list_warehouses():
    db = get_db()
    rows = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
    return jsonify({"warehouses": rows_to_list(rows)})


@bp.post("/warehouses")
@login_required
def create_warehouse():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    location = data.get("location")
    if not name:
        return jsonify({"error": "name is required"}), 400

    db = get_db()
    if db.execute("SELECT id FROM warehouses WHERE name = ?", (name,)).fetchone():
        return jsonify({"error": "A warehouse with this name already exists"}), 409

    cur = db.execute(
        "INSERT INTO warehouses (name, location) VALUES (?, ?)", (name, location)
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name, "location": location}), 201


@bp.put("/warehouses/<int:warehouse_id>")
@login_required
def update_warehouse(warehouse_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    warehouse = db.execute("SELECT * FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone()
    if warehouse is None:
        return jsonify({"error": "Warehouse not found"}), 404

    name = data.get("name", warehouse["name"])
    location = data.get("location", warehouse["location"])
    db.execute(
        "UPDATE warehouses SET name = ?, location = ? WHERE id = ?",
        (name, location, warehouse_id),
    )
    db.commit()
    return jsonify({"id": warehouse_id, "name": name, "location": location})


@bp.delete("/warehouses/<int:warehouse_id>")
@login_required
def delete_warehouse(warehouse_id):
    db = get_db()
    in_use = db.execute(
        "SELECT id FROM stock WHERE warehouse_id = ? AND quantity != 0 LIMIT 1",
        (warehouse_id,),
    ).fetchone()
    if in_use:
        return jsonify({"error": "Cannot delete a warehouse that still holds stock"}), 409
    db.execute("DELETE FROM warehouses WHERE id = ?", (warehouse_id,))
    db.commit()
    return jsonify({"message": "Warehouse deleted"})


# ---------------------------------------------------------------- Categories
@bp.get("/categories")
@login_required
def list_categories():
    db = get_db()
    rows = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return jsonify({"categories": rows_to_list(rows)})


@bp.post("/categories")
@login_required
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    db = get_db()
    if db.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone():
        return jsonify({"error": "Category already exists"}), 409
    cur = db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name}), 201


# ----------------------------------------------------------------- Suppliers
@bp.get("/suppliers")
@login_required
def list_suppliers():
    db = get_db()
    rows = db.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    return jsonify({"suppliers": rows_to_list(rows)})


@bp.post("/suppliers")
@login_required
def create_supplier():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    contact = data.get("contact")
    if not name:
        return jsonify({"error": "name is required"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO suppliers (name, contact) VALUES (?, ?)", (name, contact)
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name, "contact": contact}), 201
