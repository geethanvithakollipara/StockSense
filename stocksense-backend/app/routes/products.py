from flask import Blueprint, request, jsonify

from app.database import get_db, rows_to_list, dict_from_row
from app.utils.security import login_required
from app.utils.inventory import apply_stock_change

bp = Blueprint("products", __name__, url_prefix="/api/products")


def _serialize_product(db, product):
    product = dict(product)
    stock_rows = db.execute(
        """SELECT s.warehouse_id, w.name AS warehouse_name, s.quantity
           FROM stock s JOIN warehouses w ON w.id = s.warehouse_id
           WHERE s.product_id = ?""",
        (product["id"],),
    ).fetchall()
    product["stock_by_location"] = rows_to_list(stock_rows)
    product["total_stock"] = sum(r["quantity"] for r in stock_rows)
    product["low_stock"] = product["total_stock"] <= (product["reorder_min"] or 0)
    return product


@bp.get("")
@login_required
def list_products():
    db = get_db()
    category_id = request.args.get("category_id")
    warehouse_id = request.args.get("warehouse_id")
    search = request.args.get("search")  # matches name or SKU
    low_stock_only = request.args.get("low_stock") == "true"

    query = "SELECT DISTINCT p.* FROM products p"
    joins = []
    conditions = []
    params = []

    if warehouse_id:
        joins.append("JOIN stock s ON s.product_id = p.id")
        conditions.append("s.warehouse_id = ?")
        params.append(warehouse_id)
    if category_id:
        conditions.append("p.category_id = ?")
        params.append(category_id)
    if search:
        conditions.append("(p.name LIKE ? OR p.sku LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    if joins:
        query += " " + " ".join(joins)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY p.name"

    products = [_serialize_product(db, r) for r in db.execute(query, params).fetchall()]
    if low_stock_only:
        products = [p for p in products if p["low_stock"]]

    return jsonify({"products": products})


@bp.post("")
@login_required
def create_product():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    sku = (data.get("sku") or "").strip()
    category_id = data.get("category_id")
    uom = data.get("uom", "unit")
    reorder_min = data.get("reorder_min", 0)
    reorder_max = data.get("reorder_max")
    initial_stock = data.get("initial_stock")  # optional {warehouse_id, quantity}

    if not name or not sku:
        return jsonify({"error": "name and sku are required"}), 400

    db = get_db()
    if db.execute("SELECT id FROM products WHERE sku = ?", (sku,)).fetchone():
        return jsonify({"error": "A product with this SKU already exists"}), 409

    cur = db.execute(
        """INSERT INTO products (name, sku, category_id, uom, reorder_min, reorder_max)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, sku, category_id, uom, reorder_min, reorder_max),
    )
    product_id = cur.lastrowid

    if initial_stock and initial_stock.get("warehouse_id") and initial_stock.get("quantity"):
        apply_stock_change(
            db,
            product_id,
            initial_stock["warehouse_id"],
            float(initial_stock["quantity"]),
            document_id=None,
            doc_type="initial",
        )

    db.commit()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return jsonify(_serialize_product(db, product)), 201


@bp.get("/<int:product_id>")
@login_required
def get_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(_serialize_product(db, product))


@bp.put("/<int:product_id>")
@login_required
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    fields = {
        "name": data.get("name", product["name"]),
        "category_id": data.get("category_id", product["category_id"]),
        "uom": data.get("uom", product["uom"]),
        "reorder_min": data.get("reorder_min", product["reorder_min"]),
        "reorder_max": data.get("reorder_max", product["reorder_max"]),
    }
    db.execute(
        """UPDATE products SET name=?, category_id=?, uom=?, reorder_min=?, reorder_max=?
           WHERE id=?""",
        (*fields.values(), product_id),
    )
    db.commit()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return jsonify(_serialize_product(db, product))


@bp.delete("/<int:product_id>")
@login_required
def delete_product(product_id):
    db = get_db()
    has_stock = db.execute(
        "SELECT id FROM stock WHERE product_id = ? AND quantity != 0 LIMIT 1", (product_id,)
    ).fetchone()
    if has_stock:
        return jsonify({"error": "Cannot delete a product that still has stock on hand"}), 409
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return jsonify({"message": "Product deleted"})


@bp.get("/<int:product_id>/stock")
@login_required
def product_stock(product_id):
    db = get_db()
    rows = db.execute(
        """SELECT s.warehouse_id, w.name AS warehouse_name, s.quantity
           FROM stock s JOIN warehouses w ON w.id = s.warehouse_id
           WHERE s.product_id = ?""",
        (product_id,),
    ).fetchall()
    return jsonify({"product_id": product_id, "stock_by_location": rows_to_list(rows)})
