from flask import Blueprint, request, jsonify

from app.database import get_db
from app.utils.security import login_required
from app.utils.documents import list_documents

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/kpis")
@login_required
def kpis():
    db = get_db()

    total_products = db.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]

    low_stock_rows = db.execute(
        """SELECT p.id, p.reorder_min, COALESCE(SUM(s.quantity), 0) AS total_qty
           FROM products p LEFT JOIN stock s ON s.product_id = p.id
           GROUP BY p.id"""
    ).fetchall()
    low_stock = sum(1 for r in low_stock_rows if r["total_qty"] <= r["reorder_min"])
    out_of_stock = sum(1 for r in low_stock_rows if r["total_qty"] <= 0)

    def count_pending(doc_type):
        return db.execute(
            """SELECT COUNT(*) AS c FROM documents
               WHERE doc_type = ? AND status IN ('draft','waiting','ready')""",
            (doc_type,),
        ).fetchone()["c"]

    return jsonify(
        {
            "total_products_in_stock": total_products,
            "low_stock_items": low_stock,
            "out_of_stock_items": out_of_stock,
            "pending_receipts": count_pending("receipt"),
            "pending_deliveries": count_pending("delivery"),
            "internal_transfers_scheduled": count_pending("internal"),
        }
    )


@bp.get("/documents")
@login_required
def dashboard_documents():
    """Dynamic filters: by document type, status, warehouse, or product category."""
    db = get_db()
    doc_type = request.args.get("doc_type", "receipt")  # receipt|delivery|internal|adjustment
    if doc_type not in ("receipt", "delivery", "internal", "adjustment"):
        return jsonify({"error": "doc_type must be one of receipt, delivery, internal, adjustment"}), 400

    filters = {
        "status": request.args.get("status"),
        "warehouse_id": request.args.get("warehouse_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"documents": list_documents(db, doc_type, filters)})
