# main.py
import tkinter as tk
from tkinter import ttk
import db

# Import UI modules (these should be the updated files you received)
from ui_dashboard import DashboardFrame
from ui_entries import EntriesFrame
from ui_masters import MastersFrame
from ui_fabricators import FabricatorsFrame  # or FabricatorsNotebook / FabricatorsFrame depending on the file you used
from reports import ReportsFrame

class FabricTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fabric Tracker")
        self.geometry("1200x800")

        # initialize DB (creates backups & migrations if needed)
        db.init_db()

        # main notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Create frames
        self.entries_frame = EntriesFrame(self.notebook, controller=self)
        self.dashboard_frame = DashboardFrame(self.notebook, controller=self)
        # FabricatorsFrame should dynamically create sub-tabs for knitting/dyeing units
        # depending on your ui_fabricators implementation it may be named FabricatorsFrame or similar.
        # Import in this file must match the class name in ui_fabricators.py.
        self.fabricators_frame = FabricatorsFrame(self.notebook, controller=self)
        # MastersFrame accepts a callback to notify when masters change so fabricator tabs reload instantly
        self.masters_frame = MastersFrame(self.notebook, on_masters_changed=self.reload_fabricators)
        self.reports_frame = ReportsFrame(self.notebook, controller=self)

        # Add tabs to notebook
        self.notebook.add(self.entries_frame, text="Entries")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.fabricators_frame, text="Fabricators")
        self.notebook.add(self.masters_frame, text="Masters")
        self.notebook.add(self.reports_frame, text="Reports")

        # keep references available for other components
        # so, for example, dashboard or entries code can call:
        # self.controller.fabricators_frame.build_tabs()
        self.entries_frame.controller = self
        self.dashboard_frame.controller = self
        self.fabricators_frame.controller = self
        self.masters_frame.controller = self
        self.reports_frame.controller = self

    def reload_fabricators(self):
        """
        Called when Masters are changed (add/edit/delete fabricator).
        Fabricators UI should rebuild its tabs on this call.
        """
        try:
            if hasattr(self.fabricators_frame, "build_tabs"):
                self.fabricators_frame.build_tabs()
            elif hasattr(self.fabricators_frame, "reload_all"):
                self.fabricators_frame.reload_all()
        except Exception as e:
            print("Error reloading fabricator tabs:", e)

    def open_dyeing_tab_for_batch(self, dyeer_name, batch_ref):
        """
        Called by a Knitting tab when the user requests to jump to the dyeing unit
        responsible for a batch. Proxy to fabricators_frame implementation.
        """
        try:
            if hasattr(self.fabricators_frame, "open_dyeing_tab_for_batch"):
                self.fabricators_frame.open_dyeing_tab_for_batch(dyeer_name, batch_ref)
        except Exception as e:
            print("Error opening dyeing tab for batch:", e)

if __name__ == "__main__":
    app = FabricTrackerApp()
    app.mainloop()
