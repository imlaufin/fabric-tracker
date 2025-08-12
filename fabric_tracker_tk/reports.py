import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import db
import openpyxl


class ReportsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_filters()

    def build_ui(self):
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Financial year dropdown
        ttk.Label(filter_frame, text="Financial Year:").pack(side="left")
        self.year_filter = ttk.Combobox(filter_frame, state="readonly", width=12)
        self.year_filter.pack(side="left", padx=5)

        # Manual date range
        ttk.Label(filter_frame, text="From:").pack(side="left", padx=(10, 0))
        self.from_date_var = tk.StringVar()
        self.from_date_entry = ttk.Entry(filter_frame, textvariable=self.from_date_var, width=12)
        self.from_date_entry.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="To:").pack(side="left", padx=(10, 0))
        self.to_date_var = tk.StringVar()
        self.to_date_entry = ttk.Entry(filter_frame, textvariable=self.to_date_var, width=12)
        self.to_date_entry.pack(side="left", padx=5)

        # Supplier filter
        ttk.Label(filter_frame, text="Supplier:").pack(side="left", padx=(10, 0))
        self.supplier_filter = ttk.Combobox(filter_frame, state="readonly", width=18)
        self.supplier_filter.pack(side="left", padx=5)

        # Delivered To filter
        ttk.Label(filter_frame, text="Delivered To:").pack(side="left", padx=(10, 0))
        self.delivered_filter = ttk.Combobox(filter_frame, state="readonly", width=18)
        self.delivered_filter.pack(side="left", padx=5)

        # Yarn Type filter
        ttk.Label(filter_frame, text="Yarn Type:").pack(side="left", padx=(10, 0))
        self.yarn_filter = ttk.Combobox(filter_frame, state="readonly", width=15)
        self.yarn_filter.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Apply Filters", command=self.load_data).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Export to Excel", command=self.export_to_excel).pack(side="right", padx=5)

        # Table
        columns = ("date", "supplier", "delivered_to", "yarn_type", "qty_kg", "qty_rolls", "net_balance")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("date", text="Date")
        self.tree.heading("supplier", text="Supplier")
        self.tree.heading("delivered_to", text="Delivered To")
        self.tree.heading("yarn_type", text="Yarn Type")
        self.tree.heading("qty_kg", text="Qty (kg)")
        self.tree.heading("qty_rolls", text="Qty (rolls)")
        self.tree.heading("net_balance", text="Net Balance (kg)")

        for col, w in zip(columns, [90, 150, 150, 150, 80, 90, 120]):
            self.tree.column(col, width=w)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.total_label = ttk.Label(self, text="", font=("Arial", 10, "bold"))
        self.total_label.pack(side="bottom", pady=5)

    def load_filters(self):
        # Populate years from data
        conn = db.get_connection()
        years = set()
        for row in conn.execute("SELECT date FROM purchases"):
            try:
                y = int(row["date"][:4])
                years.add(y)
            except:
                pass
        conn.close()

        fy_list = []
        for y in sorted(years):
            fy_list.append(f"{y}-{y+1}")
        self.year_filter["values"] = fy_list

        suppliers = [s["name"] for s in db.list_suppliers()]
        yarn_types = db.list_yarn_types()

        self.supplier_filter["values"] = [""] + suppliers
        self.delivered_filter["values"] = [""] + suppliers
        self.yarn_filter["values"] = [""] + yarn_types

    def clear_filters(self):
        self.year_filter.set("")
        self.from_date_var.set("")
        self.to_date_var.set("")
        self.supplier_filter.set("")
        self.delivered_filter.set("")
        self.yarn_filter.set("")
        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Determine date range
        from_date, to_date = None, None
        if self.from_date_var.get() and self.to_date_var.get():
            try:
                from_date = db.ui_to_db_date(self.from_date_var.get())
                to_date = db.ui_to_db_date(self.to_date_var.get())
            except:
                messagebox.showerror("Invalid Date", "Please use dd/mm/yyyy format for dates.")
                return
        elif self.year_filter.get():
            try:
                fy_start = int(self.year_filter.get().split("-")[0])
                from_date = f"{fy_start}-04-01"
                to_date = f"{fy_start+1}-03-31"
            except:
                pass

        # Build query
        query = """
            SELECT date, supplier, delivered_to, yarn_type, qty_kg, qty_rolls
            FROM purchases
        """
        params = []
        conditions = []

        if from_date and to_date:
            conditions.append("date BETWEEN ? AND ?")
            params.extend([from_date, to_date])

        if self.supplier_filter.get().strip():
            conditions.append("supplier = ?")
            params.append(self.supplier_filter.get().strip())

        if self.delivered_filter.get().strip():
            conditions.append("delivered_to = ?")
            params.append(self.delivered_filter.get().strip())

        if self.yarn_filter.get().strip():
            conditions.append("yarn_type = ?")
            params.append(self.yarn_filter.get().strip())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date ASC"

        conn = db.get_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()

        # Calculate net balance per Delivered To + Yarn Type
        balance_map = {}
        total_kg_sum = total_rolls_sum = 0

        for r in rows:
            key = (r["delivered_to"], r["yarn_type"])
            prev_balance = balance_map.get(key, 0)
            new_balance = prev_balance + (r["qty_kg"] or 0)
            balance_map[key] = new_balance

            self.tree.insert("", "end", values=(
                db.db_to_ui_date(r["date"]),
                r["supplier"],
                r["delivered_to"],
                r["yarn_type"],
                r["qty_kg"] or 0,
                r["qty_rolls"] or 0,
                new_balance
            ))

            total_kg_sum += r["qty_kg"] or 0
            total_rolls_sum += r["qty_rolls"] or 0

        self.total_label.config(text=f"TOTAL: {total_kg_sum} kg, {total_rolls_sum} rolls")

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"

        # Header
        ws.append(["Date", "Supplier", "Delivered To", "Yarn Type", "Qty (kg)", "Qty (rolls)", "Net Balance (kg)"])

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
