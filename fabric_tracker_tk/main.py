import tkinter as tk
from tkinter import ttk
from fabric_tracker_tk import db
from ui_dashboard import DashboardFrame
from ui_entries import EntriesFrame
from ui_masters import MastersFrame
from ui_fabricators import FabricatorsFrame
from reports import ReportsFrame
from backup_restore import BackupRestoreFrame  # import the backup/restore UI

class FabricTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fabric Tracker (All-in-One)")
        self.geometry("1200x800")
        db.init_db()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # create frames
        self.dashboard_frame = DashboardFrame(self.notebook, self)
        self.entries_frame = EntriesFrame(self.notebook, self)
        self.fabricators_frame = FabricatorsFrame(self.notebook, controller=self)
        self.masters_frame = MastersFrame(self.notebook, controller=self, on_change_callback=self.reload_fabricators)
        self.reports_frame = ReportsFrame(self.notebook, self)
        self.backup_frame = BackupRestoreFrame(self.notebook, controller=self)  # create backup/restore tab

        # add to notebook
        self.notebook.add(self.entries_frame, text="Entries")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.fabricators_frame, text="Fabricators")
        self.notebook.add(self.masters_frame, text="Masters")
        self.notebook.add(self.reports_frame, text="Reports")
        self.notebook.add(self.backup_frame, text="Backup & Restore")  # add the new tab

    def reload_fabricators(self):
        # called when Masters change
        try:
            self.fabricators_frame.build_tabs()
        except Exception as e:
            print("Error reloading fabricators:", e)

    def open_dyeing_tab_for_batch(self, dyeer_name, batch_ref):
        # proxy to fabricators frame
        if hasattr(self.fabricators_frame, "open_dyeing_tab_for_batch"):
            self.fabricators_frame.open_dyeing_tab_for_batch(dyeer_name, batch_ref)

if __name__ == "__main__":
    app = FabricTrackerApp()
    app.mainloop()
