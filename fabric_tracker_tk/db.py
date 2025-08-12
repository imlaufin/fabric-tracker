# db.py
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "fabric.db"
BACKUP_DIR = "backups"

def backup_db():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"fabric_backup_{ts}.db")
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, dest)
    return dest

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize DB and perform migrations. Backups current DB before changes.
    """
    # ensure db file exists
    created = False
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "w").close()
        created = True

    # backup first
    backup = backup_db()
    print(f"[DB] Backup created at {backup}")

    conn = get_connection()
    cur = conn.cursor()

    # --- core existing tables: purchases, suppliers, yarn_types ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT DEFAULT 'yarn_supplier',  -- yarn_supplier / knitting_unit / dyeing_unit
        color_code TEXT DEFAULT ''
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS yarn_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        batch_id TEXT,
        lot_no TEXT,
        supplier TEXT,
        yarn_type TEXT,
        qty_kg REAL,
        qty_rolls INTEGER,
        delivered_to TEXT,
        notes TEXT
    )
    """)

    # --- new tables for batches, lots, transactions linking to fabricators ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_ref TEXT,                 -- user visible batch id (e.g., "200")
        fabricator_id INTEGER,          -- masters id
        product_name TEXT,
        expected_lots INTEGER DEFAULT 0,
        composition TEXT,               -- free-text composition
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(fabricator_id) REFERENCES suppliers(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        lot_no TEXT,            -- e.g., "200/1"
        lot_index INTEGER,      -- 1,2,3...
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(batch_id) REFERENCES batches(id)
    )
    """)

    # table to record dyeing outputs / returns (so we can link original knitter records)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dyeing_outputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        dyeing_unit_id INTEGER,    -- supplier.id for dyeing unit
        returned_date TEXT,
        returned_qty_kg REAL,
        returned_qty_rolls INTEGER,
        notes TEXT,
        FOREIGN KEY(lot_id) REFERENCES lots(id),
        FOREIGN KEY(dyeing_unit_id) REFERENCES suppliers(id)
    )
    """)

    # index hints (speed up queries)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_delivered_to ON purchases(delivered_to)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_batch ON purchases(batch_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_batches_ref ON batches(batch_ref)")

    conn.commit()
    conn.close()
    if created:
        print("[DB] New DB created and initialized.")
    else:
        print("[DB] DB init/migrations complete.")

# Helper convenience queries used by UI
def get_fabricators(fab_type):
    """Return list of suppliers of given type: 'knitting_unit' or 'dyeing_unit'"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers WHERE type=? ORDER BY name", (fab_type,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_master(name, mtype="yarn_supplier", color_code=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO suppliers (name, type, color_code) VALUES (?, ?, ?)", (name, mtype, color_code))
    conn.commit()
    conn.close()

def update_master_color_and_type(name, mtype, color_hex):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE suppliers SET type=?, color_code=? WHERE name=?", (mtype, color_hex, name))
    conn.commit()
    conn.close()

def get_batches_for_fabricator(fabricator_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM batches WHERE fabricator_id=? ORDER BY created_at DESC", (fabricator_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def create_batch(batch_ref, fabricator_id, product_name, expected_lots, composition=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO batches (batch_ref, fabricator_id, product_name, expected_lots, composition)
        VALUES (?, ?, ?, ?, ?)
    """, (batch_ref, fabricator_id, product_name, expected_lots, composition))
    bid = cur.lastrowid
    conn.commit()
    conn.close()
    return bid

def create_lot(batch_id, lot_index):
    conn = get_connection()
    cur = conn.cursor()
    # get batch_ref for forming lot_no
    cur.execute("SELECT batch_ref FROM batches WHERE id=?", (batch_id,))
    row = cur.fetchone()
    batch_ref = row["batch_ref"] if row else str(batch_id)
    lot_no = f"{batch_ref}/{lot_index}"
    cur.execute("INSERT INTO lots (batch_id, lot_no, lot_index) VALUES (?, ?, ?)", (batch_id, lot_no, lot_index))
    lid = cur.lastrowid
    conn.commit()
    conn.close()
    return lid

def record_purchase(date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases (date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to, notes))
    conn.commit()
    conn.close()

def record_dyeing_output(lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dyeing_outputs (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes))
    conn.commit()
    conn.close()
