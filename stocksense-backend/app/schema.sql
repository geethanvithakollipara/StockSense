-- StockSense IMS schema (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'inventory_manager', -- inventory_manager | warehouse_staff
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS otp_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    otp_code TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    location TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    category_id INTEGER REFERENCES categories(id),
    uom TEXT NOT NULL DEFAULT 'unit',      -- unit, kg, box, etc.
    reorder_min INTEGER NOT NULL DEFAULT 0, -- triggers low-stock alert
    reorder_max INTEGER,                    -- suggested restock ceiling
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Stock on hand per product per warehouse
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity REAL NOT NULL DEFAULT 0,
    UNIQUE(product_id, warehouse_id)
);

-- One row per operation: receipt / delivery / internal transfer / adjustment
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL CHECK (doc_type IN ('receipt','delivery','internal','adjustment')),
    reference_no TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','waiting','ready','done','cancelled')),
    source_warehouse_id INTEGER REFERENCES warehouses(id),
    dest_warehouse_id INTEGER REFERENCES warehouses(id),   -- used for internal transfers
    supplier_id INTEGER REFERENCES suppliers(id),          -- used for receipts
    customer_name TEXT,                                    -- used for deliveries
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    validated_at TEXT
);

CREATE TABLE IF NOT EXISTS document_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    expected_qty REAL NOT NULL DEFAULT 0,   -- planned quantity
    counted_qty REAL,                        -- used for adjustments (physical count)
    done_qty REAL                            -- actual qty applied on validate
);

-- Immutable ledger of every stock movement, for Move History
CREATE TABLE IF NOT EXISTS stock_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    change_qty REAL NOT NULL,       -- + increase, - decrease
    balance_after REAL NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    doc_type TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_stock_product ON stock(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_warehouse ON stock(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_documents_type_status ON documents(doc_type, status);
CREATE INDEX IF NOT EXISTS idx_ledger_product ON stock_ledger(product_id);
CREATE INDEX IF NOT EXISTS idx_ledger_warehouse ON stock_ledger(warehouse_id);
