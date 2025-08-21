import sqlite3
import os
import sys
import shutil
from datetime import datetime

APP_NAME = "FabricTracker"
DB_NAME = "fabric_tracker.db"
BACKUP_DIR = "backups"
MAX_BACKUPS = 5  # keep only latest 5 backups
DEFAULT_NAMES = ["Shiv Fabrics", "Oswal Finishing Mills"]

# Define persistent database path
if os.name == 'nt':  # Windows
    BASE_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)
else:  # Linux/Mac
    BASE_DIR = os.path.join(os.path.expanduser('~'), '.' + APP_NAME.lower())
os.makedirs(BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

# Backup directory in persistent location
BACKUP_PATH = os.path.join(BASE_DIR, BACKUP_DIR)
os.makedirs(BACKUP_PATH, exist_ok=True)

# ----------------------------
# Backup / Restore Utilities
# ----------------------------
def get_db_path():
    """Returns the path to the database file in a persistent location."""
    return DB_PATH

def backup_db():
    """Create a timestamped backup and prune old ones."""
    if not os.path.exists(BACKUP_PATH):
        os.makedirs(BACKUP_PATH)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_PATH, f"fabric_backup_{ts}.db")
    if os.path.exists(get_db_path()):
        shutil.copy2(get_db_path(), dest)
    backups = sorted([f for f in os.listdir(BACKUP_PATH) if f.startswith("fabric_backup_")])
    while len(backups) > MAX_BACKUPS:
        old_backup = backups.pop(0)
        try:
            os.remove(os.path.join(BACKUP_PATH, old_backup))
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
    """
    Return a direct sqlite3 connection (works with both:
      - conn = get_connection(); cur = conn.cursor()
      - with get_connection() as conn:
    )
    """
    conn = sqlite3.connect(get_db_path(), timeout=10)
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

    with get_connection() as conn:
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
            status TEXT DEFAULT 'Ordered',
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
            weight_kg REAL,
            status TEXT DEFAULT 'Ordered',
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

        # Migration: Add missing columns to lots if they don't exist
        cur.execute("PRAGMA table_info(lots)")
        columns = [row["name"] for row in cur.fetchall()]
        if "weight_kg" not in columns:
            cur.execute("ALTER TABLE lots ADD COLUMN weight_kg REAL")
        if "status" not in columns:
            cur.execute("ALTER TABLE lots ADD COLUMN status TEXT DEFAULT 'Ordered'")

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
    with get_connection() as conn:
        cur = conn.cursor()
        if supplier_type:
            cur.execute("SELECT id, name, color_code, type FROM suppliers WHERE type=? ORDER BY name", (supplier_type,))
        else:
            cur.execute("SELECT id, name, type, color_code FROM suppliers ORDER BY name")
        rows = cur.fetchall()
    return rows

def search_suppliers_prefix(prefix: str, supplier_type: str = None, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    with get_connection() as conn:
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
    return rows

def add_master(name, mtype="yarn_supplier", color_code=""):
    if not name or not name.strip():
        return
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO suppliers (name, type, color_code) VALUES (?, ?, ?)",
            (name.strip(), mtype, color_code)
        )
        conn.commit()

def update_master_color_and_type(name, mtype, color_hex):
    with get_connection() as conn:
        conn.execute("UPDATE suppliers SET type=?, color_code=? WHERE name=?", (mtype, color_hex, name))
        conn.commit()

def delete_master_by_name(name: str):
    """
    Safe delete: removes supplier if not referenced in purchases, batches, or dyeing outputs.
    Default units are deletable.
    """
    if not name or not name.strip():
        return False
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM suppliers WHERE name=? LIMIT 1", (name.strip(),))
        row = cur.fetchone()
        if not row:
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
                cur.execute(
                    f"SELECT 1 FROM {table} WHERE {col}=? LIMIT 1",
                    (name if col in ("supplier", "delivered_to") else sid,)
                )
                if cur.fetchone():
                    return False

        cur.execute("DELETE FROM suppliers WHERE id=?", (sid,))
        conn.commit()
    return True

def get_supplier_id_by_name(name: str, required_type: str = None):
    if not name or not name.strip():
        return None
    with get_connection() as conn:
        cur = conn.cursor()
        if required_type:
            cur.execute("SELECT id FROM suppliers WHERE name=? AND type=? LIMIT 1", (name.strip(), required_type))
        else:
            cur.execute("SELECT id FROM suppliers WHERE name=? LIMIT 1", (name.strip(),))
        row = cur.fetchone()
    return row["id"] if row else None

def is_delivered_to_valid(name):
    if not name or not name.strip():
        return False
    with get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM suppliers WHERE name=? LIMIT 1", (name.strip(),)).fetchone() is not None
    return exists

# ----------------------------
# Yarn Types
# ----------------------------
def list_yarn_types():
    with get_connection() as conn:
        rows = [r["name"] for r in conn.execute("SELECT DISTINCT name FROM yarn_types ORDER BY name").fetchall()]
    return rows

def add_yarn_type(name: str):
    if not name or not name.strip():
        return
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO yarn_types (name) VALUES (?)", (name.strip(),))
        conn.commit()

def search_yarn_types_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    with get_connection() as conn:
        rows = [r["name"] for r in conn.execute(
            r"SELECT name FROM yarn_types WHERE name LIKE ? ESCAPE '\' ORDER BY name LIMIT ?", (like, limit)
        ).fetchall()]
    return rows

# ----------------------------
# Fabric Types
# ----------------------------
def list_fabric_types():
    with get_connection() as conn:
        rows = [r["name"] for r in conn.execute("SELECT DISTINCT name FROM fabric_types ORDER BY name").fetchall()]
    return rows

def add_fabric_type(name: str):
    if not name or not name.strip():
        return
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO fabric_types (name) VALUES (?)", (name.strip(),))
        conn.commit()

def search_fabric_types_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    with get_connection() as conn:
        rows = [r["name"] for r in conn.execute(
            r"SELECT name FROM fabric_types WHERE name LIKE ? ESCAPE '\' ORDER BY name LIMIT ?", (like, limit)
        ).fetchall()]
    return rows

# ----------------------------
# Fabricators / Batches / Lots
# ----------------------------
def get_fabricators(fab_type):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM suppliers WHERE type=? ORDER BY name", (fab_type,)).fetchall()
    return rows

def get_batches_for_fabricator(fabricator_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM batches WHERE fabricator_id=? ORDER BY created_at DESC", (fabricator_id,)).fetchall()
    return rows

def search_batches_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    with get_connection() as conn:
        rows = [r["batch_ref"] for r in conn.execute(
            r"SELECT batch_ref FROM batches WHERE batch_ref LIKE ? ESCAPE '\' ORDER BY batch_ref LIMIT ?", (like, limit)
        ).fetchall()]
    return rows

def create_batch(batch_ref, fabricator_id, product_name, expected_lots, composition=""):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO batches (batch_ref, fabricator_id, product_name, expected_lots, composition)
            VALUES (?, ?, ?, ?, ?)
        """, (batch_ref, fabricator_id, product_name, expected_lots, composition))
        bid = cur.lastrowid
        conn.commit()  # Commit batch immediately
        for i in range(1, expected_lots + 1):
            create_lot(bid, i)
    return bid

def create_lot(batch_id, lot_index, weight_kg=0):
    with get_connection() as conn:
        cur = conn.cursor()
        row = cur.execute("SELECT batch_ref FROM batches WHERE id=?", (batch_id,)).fetchone()
        if row is None:
            raise ValueError(f"Batch ID {batch_id} not found. Ensure the batch was created successfully.")
        batch_ref = row["batch_ref"]
        lot_no = f"{batch_ref}/{lot_index}"
        cur.execute(
            "INSERT INTO lots (batch_id, lot_no, lot_index, weight_kg) VALUES (?, ?, ?, ?)",
            (batch_id, lot_no, lot_index, weight_kg)
        )
        conn.commit()  # Commit each lot
        return cur.lastrowid

def get_lot_id_by_no(lot_no: str):
    if not lot_no or not lot_no.strip():
        return None
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM lots WHERE lot_no=? LIMIT 1", (lot_no.strip(),)).fetchone()
    return row["id"] if row else None

def search_lots_prefix(prefix: str, limit: int = 20):
    prefix = (prefix or "").strip()
    like = _escape_like(prefix) + "%"
    with get_connection() as conn:
        rows = [r["lot_no"] for r in conn.execute(
            r"SELECT lot_no FROM lots WHERE lot_no LIKE ? ESCAPE '\' ORDER BY lot_no LIMIT ?", (like, limit)
        ).fetchall()]
    return rows

# ----------------------------
# Purchases / Dyeing Outputs
# ----------------------------
def record_purchase(date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls,
                    price_per_unit=0, delivered_to="", notes=""):
    if not is_delivered_to_valid(delivered_to):
        raise ValueError(f"Delivered To '{delivered_to}' not found in Masters.")
    with get_connection() as conn:
        cur = conn.cursor()

        # Create batch (and its first lot) if they don't exist
        if not batch_id:
            fabricator_id = get_supplier_id_by_name(delivered_to, "knitting_unit")
            if fabricator_id:
                batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                cur.execute("""
                    INSERT INTO batches (batch_ref, fabricator_id, product_name, expected_lots, composition)
                    VALUES (?, ?, ?, ?, ?)
                """, (batch_id, fabricator_id, "Default Product", 1, ""))
                bid = cur.lastrowid
                conn.commit()  # Commit batch
                lot_no = f"{batch_id}/1"
                cur.execute(
                    "INSERT INTO lots (batch_id, lot_no, lot_index, weight_kg) VALUES (?, ?, ?, ?)",
                    (bid, lot_no, 1, qty_kg)
                )
                conn.commit()  # Commit lot

        cur.execute("""
            INSERT INTO purchases (date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ui_to_db_date(date), batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes))
        purchase_id = cur.lastrowid

        # Update lot weight and status within the same connection
        lot_id = get_lot_id_by_no(lot_no) if lot_no else None
        if lot_id:
            cur.execute("UPDATE lots SET weight_kg=?, status='Ordered' WHERE id=?", (qty_kg, lot_id))

        # Update batch status
        batch_id_int = get_batch_id_by_ref(batch_id)
        if batch_id_int:
            cur.execute("UPDATE batches SET status='Ordered' WHERE id=?", (batch_id_int,))
            cur.execute("UPDATE lots SET status='Ordered' WHERE batch_id=?", (batch_id_int,))
            if "Knitting" in delivered_to:
                cur.execute("UPDATE batches SET status='Knitted' WHERE id=?", (batch_id_int,))
                if lot_id:
                    cur.execute("UPDATE lots SET status='Knitted' WHERE id=?", (lot_id,))

        conn.commit()
    return purchase_id

def edit_purchase(purchase_id, date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls,
                  price_per_unit, delivered_to, notes=""):
    if not is_delivered_to_valid(delivered_to):
        raise ValueError(f"Delivered To '{delivered_to}' not found in Masters.")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE purchases
            SET date=?, batch_id=?, lot_no=?, supplier=?, yarn_type=?, qty_kg=?, qty_rolls=?, price_per_unit=?, delivered_to=?, notes=?
            WHERE id=?
        """, (ui_to_db_date(date), batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, price_per_unit, delivered_to, notes, purchase_id))
        # Update lot weight
        lot_id = get_lot_id_by_no(lot_no)
        if lot_id:
            cur.execute("UPDATE lots SET weight_kg=? WHERE id=?", (qty_kg, lot_id))
        conn.commit()

def delete_purchase(purchase_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT lot_no FROM purchases WHERE id=?", (purchase_id,))
        row = cur.fetchone()
        if row:
            lot_no = row["lot_no"]
            lot_id = get_lot_id_by_no(lot_no)
            if lot_id:
                cur.execute("DELETE FROM lots WHERE id=?", (lot_id,))
            cur.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))
        conn.commit()

def record_dyeing_output(lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes=""):
    resolved_lot_id = None
    if isinstance(lot_id, int):
        resolved_lot_id = lot_id
    else:
        try:
            resolved_lot_id = int(str(lot_id).strip())
        except Exception:
            resolved_lot_id = get_lot_id_by_no(lot_id)
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO dyeing_outputs (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (resolved_lot_id, dyeing_unit_id, ui_to_db_date(returned_date), returned_qty_kg, returned_qty_rolls, notes))
        # Update lot status based on completion
        if returned_qty_kg >= 0.9 * (conn.execute("SELECT weight_kg FROM lots WHERE id=?", (resolved_lot_id,)).fetchone()["weight_kg"] or 0):
            cur = conn.cursor()
            cur.execute("UPDATE lots SET status='Received' WHERE id=?", (resolved_lot_id,))
            # Update batch status if all lots are received
            cur.execute("SELECT batch_id FROM lots WHERE id=?", (resolved_lot_id,))
            batch_id = cur.fetchone()["batch_id"]
            cur.execute("SELECT MIN(status) AS min_status FROM lots WHERE batch_id=?", (batch_id,))
            min_status = cur.fetchone()["min_status"]
            if min_status == "Received":
                cur.execute("UPDATE batches SET status='Received' WHERE id=?", (batch_id,))
        conn.commit()

def delete_dyeing_output(dyeing_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM dyeing_outputs WHERE id=?", (dyeing_id,))
        conn.commit()

# Helper function to get batch_id by reference
def get_batch_id_by_ref(batch_ref):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM batches WHERE batch_ref=? LIMIT 1", (batch_ref,)).fetchone()
    return row["id"] if row else None

# ----------------------------
# New Functions
# ----------------------------
def update_batch_status(batch_id, status):
    if status not in ['Ordered', 'Knitted', 'Dyed', 'Received']:
        raise ValueError(f"Invalid status: {status}")
    with get_connection() as conn:
        conn.execute("UPDATE batches SET status=? WHERE id=?", (status, batch_id))
        conn.execute("UPDATE lots SET status=? WHERE batch_id=?", (status, batch_id))
        conn.commit()

def update_lot_status(lot_id, status):
    if status not in ['Ordered', 'Knitted', 'Dyed', 'Received']:
        raise ValueError(f"Invalid status: {status}")
    with get_connection() as conn:
        conn.execute("UPDATE lots SET status=? WHERE id=?", (status, lot_id))
        # Update batch status based on minimum lot status
        cur = conn.cursor()
        cur.execute("SELECT batch_id FROM lots WHERE id=?", (lot_id,))
        batch_id = cur.fetchone()["batch_id"]
        cur.execute("SELECT MIN(status) AS min_status FROM lots WHERE batch_id=?", (batch_id,))
        min_status = cur.fetchone()["min_status"]
        if min_status == status:
            conn.execute("UPDATE batches SET status=? WHERE id=?", (status, batch_id))
        conn.commit()

def get_batch_status(batch_id):
    with get_connection() as conn:
        row = conn.execute("SELECT status FROM batches WHERE id=? LIMIT 1", (batch_id,)).fetchone()
    return row["status"] if row else None

def get_lot_status(lot_id):
    with get_connection() as conn:
        row = conn.execute("SELECT status FROM lots WHERE id=? LIMIT 1", (lot_id,)).fetchone()
    return row["status"] if row else None

def calculate_net_price(batch_id):
    with get_connection() as conn:
        cur = conn.cursor()
        # Yarn cost
        cur.execute("SELECT SUM(price_per_unit * qty_kg) AS yarn_cost FROM purchases WHERE batch_id=?", (batch_id,))
        yarn_cost = cur.fetchone()["yarn_cost"] or 0

        # Knitting cost (e.g., $5 per kg for Shiv Fabrics)
        cur.execute("""
            SELECT p.delivered_to, SUM(p.qty_kg) AS total_kg
            FROM purchases p
            WHERE p.batch_id=? AND p.delivered_to IN ('Shiv Fabrics')
            GROUP BY p.delivered_to
        """, (batch_id,))
        knitting_row = cur.fetchone()
        knitting_cost = (knitting_row["total_kg"] or 0) * 5 if knitting_row else 0

        # Dyeing cost (e.g., $10 per kg for Oswal Finishing Mills)
        cur.execute("""
            SELECT SUM(d.returned_qty_kg) AS dyed_kg
            FROM dyeing_outputs d
            JOIN lots l ON d.lot_id = l.id
            JOIN batches b ON l.batch_id = b.id
            WHERE b.id=? AND d.dyeing_unit_id = (SELECT id FROM suppliers WHERE name='Oswal Finishing Mills' LIMIT 1)
        """, (batch_id,))
        dyeing_row = cur.fetchone()
        dyeing_cost = (dyeing_row["dyed_kg"] or 0) * 10 if dyeing_row else 0

        net_price = yarn_cost + knitting_cost + dyeing_cost
    return net_price

# ----------------------------
# Initialization on Import
# ----------------------------
init_db()
