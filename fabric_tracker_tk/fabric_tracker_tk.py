# fabric_tracker_tk.py
import tkinter as tk
from tkinter import ttk, messagebox

# Sample minimal starter code — replace with full code later
class FabricTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fabric Tracker - Tkinter")
        self.geometry("800x600")

        label = ttk.Label(self, text="Welcome to Fabric Tracker (Tkinter)")
        label.pack(pady=20)

if __name__ == "__main__":
    app = FabricTrackerApp()
    app.mainloop()
