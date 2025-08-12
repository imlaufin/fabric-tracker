import tkinter as tk
from tkinter import ttk, filedialog
import db
import pandas as pd

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.sort_column = None
        self.sort_reverse = False
        self.build_ui()
        self.filter_state = {}  # For persistent filters

    def build_ui(self):
        # ---- Filter Frame ----
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(filter_frame, text="From Date:").grid(row=0, column=0, padx=2)
        self.from_date = ttk.Entry(filter_frame, width=12)
        self.from_date.grid(row=0, column=1, padx=2)

        ttk.Label(filter_frame, text="To Date:").grid(row=0, column=2, padx=2)
        self.to_date = ttk.Entry(filter_frame, width=12)
        self.to_date.grid(row=0, column=3, padx=2)

        ttk.Label(filter_frame, text="Holder:").grid(row=0, column=4, padx=2)
        self.holder_filter = ttk.Combobox(filter_frame, width=20)
        self.holder_filter.grid(row=0, column=5, padx=2)

        ttk.Label(filter_frame, text="Yarn Type:").grid(row=0, column=6, padx=2)
        self.yarn_filter = ttk.Combobox(filter_frame, width=20)
        self.yarn_filter.grid(row=0, column=7, padx=2)

        ttk.Label(filter_frame, text="Search:").grid(row=0, column=8, padx=2)
        self.search_entry = ttk.Entry(filter_frame, width=20)
        self.search_entry.grid(row=0, column=9, padx=2)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_data())

        ttk.Button(filter_frame, text="Apply Filters", command=self.load_data).grid(row=0, column=10, padx=5)
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).grid(row=0, column=11, padx=5)
        ttk.Button(filter_frame, text="Export to Excel", command=self.export_to_excel).grid(row=0, column=12, padx=5)

        # ---- Main Table ----
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(5,0))

        columns = ("holder", "yarn_type", "total_kg", "total_rolls")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        self.tree.heading("holder", text="Holder", command=lambda: self.sort_by_column("holder"))
        self.tree.heading("yarn_type", text="Yarn Type", command=lambda: self.sort_by_column("yarn_type"))
        self.tree.heading("total_kg", text="Total (kg)", command=lambda: self.sort_by_column("total_kg"))
        self.tree.heading("total_rolls", text="Total (rolls)", command=lambda: self.sort_by_column("total_rolls"))

        for col, w in zip(columns, [150, 150, 100, 100]):
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # ---- Totals Row (Fixed) ----
        totals_frame = ttk.Frame(self)
        totals_frame.pack(fill="x", padx=10, pady=(0,5))

        self.totals_tree = ttk.Treeview(totals_frame, columns=columns, show="headings", height=1)
        for col, text, w in zip(columns, ["Holder", "Yarn Type", "Total (kg)", "Total (rolls)"], [150, 150, 100, 100]):
            self.totals_tree.heading(col, text=text)
            self.totals_tree.column(col, width=w)

        self.totals_tree.grid(row=0, column=0, sticky="ew")
        self.totals_tree.tag_configure("total_row", background="#e6ffe6", font=("Arial", 10, "bold"))

        # Sync column widths between main & totals
        self.tree.bind("<Configure>", self.sync_column_widths)

        # Double click → fill Entries tab
        self.tree.bind("<Double-1>", self.send_to_entries)

        self.load_filter_options()
        self.load_data()

    def sync_column_widths(self, event=None):
        for i, col in enumerate(self.tree["columns"]):
            width = self.tree.column(col)["width"]
            self.totals_tree.column(col, width=width)

    def sort_by_column(self, col):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        self.load_data()

    def load_filter_options(self):
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT delivered_to FROM purchases WHERE delivered_to IS NOT NULL AND delivered_to != '' ORDER BY delivered_to")
        holders = [row[0] for row in cur.fetchall()]
        self.holder_filter["values"] = [""] + holders

        cur.execute("SELECT DISTINCT yarn_type FROM purchases WHERE yarn_type IS NOT NULL AND yarn_type != '' ORDER BY yarn_type")
        yarn_types = [row[0] for row in cur.fetchall()]
        self.yarn_filter["values"] = [""] + yarn_types

        conn.close()

    def clear_filters(self):
        self.from_date.delete(0, tk.END)
        self.to_date.delete(0, tk.END)
        self.holder_filter.set("")
        self.yarn_filter.set("")
        self.search_entry.delete(0, tk.END)
        self.load_data()

    def export_to_excel(self):
        data = [self.tree.item(row)["values"] for row in self.tree.get_children()]
        df = pd.DataFrame(data, columns=["Holder", "Yarn Type", "Total (kg)", "Total (rolls)"])
        if df.empty:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel Files", "*.xlsx")],
                                                 title="Save Excel File")
        if file_path:
            df.to_excel(file_path, index=False)

    def load_data(self):
        # Save filter state
        self.filter_state = {
            "from": self.from_date.get(),
            "to": self.to_date.get(),
            "holder": self.holder_filter.get(),
            "yarn": self.yarn_filter.get(),
            "search": self.search_entry.get()
        }

        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.totals_tree.get_children():
            self.totals_tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()

        query = """
            SELECT delivered_to, yarn_type, SUM(qty_kg), SUM(qty_rolls)
            FROM purchases
            WHERE 1=1
        """
        params = []

        if self.filter_state["from"].strip():
            query += " AND date >= ?"
            params.append(self.filter_state["from"])
        if self.filter_state["to"].strip():
            query += " AND date <= ?"
            params.append(self.filter_state["to"])
        if self.filter_state["holder"].strip():
            query += " AND delivered_to = ?"
            params.append(self.filter_state["holder"])
        if self.filter_state["yarn"].strip():
            query += " AND yarn_type = ?"
            params.append(self.filter_state["yarn"])

        query += " GROUP BY delivered_to, yarn_type"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        # Apply search filter
        search_text = self.filter_state["search"].strip().lower()
        rows = [r for r in rows if not search_text or
                search_text in str(r[0]).lower() or search_text in str(r[1]).lower()]

        # Sorting
        if self.sort_column:
            col_index = {"holder": 0, "yarn_type": 1, "total_kg": 2, "total_rolls": 3}[self.sort_column]
            rows.sort(key=lambda x: x[col_index] or 0, reverse=self.sort_reverse)

        total_kg_sum = 0
        total_rolls_sum = 0

        for holder, yarn_type, total_kg, total_rolls in rows:
            total_kg_sum += total_kg or 0
            total_rolls_sum += total_rolls or 0

            row_id = self.tree.insert("", "end", values=(holder or "Unknown", yarn_type, total_kg or 0, total_rolls or 0))
            if (total_kg or 0) < 50:
                self.tree.item(row_id, tags=("low_stock",))

        self.tree.tag_configure("low_stock", background="#ffcccc")

        self.totals_tree.insert("", "end", values=("TOTAL", "", round(total_kg_sum, 2), total_rolls_sum),
                                tags=("total_row",))
        self.totals_tree.tag_configure("total_row", background="#e6ffe6", font=("Arial", 10, "bold"))

        conn.close()
        self.load_filter_options()
        self.sync_column_widths()

    def send_to_entries(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if hasattr(self.controller, "entries_frame"):
            self.controller.entries_frame.prefill_from_dashboard(values[0], values[1])
            self.controller.notebook.select(self.controller.entries_frame)
