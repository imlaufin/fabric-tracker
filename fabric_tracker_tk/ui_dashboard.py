import tkinter as tk
from tkinter import ttk, filedialog
from openpyxl import Workbook
import db

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.filter_supplier = tk.StringVar()
        self.filter_yarn = tk.StringVar()
        self.build_ui()
        self.load_data()

    def build_ui(self):
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Supplier:").pack(side="left")
        self.supplier_cb = ttk.Combobox(filter_frame, textvariable=self.filter_supplier, width=20)
        self.supplier_cb.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="Yarn Type:").pack(side="left")
        self.yarn_cb = ttk.Combobox(filter_frame, textvariable=self.filter_yarn, width=20)
        self.yarn_cb.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Apply Filters", command=self.load_data).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Export to Excel", command=self.export_to_excel).pack(side="right", padx=5)

        columns = ("delivered_to", "yarn_type", "total_kg", "total_rolls")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        self.tree.heading("delivered_to", text="Delivered To")
        self.tree.heading("yarn_type", text="Yarn Type")
        self.tree.heading("total_kg", text="Total (kg)")
        self.tree.heading("total_rolls", text="Total (rolls)")

        self.tree.column("delivered_to", width=200)
        self.tree.column("yarn_type", width=200)
        self.tree.column("total_kg", width=100)
        self.tree.column("total_rolls", width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.bind("<Double-1>", self.on_row_double_click)

    def clear_filters(self):
        self.filter_supplier.set("")
        self.filter_yarn.set("")
        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()

        query = """
            SELECT delivered_to, yarn_type, SUM(qty_kg), SUM(qty_rolls)
            FROM purchases
            WHERE 1=1
        """
        params = []

        if self.filter_supplier.get():
            query += " AND supplier LIKE ?"
            params.append(f"%{self.filter_supplier.get()}%")
        if self.filter_yarn.get():
            query += " AND yarn_type LIKE ?"
            params.append(f"%{self.filter_yarn.get()}%")

        query += " GROUP BY delivered_to, yarn_type ORDER BY delivered_to, yarn_type"

        cur.execute(query, params)
        for delivered_to, yarn_type, total_kg, total_rolls in cur.fetchall():
            self.tree.insert("", "end", values=(
                delivered_to or "", yarn_type or "", total_kg or 0, total_rolls or 0
            ))
        conn.close()

        # Populate filter dropdowns
        self.populate_dropdowns()

    def populate_dropdowns(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT supplier FROM purchases WHERE supplier IS NOT NULL AND supplier != '' ORDER BY supplier")
        self.supplier_cb["values"] = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT DISTINCT yarn_type FROM purchases WHERE yarn_type IS NOT NULL AND yarn_type != '' ORDER BY yarn_type")
        self.yarn_cb["values"] = [row[0] for row in cur.fetchall()]
        conn.close()

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not file_path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Stock Report"

        # Write header
        headers = ["Delivered To", "Yarn Type", "Total (kg)", "Total (rolls)"]
        ws.append(headers)

        # Write data
        for row_id in self.tree.get_children():
            row_data = self.tree.item(row_id)["values"]
            ws.append(row_data)

        wb.save(file_path)

    def on_row_double_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        values = self.tree.item(selected_item[0])["values"]
        delivered_to, yarn_type = values[0], values[1]

        if hasattr(self.controller, "entries_frame"):
            self.controller.entries_frame.prefill_from_dashboard(delivered_to, yarn_type)
            self.controller.notebook.select(self.controller.entries_frame)
