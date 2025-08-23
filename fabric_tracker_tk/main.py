import sys
import tkinter as tk
from tkinter import ttk
from fabric_tracker_tk import db
from fabric_tracker_tk.ui_dashboard import DashboardFrame
from fabric_tracker_tk.ui_entries import EntriesFrame
from fabric_tracker_tk.ui_masters import MastersFrame
from fabric_tracker_tk.ui_fabricators import FabricatorsFrame
from fabric_tracker_tk.reports import ReportsFrame
from fabric_tracker_tk.backup_restore import BackupRestoreFrame  # import the backup/restore UI

class FabricTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fabric Tracker (All-in-One)")
        self.geometry("1200x800")
        try:
            db.init_db()  # Initialize database with persistent path
            # Verify schema migration (optional safeguard)
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(batches)")
                columns = [row["name"] for row in cur.fetchall()]
                if "fabric_type_id" in columns:
                    print("[DB] Warning: fabric_type_id still exists in batches table. Attempting to drop.", file=sys.stderr)
                    cur.execute("ALTER TABLE batches DROP COLUMN fabric_type_id")
                    conn.commit()
                    print("[DB] Successfully dropped fabric_type_id.", file=sys.stderr)
        except Exception as e:
            print(f"Database initialization failed: {e}", file=sys.stderr)
            self.destroy()
            return

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Create frames
        self.dashboard_frame = DashboardFrame(self.notebook, self)
        self.entries_frame = EntriesFrame(self.notebook, self)
        self.fabricators_frame = FabricatorsFrame(self.notebook, controller=self)
        self.masters_frame = MastersFrame(self.notebook, controller=self, on_change_callback=self.reload_fabricators)
        self.reports_frame = ReportsFrame(self.notebook, self)
        self.backup_frame = BackupRestoreFrame(self.notebook, controller=self)  # create backup/restore tab

        # Add to notebook
        self.notebook.add(self.entries_frame, text="Entries")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.fabricators_frame, text="Fabricators")
        self.notebook.add(self.masters_frame, text="Masters")
        self.notebook.add(self.reports_frame, text="Reports")
        self.notebook.add(self.backup_frame, text="Backup & Restore")  # add the new tab

    def reload_fabricators(self):
        # Called when Masters change, handles stage updates
        try:
            self.fabricators_frame.build_tabs()
            self.update_all_statuses()  # Propagate status updates
        except Exception as e:
            print("Error reloading fabricators:", e)

    def update_all_statuses(self):
        # Trigger status updates across all tabs
        with db.get_connection() as conn:
            cur = conn.cursor()
            # Update statuses based on transactions
            cur.execute("""
                UPDATE batches
                SET status='Knitted'
                WHERE id IN (
                    SELECT DISTINCT b.id
                    FROM batches b
                    JOIN purchases p ON b.batch_ref = p.batch_id
                    JOIN suppliers s ON s.name = p.delivered_to AND s.type = 'knitting_unit'
                )
            """)
            cur.execute("""
                UPDATE lots
                SET status='Knitted'
                WHERE batch_id IN (
                    SELECT DISTINCT b.id
                    FROM batches b
                    JOIN purchases p ON b.batch_ref = p.batch_id
                    JOIN suppliers s ON s.name = p.delivered_to AND s.type = 'knitting_unit'
                )
            """)
            cur.execute("""
                UPDATE batches
                SET status='Dyed'
                WHERE id IN (
                    SELECT DISTINCT b.id
                    FROM batches b
                    JOIN lots l ON b.id = l.batch_id
                    JOIN dyeing_outputs d ON l.id = d.lot_id
                    WHERE d.returned_qty_kg > 0
                )
            """)
            cur.execute("""
                UPDATE lots
                SET status='Dyed'
                WHERE id IN (
                    SELECT DISTINCT l.id
                    FROM lots l
                    JOIN dyeing_outputs d ON l.id = d.lot_id
                    WHERE d.returned_qty_kg > 0
                )
            """)
            cur.execute("""
                UPDATE batches
                SET status='Received'
                WHERE id IN (
                    SELECT DISTINCT b.id
                    FROM batches b
                    JOIN lots l ON b.id = l.batch_id
                    JOIN dyeing_outputs d ON l.id = d.lot_id
                    WHERE d.returned_qty_kg >= 0.9 * l.weight_kg
                )
            """)
            cur.execute("""
                UPDATE lots
                SET status='Received'
                WHERE id IN (
                    SELECT DISTINCT l.id
                    FROM lots l
                    JOIN dyeing_outputs d ON l.id = d.lot_id
                    WHERE d.returned_qty_kg >= 0.9 * l.weight_kg
                )
            """)
            # Set "Ordered" for lots/batches with purchases but no further processing
            cur.execute("""
                UPDATE lots
                SET status='Ordered'
                WHERE batch_id IN (
                    SELECT id FROM batches WHERE id IN (SELECT DISTINCT batch_id FROM purchases)
                ) AND status NOT IN ('Knitted', 'Dyed', 'Received')
            """)
            cur.execute("""
                UPDATE batches
                SET status='Ordered'
                WHERE id IN (SELECT DISTINCT batch_id FROM purchases)
                AND status NOT IN ('Knitted', 'Dyed', 'Received')
            """)
            conn.commit()

        # Reload all affected frames
        self.entries_frame.reload_entries()
        self.fabricators_frame.build_tabs()
        self.dashboard_frame.reload_all()
        if hasattr(self.reports_frame, "reload_data"):
            self.reports_frame.reload_data()

    def open_dyeing_tab_for_batch(self, dyeer_name, batch_ref):
        # Proxy to fabricators frame
        if hasattr(self.fabricators_frame, "open_dyeing_tab_for_batch"):
            self.fabricators_frame.open_dyeing_tab_for_batch(dyeer_name, batch_ref)

    def on_purchase_recorded(self, batch_id, lot_no, delivered_to):
        # Callback for purchase recording
        if batch_id and delivered_to:
            batch_id_int = db.get_batch_id_by_ref(batch_id)
            if batch_id_int:
                knitting_id = db.get_supplier_id_by_name(delivered_to, "knitting_unit")
                if knitting_id:
                    db.update_batch_status(batch_id_int, "Knitted")
                    if lot_no:
                        lot_id = db.get_lot_id_by_no(lot_no)
                        if lot_id:
                            db.update_lot_status(lot_id, "Knitted")
                else:
                    db.update_batch_status(batch_id_int, "Ordered")
                    if lot_no:
                        lot_id = db.get_lot_id_by_no(lot_no)
                        if lot_id:
                            db.update_lot_status(lot_id, "Ordered")
        self.update_all_statuses()

    def on_dyeing_output_recorded(self, lot_id):
        # Callback for dyeing output recording
        if lot_id:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT batch_id FROM lots WHERE id=?", (lot_id,))
                batch_id = cur.fetchone()["batch_id"]
                cur.execute("SELECT weight_kg FROM lots WHERE id=?", (lot_id,))
                weight_kg = cur.fetchone()["weight_kg"] or 0
                cur.execute("SELECT returned_qty_kg FROM dyeing_outputs WHERE lot_id=? ORDER BY id DESC LIMIT 1", (lot_id,))
                returned_kg = cur.fetchone()["returned_qty_kg"] or 0
                if returned_kg > 0 and returned_kg < 0.9 * weight_kg:
                    db.update_lot_status(lot_id, "Dyed")
                    if batch_id:
                        db.update_batch_status(batch_id, "Dyed")
                elif returned_kg >= 0.9 * weight_kg:
                    db.update_lot_status(lot_id, "Received")
                    if batch_id:
                        db.update_batch_status(batch_id, "Received")
            self.update_all_statuses()

if __name__ == "__main__":
    app = FabricTrackerApp()
    app.protocol("WM_DELETE_WINDOW", lambda: [db.backup_db(), app.destroy()])  # Auto-backup on close
    app.mainloop()
