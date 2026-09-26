from app.database import rows_to_list


def serialize_document(db, doc):
    doc = dict(doc)
    lines = db.execute(
        """SELECT dl.*, p.name AS product_name, p.sku
           FROM document_lines dl JOIN products p ON p.id = dl.product_id
           WHERE dl.document_id = ?""",
        (doc["id"],),
    ).fetchall()
    doc["lines"] = rows_to_list(lines)
    return doc


def list_documents(db, doc_type, filters):
    """filters: dict with optional status, warehouse_id, category_id."""
    query = "SELECT DISTINCT d.* FROM documents d"
    joins = []
    conditions = ["d.doc_type = ?"]
    params = [doc_type]

    if filters.get("category_id"):
        joins.append("JOIN document_lines dl ON dl.document_id = d.id")
        joins.append("JOIN products p ON p.id = dl.product_id")
        conditions.append("p.category_id = ?")
        params.append(filters["category_id"])

    if filters.get("status"):
        conditions.append("d.status = ?")
        params.append(filters["status"])

    if filters.get("warehouse_id"):
        conditions.append("(d.source_warehouse_id = ? OR d.dest_warehouse_id = ?)")
        params.extend([filters["warehouse_id"], filters["warehouse_id"]])

    if joins:
        query += " " + " ".join(joins)
    query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY d.created_at DESC"

    docs = db.execute(query, params).fetchall()
    return [serialize_document(db, d) for d in docs]


def create_document_with_lines(db, doc_type, reference_no, created_by, lines,
                                source_warehouse_id=None, dest_warehouse_id=None,
                                supplier_id=None, customer_name=None, notes=None,
                                status="draft"):
    cur = db.execute(
        """INSERT INTO documents
           (doc_type, reference_no, status, source_warehouse_id, dest_warehouse_id,
            supplier_id, customer_name, notes, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (doc_type, reference_no, status, source_warehouse_id, dest_warehouse_id,
         supplier_id, customer_name, notes, created_by),
    )
    document_id = cur.lastrowid
    for line in lines:
        db.execute(
            """INSERT INTO document_lines (document_id, product_id, expected_qty, counted_qty)
               VALUES (?, ?, ?, ?)""",
            (document_id, line["product_id"], line.get("expected_qty", 0),
             line.get("counted_qty")),
        )
    return document_id
