import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "fabric.db"
BACKUP_DIR = "backups"
MAX_BACKUPS = 5  # keep only latest 5 backups

# ----------------------------
# Backup / Restore Utilities
# ----------------------------
def get_db_path():
    return os.path.join(os.path.dirname(__file__), DB_PATH)

def backup_db():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"fabric_backup_{ts}.db")
    if os.path.exists(get_db_path()):
        shutil.copy2(get_db_path(), dest)

    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("fabric_backup_")])
    while len(backups) > MAX_BACKUPS:
        old_backup = backups.pop(0)
        try:
            os.remove(os.path.join(BACKUP_DIR, old_backup))
        except Exception:
            pass
    return dest

# ----------------------------
# Database Connection
# ----------------------------
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------
# DB Initialization / Migrations
# ----------------------------
def init_db():
    created = False
    if not os.path.exists(get_db_path()):
        open(get_db_path(), "w").close()
        created = True

    backup = backup_db()
    print(f"[DB] Backup created at {backup}")

    conn = get_connection()
    cur = conn.cursor()

    # Core tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT DEFAULT 'yarn_supplier',
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
        price_per_unit REAL DEFAULT 0,
        delivered_to TEXT,
        notes TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_ref TEXT UNIQUE,
        fabricator_id INTEGER,
        product_name TEXT,
        expected_lots INTEGER DEFAULT 0,
        composition TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(fabricator_id) REFERENCES suppliers(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        lot_no TEXT UNIQUE,
        lot_index INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(batch_id) REFERENCES batches(id)
    )
    """)
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

    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_delivered_to ON purchases(delivered_to)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_batch ON purchases(batch_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_batches_ref ON batches(batch_ref)")

    conn.commit()

    # Add default knitting and dyeing units
    for unit_name, unit_type in [("Default Knitting Unit", "knitting_unit"), ("Default Dyeing Unit", "dyeing_unit")]:
        cur.execute("SELECT id FROM suppliers WHERE name=? AND type=?", (unit_name, unit_type))
        if not cur.fetchone():
            cur.execute("INSERT INTO suppliers (name, type) VALUES (?, ?)", (unit_name, unit_type))
    conn.commit()
    conn.close()

    if created:
        print("[DB] New DB created and initialized.")
    else:
        print("[DB] DB init/migrations complete.")

# ----------------------------
# Date Conversion Helpers
# ----------------------------
def db_to_ui_date(db_date: str) -> str:
    if not db_date:
        return ""
    dt = datetime.strptime(db_date, "%Y-%m-%d")
    return dt.strftime("%d/%m/%Y")

def ui_to_db_date(ui_date: str) -> str:
    if not ui_date:
        return ""
    ui_date = ui_date.replace("-", "/").strip()
    parts = ui_date.split("/")
    try:
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            year = datetime.now().year
        elif len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                current_year = datetime.now().year
                century = current_year // 100
                year += century * 100
                if year > current_year + 20:
                    year -= 100
        else:
            raise ValueError(f"Cannot parse date: {ui_date}")
        dt = datetime(year, month, day)
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Invalid date '{ui_date}': {e}")

# ----------------------------
# Supplier / Masters
# ----------------------------
def list_suppliers(supplier_type=None):
    conn = get_connection()
    cur = conn.cursor()
    if supplier_type:
        cur.execute("SELECT id, name, color_code FROM suppliers WHERE type=? ORDER BY name", (supplier_type,))
    else:
        cur.execute("SELECT id, name, type, color_code FROM suppliers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_master(name, mtype="yarn_supplier", color_code=""):
    if not name.strip():
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO suppliers (name, type, color_code) VALUES (?, ?, ?)", (name.strip(), mtype, color_code))
    conn.commit()
    conn.close()

def update_master_color_and_type(name, mtype, color_hex):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE suppliers SET type=?, color_code=? WHERE name=?", (mtype, color_hex, name))
    conn.commit()
    conn.close()

def is_delivered_to_valid(name):
    if not name.strip():
        return False
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM suppliers WHERE name=? LIMIT 1", (name.strip(),))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

# ----------------------------
# Yarn Types
# ----------------------------
def list_yarn_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT name FROM yarn_types")
    rows = [r["name"] for r in cur.fetchall()]
    conn.close()
    return rows

# ----------------------------
# Fabricators / Batches / Lots
# ----------------------------
def get_fabricators(fab_type):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers WHERE type=? ORDER BY name", (fab_type,))
    rows = cur.fetchall()
    conn.close()
    return rows

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

    # Auto-create lots
    for i in range(1, expected_lots+1):
        create_lot(bid, i)
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

# ----------------------------
# Purchases / Dyeing Outputs
# ----------------------------
def record_purchase(date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit=0, delivered_to="", notes=""):
    if not is_delivered_to_valid(delivered_to):
        raise ValueError(f"Delivered To '{delivered_to}' not found in Masters.")
    conn = get_connection()
    cur = conn.cursor()
    db_date = ui_to_db_date(date)
    cur.execute("""
        INSERT INTO purchases (date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (db_date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes))
    conn.commit()
    conn.close()

def edit_purchase(purchase_id, date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes=""):
    if not is_delivered_to_valid(delivered_to):
        raise ValueError(f"Delivered To '{delivered_to}' not found in Masters.")
    conn = get_connection()
    cur = conn.cursor()
    db_date = ui_to_db_date(date)
    cur.execute("""
        UPDATE purchases
        SET date=?, batch_id=?, lot_no=?, supplier=?, yarn_type=?, qty_kg=?, qty_rolls=?, price_per_unit=?, delivered_to=?, notes=?
        WHERE id=?
    """, (db_date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes, purchase_id))
    conn.commit()
    conn.close()

def record_dyeing_output(lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    db_date = ui_to_db_date(returned_date)
    cur.execute("""
        INSERT INTO dyeing_outputs (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lot_id, dyeing_unit_id, db_date, returned_qty_kg, returned_qty_rolls, notes))
    conn.commit()
    conn.close()
