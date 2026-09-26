from flask import Blueprint, request, jsonify, g

from app.database import get_db
from app.utils.security import login_required, generate_reference_no
from app.utils.inventory import apply_stock_change, get_stock_qty
from app.utils.documents import serialize_document, list_documents, create_document_with_lines

bp = Blueprint("transfers", __name__, url_prefix="/api/transfers")


@bp.get("")
@login_required
def list_transfers():
    db = get_db()
    filters = {
        "status": request.args.get("status"),
        "warehouse_id": request.args.get("warehouse_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"transfers": list_documents(db, "internal", filters)})


@bp.post("")
@login_required
def create_transfer():
    """Move stock inside the company, e.g. Main Warehouse -> Production Floor,
    or Rack A -> Rack B (model racks/sub-locations as warehouses too)."""
    data = request.get_json(silent=True) or {}
    source_warehouse_id = data.get("source_warehouse_id")
    dest_warehouse_id = data.get("dest_warehouse_id")
    lines = data.get("lines") or []
    notes = data.get("notes")

    if not source_warehouse_id or not dest_warehouse_id or not lines:
        return jsonify(
            {"error": "source_warehouse_id, dest_warehouse_id and at least one line are required"}
        ), 400
    if source_warehouse_id == dest_warehouse_id:
        return jsonify({"error": "source and destination warehouses must differ"}), 400
    for line in lines:
        if not line.get("product_id") or line.get("expected_qty", 0) <= 0:
            return jsonify({"error": "Each line needs product_id and a positive expected_qty"}), 400

    db = get_db()
    reference_no = generate_reference_no("INT")
    document_id = create_document_with_lines(
        db, "internal", reference_no, g.current_user["id"], lines,
        source_warehouse_id=source_warehouse_id, dest_warehouse_id=dest_warehouse_id,
        notes=notes, status="waiting",
    )
    db.commit()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    return jsonify(serialize_document(db, doc)), 201


@bp.get("/<int:doc_id>")
@login_required
def get_transfer(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'internal'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Internal transfer not found"}), 404
    return jsonify(serialize_document(db, doc))


@bp.post("/<int:doc_id>/validate")
@login_required
def validate_transfer(doc_id):
    """Validate -> stock unchanged in total, but location updated. Each
    movement is logged twice in the ledger: a decrease at source and an
    increase at destination, so Move History shows both sides."""
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'internal'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Internal transfer not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Transfer already validated"}), 409
    if doc["status"] == "cancelled":
        return jsonify({"error": "Cannot validate a cancelled transfer"}), 409

    lines = db.execute(
        "SELECT * FROM document_lines WHERE document_id = ?", (doc_id,)
    ).fetchall()

    for line in lines:
        available = get_stock_qty(db, line["product_id"], doc["source_warehouse_id"])
        if available < line["expected_qty"]:
            return (
                jsonify(
                    {
                        "error": (
                            f"Insufficient stock for product_id={line['product_id']} at source: "
                            f"available {available}, requested {line['expected_qty']}"
                        )
                    }
                ),
                409,
            )

    for line in lines:
        qty = line["expected_qty"]
        apply_stock_change(db, line["product_id"], doc["source_warehouse_id"], -qty, doc_id, "internal")
        apply_stock_change(db, line["product_id"], doc["dest_warehouse_id"], qty, doc_id, "internal")
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
def cancel_transfer(doc_id):
    db = get_db()
    doc = db.execute(
        "SELECT * FROM documents WHERE id = ? AND doc_type = 'internal'", (doc_id,)
    ).fetchone()
    if doc is None:
        return jsonify({"error": "Internal transfer not found"}), 404
    if doc["status"] == "done":
        return jsonify({"error": "Cannot cancel a validated transfer"}), 409
    db.execute("UPDATE documents SET status = 'cancelled' WHERE id = ?", (doc_id,))
    db.commit()
    return jsonify({"message": "Internal transfer cancelled"})
