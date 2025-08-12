import tkinter as tk
from tkinter import ttk
from ui_dashboard import DashboardFrame
from ui_entries import EntriesFrame
from ui_masters import MastersFrame
import db

class FabricTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fabric Tracker (Tkinter Version)")
        self.geometry("1200x700")  # little bigger for filters + tables

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Create frames
        self.dashboard_frame = DashboardFrame(self.notebook, self)
        self.entries_frame = EntriesFrame(self.notebook, self, dashboard_ref=self.dashboard_frame)
        self.masters_frame = MastersFrame(self.notebook, self)

        # Add tabs
        self.notebook.add(self.entries_frame, text="Entries")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.masters_frame, text="Masters")

if __name__ == "__main__":
    db.init_db()
    app = FabricTrackerApp()
    app.mainloop()
