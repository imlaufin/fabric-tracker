import tkinter as tk
from tkinter import ttk
import db

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_data()

    def build_ui(self):
        ttk.Label(self, text="Dashboard — Current Stock by Holder", font=("Arial", 14, "bold")).pack(pady=10)

        columns = ("holder", "yarn_type", "total_kg", "total_rolls")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("holder", text="Holder")
        self.tree.heading("yarn_type", text="Yarn Type")
        self.tree.heading("total_kg", text="Total (kg)")
        self.tree.heading("total_rolls", text="Total (rolls)")

        self.tree.column("holder", width=150)
        self.tree.column("yarn_type", width=150)
        self.tree.column("total_kg", width=100)
        self.tree.column("total_rolls", width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(self, text="Refresh", command=self.load_data).pack(pady=5)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT delivered_to, yarn_type, SUM(qty_kg), SUM(qty_rolls)
            FROM purchases
            GROUP BY delivered_to, yarn_type
            ORDER BY delivered_to, yarn_type
        """)
        for holder, yarn_type, total_kg, total_rolls in cur.fetchall():
            self.tree.insert("", "end", values=(
                holder or "Unknown", yarn_type, total_kg or 0, total_rolls or 0
            ))
        conn.close()
