import tkinter as tk
from tkinter import ttk, filedialog
from openpyxl import Workbook
from fabric_tracker_tk import db
from datetime import datetime

class ReportsFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=6)

        ttk.Label(top, text="Financial Year Start").grid(row=0, column=0)
        self.fy_start = ttk.Combobox(top, values=self._generate_fy_years(), width=10)
        self.fy_start.grid(row=0, column=1)
        self.fy_start.set(self._default_fy())

        ttk.Button(top, text="Apply", command=self.load_report).grid(row=0, column=2, padx=6)
        ttk.Button(top, text="Export to Excel", command=self.export_report).grid(row=0, column=3, padx=6)

        self.tree = ttk.Treeview(self, columns=("date", "batch", "supplier", "yarn", "kg", "rolls", "delivered"), show="headings")
        for c, h in zip(("date", "batch", "supplier", "yarn", "kg", "rolls", "delivered"), ["Date", "Batch", "Supplier", "Yarn", "Kg", "Rolls", "Delivered To"]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

    def _generate_fy_years(self):
        now = datetime.now().year
        vals = []
        for y in range(now - 5, now + 1):
            vals.append(str(y))
        return vals

    def _default_fy(self):
        # default to current FY start year
        now = datetime.now()
        if now.month >= 4:
            return str(now.year)
        else:
            return str(now.year - 1)

    def load_report(self):
        start_year = int(self.fy_start.get())
        fy_start_date = f"{start_year}-04-01"
        fy_end_year = start_year + 1
        fy_end_date = f"{fy_end_year}-03-31"
        for r in self.tree.get_children():
            self.tree.delete(r)
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to
                FROM purchases
                WHERE date >= ? AND date <= ?
                ORDER BY date
            """, (fy_start_date, fy_end_date))
            for row in cur.fetchall():
                display_date = db.db_to_ui_date(row["date"])
                self.tree.insert("", "end", values=(display_date, row["batch_id"], row["supplier"], row["yarn_type"], row["qty_kg"], row["qty_rolls"], row["delivered_to"]))
        # No connection.close() needed with context manager

    def export_report(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not file_path:
            return
        wb = Workbook()
        ws = wb.active
        ws.append(["Date", "Batch", "Supplier", "Yarn", "Kg", "Rolls", "Delivered To"])
        for r in self.tree.get_children():
            ws.append(self.tree.item(r)["values"])
        wb.save(file_path)

    def reload_data(self):
        # Refresh the report with the current financial year
        self.load_report()
