from flask import Blueprint, request, jsonify, g

from app.database import get_db
from app.utils.security import login_required, generate_reference_no
from app.utils.inventory import apply_stock_change, get_stock_qty
from app.utils.documents import serialize_document, list_documents, create_document_with_lines

bp = Blueprint("deliveries", __name__, url_prefix="/api/deliveries")


@bp.get("")
@login_required
def list_deliveries():
    db = get_db()
    filters = {
        "status": request.args.get("status"),
        "warehouse_id": request.args.get("warehouse_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"deliveries": list_documents(db, "delivery", filters)})


@bp.post("")
@login_required
def create_delivery():
    data = request.get_json(silent=True) or {}
    warehouse_id = data.get("warehouse_id")
    customer_name = data.get("customer_name")
    lines = data.get("lines") or []  # [{product_id, expected_qty}]
    notes = data.get("notes")

    if not warehouse_id or not lines:
        return jsonify({"error": "warehouse_id and at least one line are required"}), 400
    for line in lines:
        if not line.get("product_id") or line.get("expected_qty", 0) <= 0:
            return jsonify({"error": "Each line needs product_id and a positive expected_qty"}), 400

    db = get_db()
    reference_no = generate_reference_no("DO")
    document_id = create_document_with_lines(
        db, "delivery", reference_no, g.current_user["id"], lines,
        source_warehouse_id=warehouse_id, customer_name=customer_name, notes=notes,
        status="waiting",
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    return jsonify(serialize_document(db, doc)), 201


@bp.get("/<int:doc_id>")
@login_required
def get_delivery(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'delivery'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Delivery order not found"}), 404
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/pick")
@login_required
def pick_delivery(doc_id):
    """Mark items as picked -> moves status waiting -> ready."""
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'delivery'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Delivery order not found"}), 404
    if doc["status"] not in ("waiting",):
        return jsonify({"error": f"Cannot pick a delivery in status '{doc['status']}'"}), 409

    db.execute("UPDATE documents SET status = 'ready' WHERE id = ?", (doc_id,))
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/validate")
@login_required
def validate_delivery(doc_id):
    """Pack + validate -> stock decreases automatically for every line."""
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'delivery'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Delivery order not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Delivery already validated"}), 409
    if doc["status"] == "cancelled":
        return jsonify({"error": "Cannot validate a cancelled delivery"}), 409

    lines = db.execute(
        "SELECT * FROM document_lines WHERE document_id = ?", (doc_id,)
    ).fetchall()

    # Validate stock availability before committing any change
    for line in lines:
        available = get_stock_qty(db, line["product_id"], doc["source_warehouse_id"])
        if available < line["expected_qty"]:
            return (
                jsonify(
                    {
                        "error": (
                            f"Insufficient stock for product_id={line['product_id']}: "
                            f"available {available}, requested {line['expected_qty']}"
                        )
                    }
                ),
                409,
            )

    for line in lines:
        qty = line["expected_qty"]
        apply_stock_change(db, line["product_id"], doc["source_warehouse_id"], -qty, doc_id, "delivery")
        db.execute("UPDATE document_lines SET done_qty = ? WHERE id = ?", (qty, line["id"]))

    db.execute(
        "UPDATE documents SET status = 'done', validated_at = datetime('now') WHERE id = ?",
        (doc_id,),
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/cancel")
@login_required
def cancel_delivery(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'delivery'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Delivery order not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Cannot cancel a validated delivery"}), 409
    db.execute("UPDATE documents SET status = 'cancelled' WHERE id = ?", (doc_id,))
    db.commit()
    return jsonify({"message": "Delivery order cancelled"})
