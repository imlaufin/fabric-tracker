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
        # Called when Masters change
        try:
            self.fabricators_frame.build_tabs()
            self.update_statuses()  # Update statuses across tabs
        except Exception as e:
            print("Error reloading fabricators:", e)

    def update_statuses(self):
        # Update batch/lot statuses based on purchases/dyeing
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE batches SET status='Knitted' WHERE id IN (SELECT batch_id FROM purchases WHERE delivered_to LIKE '%Knitting%')")
            cur.execute("UPDATE lots SET status='Knitted' WHERE batch_id IN (SELECT batch_id FROM purchases WHERE delivered_to LIKE '%Knitting%')")
            cur.execute("UPDATE batches SET status='Dyed' WHERE id IN (SELECT batch_id FROM dyeing_outputs)")
            cur.execute("UPDATE lots SET status='Dyed' WHERE id IN (SELECT lot_id FROM dyeing_outputs)")
            cur.execute("UPDATE batches SET status='Received' WHERE id IN (SELECT batch_id FROM dyeing_outputs WHERE returned_qty_kg > 0)")
            cur.execute("UPDATE lots SET status='Received' WHERE id IN (SELECT lot_id FROM dyeing_outputs WHERE returned_qty_kg > 0)")
            conn.commit()
        self.entries_frame.reload_entries()
        self.fabricators_frame.build_tabs()
        self.dashboard_frame.reload_all()

    def open_dyeing_tab_for_batch(self, dyeer_name, batch_ref):
        # Proxy to fabricators frame
        if hasattr(self.fabricators_frame, "open_dyeing_tab_for_batch"):
            self.fabricators_frame.open_dyeing_tab_for_batch(dyeer_name, batch_ref)


if __name__ == "__main__":
    app = FabricTrackerApp()
    app.protocol("WM_DELETE_WINDOW", lambda: [db.backup_db(), app.destroy()])  # Auto-backup on close
    app.mainloop()
