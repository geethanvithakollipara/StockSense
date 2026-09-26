import os
import sqlite3
from flask import g, current_app

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db():
    """Return a request-scoped SQLite connection with foreign keys enabled."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create tables if they do not exist yet. Safe to call on every boot."""
    db_path = app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def dict_from_row(row):
    return dict(row) if row is not None else None


def rows_to_list(rows):
    return [dict(r) for r in rows]
