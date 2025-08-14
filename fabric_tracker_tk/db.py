import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "fabric.db"
BACKUP_DIR = "backups"
MAX_BACKUPS = 5  # keep only latest 5 backups
DEFAULT_NAMES = ["Shiv Fabrics", "Oswal Finishing Mills"]

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

def restore_backup(path):
    if os.path.exists(path):
        shutil.copy2(path, get_db_path())

# ----------------------------
# Database Connection
# ----------------------------
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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
    CREATE TABLE IF NOT EXISTS fabric_types (
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
        FOREIGN KEY(lot_id) REFERENCES lots(id) ON DELETE CASCADE,
        FOREIGN KEY(dyeing_unit_id) REFERENCES suppliers(id)
    )
    """)

    # Helpful indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_delivered_to ON purchases(delivered_to)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_batch ON purchases(batch_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_batches_ref ON batches(batch_ref)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_type ON suppliers(type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_yarn_types_name ON yarn_types(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fabric_types_name ON fabric_types(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lots_lot_no ON lots(lot_no)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_lot_no ON purchases(lot_no)")

    conn.commit()

    # Default suppliers / units
    for unit_name, unit_type in [
        ("Shiv Fabrics", "knitting_unit"),
        ("Oswal Finishing Mills", "dyeing_unit")
    ]:
        cur.execute("SELECT id FROM suppliers WHERE name=? AND type=?", (unit_name, unit_type))
        if not cur.fetchone():
            cur.execute("INSERT INTO suppliers (name, type) VALUES (?, ?)", (unit_name, unit_type))

    conn.commit()
    conn.close()
    print("[DB] New DB created and initialized." if created else "[DB] DB init/migrations complete.")


# ----------------------------
# Date Helpers
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
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Invalid date '{ui_date}': {e}")

# ----------------------------
# LIKE Helper
# ----------------------------
def _escape_like(s: str) -> str:
    return s.replace("%", r"\%").replace("_", r"\_")

# ----------------------------
# Supplier / Masters
# ----------------------------
def list_suppliers(supplier_type=None):
    conn = get_connection()
    cur = conn.cursor()
    if supplier_type:
        cur.execute("SELECT id, name, color_code, type FROM suppliers WHERE type=? ORDER BY name", (supplier_type,))
    else:
        cur.execute("SELECT id, name, type, color_code FROM suppliers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def search_suppliers_prefix(prefix: str, supplier_type: str = None, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    conn = get_connection()
    cur = conn.cursor()
    if supplier_type:
        cur.execute(r"""
            SELECT id, name, type, color_code FROM suppliers
            WHERE type=? AND name LIKE ? ESCAPE '\'
            ORDER BY name LIMIT ?
        """, (supplier_type, like, limit))
    else:
        cur.execute(r"""
            SELECT id, name, type, color_code FROM suppliers
            WHERE name LIKE ? ESCAPE '\'
            ORDER BY name LIMIT ?
        """, (like, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_master(name, mtype="yarn_supplier", color_code=""):
    if not name or not name.strip():
        return
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO suppliers (name, type, color_code) VALUES (?, ?, ?)",
        (name.strip(), mtype, color_code)
    )
    conn.commit()
    conn.close()

def update_master_color_and_type(name, mtype, color_hex):
    conn = get_connection()
    conn.execute("UPDATE suppliers SET type=?, color_code=? WHERE name=?", (mtype, color_hex, name))
    conn.commit()
    conn.close()

def delete_master_by_name(name: str):
    """
    Safe delete: removes supplier if not referenced in purchases, batches, or dyeing outputs.
    Default units are deletable.
    """
    if not name or not name.strip():
        return False
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM suppliers WHERE name=? LIMIT 1", (name.strip(),))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    sid = row["id"]

    # Skip reference check for default units
    if name not in DEFAULT_NAMES:
        for table, col in [
            ("purchases", "supplier"),
            ("purchases", "delivered_to"),
            ("batches", "fabricator_id"),
            ("dyeing_outputs", "dyeing_unit_id")
        ]:
            cur.execute(f"SELECT 1 FROM {table} WHERE {col}=? LIMIT 1", (name if col in ("supplier", "delivered_to") else sid,))
            if cur.fetchone():
                conn.close()
                return False

    cur.execute("DELETE FROM suppliers WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return True

def get_supplier_id_by_name(name: str, required_type: str = None):
    if not name or not name.strip():
        return None
    conn = get_connection()
    cur = conn.cursor()
    if required_type:
        cur.execute("SELECT id FROM suppliers WHERE name=? AND type=? LIMIT 1", (name.strip(), required_type))
    else:
        cur.execute("SELECT id FROM suppliers WHERE name=? LIMIT 1", (name.strip(),))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else None

def is_delivered_to_valid(name):
    if not name or not name.strip():
        return False
    conn = get_connection()
    exists = conn.execute("SELECT 1 FROM suppliers WHERE name=? LIMIT 1", (name.strip(),)).fetchone() is not None
    conn.close()
    return exists

# ----------------------------
# Yarn Types
# ----------------------------
def list_yarn_types():
    conn = get_connection()
    rows = [r["name"] for r in conn.execute("SELECT DISTINCT name FROM yarn_types ORDER BY name").fetchall()]
    conn.close()
    return rows

def add_yarn_type(name: str):
    if not name or not name.strip():
        return
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO yarn_types (name) VALUES (?)", (name.strip(),))
    conn.commit()
    conn.close()

def search_yarn_types_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    conn = get_connection()
    rows = [r["name"] for r in conn.execute(
        r"SELECT name FROM yarn_types WHERE name LIKE ? ESCAPE '\' ORDER BY name LIMIT ?", (like, limit)
    ).fetchall()]
    conn.close()
    return rows

# ----------------------------
# Fabric Types
# ----------------------------
def list_fabric_types():
    conn = get_connection()
    rows = [r["name"] for r in conn.execute("SELECT DISTINCT name FROM fabric_types ORDER BY name").fetchall()]
    conn.close()
    return rows

def add_fabric_type(name: str):
    if not name or not name.strip():
        return
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO fabric_types (name) VALUES (?)", (name.strip(),))
    conn.commit()
    conn.close()

def search_fabric_types_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    conn = get_connection()
    rows = [r["name"] for r in conn.execute(
        r"SELECT name FROM fabric_types WHERE name LIKE ? ESCAPE '\' ORDER BY name LIMIT ?", (like, limit)
    ).fetchall()]
    conn.close()
    return rows

# ----------------------------
# Fabricators / Batches / Lots
# ----------------------------
def get_fabricators(fab_type):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM suppliers WHERE type=? ORDER BY name", (fab_type,)).fetchall()
    conn.close()
    return rows

def get_batches_for_fabricator(fabricator_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM batches WHERE fabricator_id=? ORDER BY created_at DESC", (fabricator_id,)).fetchall()
    conn.close()
    return rows

def search_batches_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    conn = get_connection()
    rows = [r["batch_ref"] for r in conn.execute(
        r"SELECT batch_ref FROM batches WHERE batch_ref LIKE ? ESCAPE '\' ORDER BY batch_ref LIMIT ?", (like, limit)
    ).fetchall()]
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
    for i in range(1, expected_lots + 1):
        create_lot(bid, i)
    conn.commit()
    conn.close()
    return bid

def create_lot(batch_id, lot_index):
    conn = get_connection()
    cur = conn.cursor()
    batch_ref = cur.execute("SELECT batch_ref FROM batches WHERE id=?", (batch_id,)).fetchone()["batch_ref"]
    lot_no = f"{batch_ref}/{lot_index}"
    cur.execute("INSERT INTO lots (batch_id, lot_no, lot_index) VALUES (?, ?, ?)", (batch_id, lot_no, lot_index))
    lid = cur.lastrowid
    conn.commit()
    conn.close()
    return lid

def get_lot_id_by_no(lot_no: str):
    if not lot_no or not lot_no.strip():
        return None
    conn = get_connection()
    row = conn.execute("SELECT id FROM lots WHERE lot_no=? LIMIT 1", (lot_no.strip(),)).fetchone()
    conn.close()
    return row["id"] if row else None

def search_lots_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    conn = get_connection()
    rows = [r["lot_no"] for r in conn.execute(
        r"SELECT lot_no FROM lots WHERE lot_no LIKE ? ESCAPE '\' ORDER BY lot_no LIMIT ?", (like, limit)
    ).fetchall()]
    conn.close()
    return rows

# ----------------------------
# Purchases / Dyeing Outputs
# ----------------------------
def record_purchase(date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls,
                    price_per_unit=0, delivered_to="", notes=""):
    if not is_delivered_to_valid(delivered_to):
        raise ValueError(f"Delivered To '{delivered_to}' not found in Masters.")
    conn = get_connection()
    conn.execute("""
        INSERT INTO purchases (date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ui_to_db_date(date), batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes))
    conn.commit()
    conn.close()

def edit_purchase(purchase_id, date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls,
                  price_per_unit, delivered_to, notes=""):
    if not is_delivered_to_valid(delivered_to):
        raise ValueError(f"Delivered To '{delivered_to}' not found in Masters.")
    conn = get_connection()
    conn.execute("""
        UPDATE purchases
        SET date=?, batch_id=?, lot_no=?, supplier=?, yarn_type=?, qty_kg=?, qty_rolls=?, price_per_unit=?, delivered_to=?, notes=?
        WHERE id=?
    """, (ui_to_db_date(date), batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes, purchase_id))
    conn.commit()
    conn.close()

def delete_purchase(purchase_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))
    conn.commit()
    conn.close()

def record_dyeing_output(lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes=""):
    resolved_lot_id = None
    if isinstance(lot_id, int):
        resolved_lot_id = lot_id
    else:
        try:
            resolved_lot_id = int(str(lot_id).strip())
        except Exception:
            resolved_lot_id = get_lot_id_by_no(lot_id)
    conn = get_connection()
    conn.execute("""
        INSERT INTO dyeing_outputs (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (resolved_lot_id, dyeing_unit_id, ui_to_db_date(returned_date), returned_qty_kg, returned_qty_rolls, notes))
    conn.commit()
    conn.close()
