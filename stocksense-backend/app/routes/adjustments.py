from flask import Blueprint, request, jsonify, g

from app.database import get_db
from app.utils.security import login_required, generate_reference_no
from app.utils.inventory import apply_stock_change, get_stock_qty
from app.utils.documents import serialize_document, list_documents, create_document_with_lines

bp = Blueprint("adjustments", __name__, url_prefix="/api/adjustments")


@bp.get("")
@login_required
def list_adjustments():
    db = get_db()
    filters = {
        "status": request.args.get("status"),
        "warehouse_id": request.args.get("warehouse_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"adjustments": list_documents(db, "adjustment", filters)})


@bp.post("")
@login_required
def create_adjustment():
    """Fix mismatches between recorded stock and a physical count.
    Body: { warehouse_id, lines: [{product_id, counted_qty}], notes }
    """
    data = request.get_json(silent=True) or {}
    warehouse_id = data.get("warehouse_id")
    lines = data.get("lines") or []
    notes = data.get("notes")

    if not warehouse_id or not lines:
        return jsonify({"error": "warehouse_id and at least one line are required"}), 400
    for line in lines:
        if not line.get("product_id") or line.get("counted_qty") is None:
            return jsonify({"error": "Each line needs product_id and counted_qty"}), 400

    db = get_db()
    # expected_qty stores the system's recorded quantity at the time of the count
    enriched_lines = []
    for line in lines:
        recorded = get_stock_qty(db, line["product_id"], warehouse_id)
        enriched_lines.append(
            {
                "product_id": line["product_id"],
                "expected_qty": recorded,
                "counted_qty": line["counted_qty"],
            }
        )

    reference_no = generate_reference_no("ADJ")
    document_id = create_document_with_lines(
        db, "adjustment", reference_no, g.current_user["id"], enriched_lines,
        source_warehouse_id=warehouse_id, notes=notes, status="waiting",
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    return jsonify(serialize_document(db, doc)), 201


@bp.get("/<int:doc_id>")
@login_required
def get_adjustment(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'adjustment'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Adjustment not found"}), 404
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/validate")
@login_required
def validate_adjustment(doc_id):
    """System auto-updates stock to the counted quantity and logs the delta."""
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'adjustment'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Adjustment not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Adjustment already validated"}), 409
    if doc["status"] == "cancelled":
        return jsonify({"error": "Cannot validate a cancelled adjustment"}), 409

    lines = db.execute(
        "SELECT * FROM document_lines WHERE document_id = ?", (doc_id,)
    ).fetchall()

    for line in lines:
        current = get_stock_qty(db, line["product_id"], doc["source_warehouse_id"])
        delta = line["counted_qty"] - current
        if delta != 0:
            apply_stock_change(
                db, line["product_id"], doc["source_warehouse_id"], delta, doc_id, "adjustment"
            )
        db.execute("UPDATE document_lines SET done_qty = ? WHERE id = ?", (delta, line["id"]))

    db.execute(
        "UPDATE documents SET status = 'done', validated_at = datetime('now') WHERE id = ?",
        (doc_id,),
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/cancel")
@login_required
def cancel_adjustment(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'adjustment'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Adjustment not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Cannot cancel a validated adjustment"}), 409
    db.execute("UPDATE documents SET status = 'cancelled' WHERE id = ?", (doc_id,))
    db.commit()
    return jsonify({"message": "Adjustment cancelled"})
