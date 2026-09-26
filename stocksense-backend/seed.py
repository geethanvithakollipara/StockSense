"""Optional: populate a couple of warehouses/categories/suppliers for quick testing.
Run with: python seed.py
"""
from app import create_app
from app.database import get_db

app = create_app()

with app.app_context():
    db = get_db()
    for name, location in [("Main Warehouse", "Building A"), ("Production Floor", "Building B")]:
        db.execute(
            "INSERT OR IGNORE INTO warehouses (name, location) VALUES (?, ?)", (name, location)
        )
    for cat in ["Raw Materials", "Finished Goods", "Furniture"]:
        db.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    db.execute(
        "INSERT OR IGNORE INTO suppliers (name, contact) VALUES (?, ?)",
        ("Acme Steel Co.", "sales@acmesteel.example"),
    )
    db.commit()
    print("Seed data inserted.")
