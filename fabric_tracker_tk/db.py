import sqlite3

DB_NAME = "../fabric_tracker.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Purchase Records
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        batch_id TEXT,
        supplier TEXT,
        yarn_type TEXT,
        qty_kg REAL,
        qty_rolls INTEGER,
        delivered_to TEXT
    )
    """)

    # Yarn Stock at Suppliers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS yarn_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier TEXT,
        batch_id TEXT,
        yarn_type TEXT,
        qty_kg REAL,
        qty_rolls INTEGER
    )
    """)

    # Masters (dropdown values)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS yarn_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()
