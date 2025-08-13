# ui_dashboard.py
import tkinter as tk
from tkinter import ttk, filedialog
from openpyxl import Workbook
import db

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_data()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Global Dashboard", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.load_data).pack(side="right")

        cols = ("party","yarn","kg","rolls")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("party", text="Party")
        self.tree.heading("yarn", text="Yarn Type")
        self.tree.heading("kg", text="Net (kg)")
        self.tree.heading("rolls", text="Net (rolls)")
        for c,w in zip(cols,[200,200,120,120]):
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Button(self, text="Export", command=self.export).pack(pady=4)

    def load_data(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        # net: + supplier deliveries, - when they send (delivered_to)
        query = """
            SELECT party, yarn_type, SUM(qty_change_kg) as kg, SUM(qty_change_rolls) as rolls
            FROM (
                SELECT supplier as party, yarn_type, qty_kg as qty_change_kg, qty_rolls as qty_change_rolls FROM purchases WHERE supplier IS NOT NULL AND supplier != ''
                UNION ALL
                SELECT delivered_to as party, yarn_type, -qty_kg as qty_change_kg, -qty_rolls as qty_change_rolls FROM purchases WHERE delivered_to IS NOT NULL AND delivered_to != ''
            ) t
            GROUP BY party, yarn_type
            ORDER BY party, yarn_type
        """
        cur.execute(query)
        for row in cur.fetchall():
            self.tree.insert("", "end", values=(row["party"], row["yarn_type"], row["kg"], row["rolls"]))
        conn.close()

    def export(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")])
        if not file_path:
            return
        wb = Workbook()
        ws = wb.active
        ws.append(["Party","Yarn Type","Net (kg)","Net (rolls)"])
        for r in self.tree.get_children():
            ws.append(self.tree.item(r)["values"])
        wb.save(file_path)
