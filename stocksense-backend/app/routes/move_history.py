from flask import Blueprint, request, jsonify

from app.database import get_db, rows_to_list
from app.utils.security import login_required

bp = Blueprint("move_history", __name__, url_prefix="/api/move-history")


@bp.get("")
@login_required
def move_history():
    """The Stock Ledger: every increase/decrease ever applied, with filters."""
    db = get_db()
    product_id = request.args.get("product_id")
    warehouse_id = request.args.get("warehouse_id")
    doc_type = request.args.get("doc_type")  # receipt | delivery | internal | adjustment
    date_from = request.args.get("date_from")  # YYYY-MM-DD
    date_to = request.args.get("date_to")

    query = """
        SELECT l.*, p.name AS product_name, p.sku, w.name AS warehouse_name,
               d.reference_no, d.doc_type AS document_type
        FROM stock_ledger l
        JOIN products p ON p.id = l.product_id
        JOIN warehouses w ON w.id = l.warehouse_id
        LEFT JOIN documents d ON d.id = l.document_id
    """
    conditions = []
    params = []

    if product_id:
        conditions.append("l.product_id = ?")
        params.append(product_id)
    if warehouse_id:
        conditions.append("l.warehouse_id = ?")
        params.append(warehouse_id)
    if doc_type:
        conditions.append("l.doc_type = ?")
        params.append(doc_type)
    if date_from:
        conditions.append("date(l.created_at) >= date(?)")
        params.append(date_from)
    if date_to:
        conditions.append("date(l.created_at) <= date(?)")
        params.append(date_to)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY l.created_at DESC, l.id DESC"

    rows = db.execute(query, params).fetchall()
    return jsonify({"ledger": rows_to_list(rows)})
