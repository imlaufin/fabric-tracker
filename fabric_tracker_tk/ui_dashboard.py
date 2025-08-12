import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import db
import openpyxl


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_filters()
        self.load_data()

    def build_ui(self):
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Delivered To filter
        ttk.Label(filter_frame, text="Delivered To:").pack(side="left")
        self.delivered_filter = ttk.Combobox(filter_frame, state="readonly")
        self.delivered_filter.pack(side="left", padx=5)

        # Yarn Type filter
        ttk.Label(filter_frame, text="Yarn Type:").pack(side="left")
        self.yarn_filter = ttk.Combobox(filter_frame, state="readonly")
        self.yarn_filter.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Apply Filters", command=self.load_data).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Export to Excel", command=self.export_to_excel).pack(side="right", padx=5)

        # Treeview
        columns = ("delivered_to", "yarn_type", "total_kg", "total_rolls")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("delivered_to", text="Delivered To")
        self.tree.heading("yarn_type", text="Yarn Type")
        self.tree.heading("total_kg", text="Total (kg)")
        self.tree.heading("total_rolls", text="Total (rolls)")

        self.tree.column("delivered_to", width=150)
        self.tree.column("yarn_type", width=150)
        self.tree.column("total_kg", width=100)
        self.tree.column("total_rolls", width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.total_label = ttk.Label(self, text="", font=("Arial", 10, "bold"))
        self.total_label.pack(side="bottom", pady=5)

    def load_filters(self):
        suppliers = [s["name"] for s in db.list_suppliers()]
        yarn_types = db.list_yarn_types()

        self.delivered_filter["values"] = [""] + suppliers
        self.yarn_filter["values"] = [""] + yarn_types

    def clear_filters(self):
        self.delivered_filter.set("")
        self.yarn_filter.set("")
        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        delivered_to = self.delivered_filter.get().strip()
        yarn_type = self.yarn_filter.get().strip()

        query = """
            SELECT delivered_to, yarn_type, SUM(qty_kg) AS total_kg, SUM(qty_rolls) AS total_rolls
            FROM purchases
        """
        params = []
        conditions = []

        if delivered_to:
            conditions.append("delivered_to = ?")
            params.append(delivered_to)
        if yarn_type:
            conditions.append("yarn_type = ?")
            params.append(yarn_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY delivered_to, yarn_type ORDER BY delivered_to, yarn_type"

        conn = db.get_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()

        total_kg_sum = total_rolls_sum = 0
        for r in rows:
            self.tree.insert("", "end", values=(
                r["delivered_to"], r["yarn_type"], r["total_kg"] or 0, r["total_rolls"] or 0
            ))
            total_kg_sum += r["total_kg"] or 0
            total_rolls_sum += r["total_rolls"] or 0

        self.total_label.config(text=f"TOTAL: {total_kg_sum} kg, {total_rolls_sum} rolls")

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Stock Dashboard"

        # Header
        ws.append(["Delivered To", "Yarn Type", "Total (kg)", "Total (rolls)"])

        # Data
        for row_id in self.tree.get_children():
            row_data = self.tree.item(row_id, "values")
            ws.append(row_data)

        # Totals row
        ws.append([])
        ws.append([self.total_label.cget("text")])

        try:
            wb.save(file_path)
            messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
