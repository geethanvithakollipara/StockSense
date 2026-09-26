from flask import Blueprint, request, jsonify, g

from app.database import get_db
from app.utils.security import login_required, generate_reference_no
from app.utils.inventory import apply_stock_change
from app.utils.documents import serialize_document, list_documents, create_document_with_lines

bp = Blueprint("receipts", __name__, url_prefix="/api/receipts")


@bp.get("")
@login_required
def list_receipts():
    db = get_db()
    filters = {
        "status": request.args.get("status"),
        "warehouse_id": request.args.get("warehouse_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"receipts": list_documents(db, "receipt", filters)})


@bp.post("")
@login_required
def create_receipt():
    """Step 1-3: create a receipt in draft status with supplier & products."""
    data = request.get_json(silent=True) or {}
    warehouse_id = data.get("warehouse_id")
    supplier_id = data.get("supplier_id")
    lines = data.get("lines") or []  # [{product_id, expected_qty}]
    notes = data.get("notes")

    if not warehouse_id or not lines:
        return jsonify({"error": "warehouse_id and at least one line are required"}), 400
    for line in lines:
        if not line.get("product_id") or line.get("expected_qty", 0) <= 0:
            return jsonify({"error": "Each line needs product_id and a positive expected_qty"}), 400

    db = get_db()
    reference_no = generate_reference_no("RCPT")
    document_id = create_document_with_lines(
        db, "receipt", reference_no, g.current_user["id"], lines,
        source_warehouse_id=warehouse_id, supplier_id=supplier_id, notes=notes,
        status="waiting",
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    return jsonify(serialize_document(db, doc)), 201


@bp.get("/<int:doc_id>")
@login_required
def get_receipt(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'receipt'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Receipt not found"}), 404
    return jsonify(serialize_document(db, doc))


@bp.put("/<int:doc_id>")
@login_required
def update_receipt(doc_id):
    """Update quantities received while still in draft/waiting."""
    data = request.get_json(silent=True) or {}
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'receipt'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Receipt not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Cannot edit a validated receipt"}), 409

    for line in data.get("lines", []):
        db.execute(
            "UPDATE document_lines SET expected_qty = ? WHERE id = ? AND document_id = ?",
            (line["expected_qty"], line["line_id"], doc_id),
        )
    if "notes" in data:
        db.execute("UPDATE documents SET notes = ? WHERE id = ?", (data["notes"], doc_id))
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/validate")
@login_required
def validate_receipt(doc_id):
    """Step 4: validate -> stock increases automatically for every line."""
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'receipt'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Receipt not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Receipt already validated"}), 409
    if doc["status"] == "cancelled":
        return jsonify({"error": "Cannot validate a cancelled receipt"}), 409

    lines = db.execute(
        "SELECT * FROM document_lines WHERE document_id = ?", (doc_id,)
    ).fetchall()
    for line in lines:
        qty = line["expected_qty"]
        apply_stock_change(db, line["product_id"], doc["source_warehouse_id"], qty, doc_id, "receipt")
        db.execute(
            "UPDATE document_lines SET done_qty = ? WHERE id = ?", (qty, line["id"])
        )

    db.execute(
        "UPDATE documents SET status = 'done', validated_at = datetime('now') WHERE id = ?",
        (doc_id,),
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/cancel")
@login_required
def cancel_receipt(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'receipt'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Receipt not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Cannot cancel a validated receipt"}), 409
    db.execute("UPDATE documents SET status = 'cancelled' WHERE id = ?", (doc_id,))
    db.commit()
    return jsonify({"message": "Receipt cancelled"})
