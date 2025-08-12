# db.py
"""
Database utilities, migrations, and helpers.

- Keeps dates in DB as ISO YYYY-MM-DD (for correct sorting & queries).
- Provides UI <-> DB date conversion helpers for DD/MM/YYYY display/entry.
- Creates/updates required tables: suppliers, yarn_types, purchases, batches, lots, dyeing_outputs.
- Backup before migrations.
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "fabric.db"
BACKUP_DIR = "backups"

DB_FILENAME = "db.sqlite"

def get_db_path():
    """Return the absolute path to the SQLite database file."""
    return os.path.abspath(DB_FILENAME)
    
# -----------------------
# Date helpers
# -----------------------
def ui_to_db_date(ui_date_str):
    """
    Convert DD/MM/YYYY (UI) -> YYYY-MM-DD (DB).
    Returns string in ISO or raises ValueError if invalid.
    Accepts also already-ISO strings and returns them unchanged.
    """
    if not ui_date_str:
        return ""
    ui_date_str = ui_date_str.strip()
    # if already ISO
    if "-" in ui_date_str and len(ui_date_str.split("-")[0]) == 4:
        return ui_date_str
    # assume DD/MM/YYYY
    try:
        d = datetime.strptime(ui_date_str, "%d/%m/%Y")
        return d.strftime("%Y-%m-%d")
    except Exception:
        raise ValueError(f"Invalid date format (expected DD/MM/YYYY): '{ui_date_str}'")

def db_to_ui_date(db_date_str):
    """
    Convert YYYY-MM-DD (DB) -> DD/MM/YYYY (UI).
    If empty or None, return empty string.
    """
    if not db_date_str:
        return ""
    db_date_str = db_date_str.strip()
    # if already in dd/mm/yyyy format
    if "/" in db_date_str:
        return db_date_str
    try:
        d = datetime.strptime(db_date_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except Exception:
        # fallback: return as-is
        return db_date_str

# -----------------------
# Backup & connection
# -----------------------
def backup_db():
    """Create a timestamped copy of the DB in BACKUP_DIR and return its path."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"fabric_backup_{ts}.db")
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, dest)
    else:
        # create empty DB copy if none exists
        open(dest, "wb").close()
    return dest

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------
# Initialization / migration
# -----------------------
def init_db():
    """
    Initialize DB and perform migrations. Creates backup before running migrations.
    """
    # ensure DB exists
    created = False
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "w").close()
        created = True

    backup = backup_db()
    print(f"[DB] Backup created at {backup}")

    conn = get_connection()
    cur = conn.cursor()

    # --- suppliers / masters table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT DEFAULT 'yarn_supplier',  -- yarn_supplier / knitting_unit / dyeing_unit
        color_code TEXT DEFAULT ''
    )
    """)

    # --- yarn types ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS yarn_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # --- purchases (raw incoming/outgoing records) ---
    # date stored as YYYY-MM-DD in DB
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

    # --- batches & lots ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_ref TEXT,                 -- user visible batch id (e.g., "200")
        fabricator_id INTEGER,          -- suppliers.id
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
        lot_index INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(batch_id) REFERENCES batches(id)
    )
    """)

    # --- dyeing outputs: returned items after dyeing ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dyeing_outputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        dyeing_unit_id INTEGER,
        returned_date TEXT,
        returned_qty_kg REAL,
        returned_qty_rolls INTEGER,
        notes TEXT,
        FOREIGN KEY(lot_id) REFERENCES lots(id),
        FOREIGN KEY(dyeing_unit_id) REFERENCES suppliers(id)
    )
    """)

    # indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_delivered_to ON purchases(delivered_to)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_batch ON purchases(batch_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_batches_ref ON batches(batch_ref)")

    conn.commit()
    conn.close()

    if created:
        print("[DB] New DB created and initialized.")
    else:
        print("[DB] DB init/migrations complete.")

# -----------------------
# Helper functions (CRUD + convenience)
# -----------------------
def get_fabricators(fab_type):
    """Return list of master rows (sqlite3.Row) of given type ('knitting_unit' or 'dyeing_unit')."""
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

def delete_master_by_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM suppliers WHERE name=?", (name,))
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
    cur.execute("SELECT batch_ref FROM batches WHERE id=?", (batch_id,))
    row = cur.fetchone()
    batch_ref = row["batch_ref"] if row else str(batch_id)
    lot_no = f"{batch_ref}/{lot_index}"
    cur.execute("INSERT INTO lots (batch_id, lot_no, lot_index) VALUES (?, ?, ?)", (batch_id, lot_no, lot_index))
    lid = cur.lastrowid
    conn.commit()
    conn.close()
    return lid

def find_lot_by_lotno(lot_no):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lots WHERE lot_no=?", (lot_no,))
    row = cur.fetchone()
    conn.close()
    return row

def record_purchase(date_ui, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to, notes=""):
    """
    date_ui: DD/MM/YYYY (UI). Will be converted to ISO for storage.
    """
    # convert date
    try:
        db_date = ui_to_db_date(date_ui) if date_ui else ""
    except ValueError:
        # allow direct ISO if user passed that
        db_date = date_ui
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases (date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (db_date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to, notes))
    conn.commit()
    conn.close()

def record_dyeing_output(lot_id, dyeing_unit_id, returned_date_ui, returned_qty_kg, returned_qty_rolls, notes=""):
    try:
        db_date = ui_to_db_date(returned_date_ui) if returned_date_ui else ""
    except ValueError:
        db_date = returned_date_ui
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dyeing_outputs (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lot_id, dyeing_unit_id, db_date, returned_qty_kg, returned_qty_rolls, notes))
    conn.commit()
    conn.close()

# convenience read helpers used by UI modules
def list_suppliers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def list_yarn_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM yarn_types ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_yarn_type(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO yarn_types (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

# --------- Additional report helpers ----------
def get_purchases_between_dates(start_iso, end_iso):
    """Get purchases where date between ISO start and end (inclusive)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to
        FROM purchases
        WHERE date >= ? AND date <= ?
        ORDER BY date
    """, (start_iso, end_iso))
    rows = cur.fetchall()
    conn.close()
    return rows

# End of db.py
