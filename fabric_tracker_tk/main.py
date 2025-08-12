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
        self.geometry("1200x700")  # more space for filters + tables

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Create frames with mutual references
        self.dashboard_frame = DashboardFrame(self.notebook, self)
        self.entries_frame = EntriesFrame(self.notebook, self)
        self.masters_frame = MastersFrame(self.notebook, self)

        # Give dashboard a reference to entries
        self.dashboard_frame.controller = self
        self.entries_frame.controller = self

        # Add frames to notebook
        self.notebook.add(self.entries_frame, text="Entries")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.masters_frame, text="Masters")

if __name__ == "__main__":
    db.init_db()
    app = FabricTrackerApp()
    app.mainloop()
