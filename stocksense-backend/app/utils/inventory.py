"""
Core stock-movement logic shared by receipts, delivery orders, internal
transfers and adjustments. Keeping it in one place guarantees every
operation updates `stock` and appends to `stock_ledger` consistently.
"""


def get_or_create_stock_row(db, product_id, warehouse_id):
    row = db.execute(
        "SELECT * FROM stock WHERE product_id = ? AND warehouse_id = ?",
        (product_id, warehouse_id),
    ).fetchone()
    if row is None:
        db.execute(
            "INSERT INTO stock (product_id, warehouse_id, quantity) VALUES (?, ?, 0)",
            (product_id, warehouse_id),
        )
        row = db.execute(
            "SELECT * FROM stock WHERE product_id = ? AND warehouse_id = ?",
            (product_id, warehouse_id),
        ).fetchone()
    return row


def apply_stock_change(db, product_id, warehouse_id, change_qty, document_id, doc_type):
    """
    Adjust on-hand quantity for (product, warehouse) by `change_qty`
    (positive to add, negative to remove) and log it to stock_ledger.
    Returns the new balance.
    """
    row = get_or_create_stock_row(db, product_id, warehouse_id)
    new_balance = row["quantity"] + change_qty
    db.execute(
        "UPDATE stock SET quantity = ? WHERE id = ?",
        (new_balance, row["id"]),
    )
    db.execute(
        """INSERT INTO stock_ledger
           (product_id, warehouse_id, change_qty, balance_after, document_id, doc_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (product_id, warehouse_id, change_qty, new_balance, document_id, doc_type),
    )
    return new_balance


def get_stock_qty(db, product_id, warehouse_id):
    row = db.execute(
        "SELECT quantity FROM stock WHERE product_id = ? AND warehouse_id = ?",
        (product_id, warehouse_id),
    ).fetchone()
    return row["quantity"] if row else 0
