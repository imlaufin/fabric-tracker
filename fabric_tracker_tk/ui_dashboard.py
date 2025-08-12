import tkinter as tk
from tkinter import ttk, messagebox
import db
from datetime import datetime

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

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

        ttk.Button(filter_frame, text="Apply Filters", command=self.load_data).grid(row=0, column=10, padx=5)
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).grid(row=0, column=11, padx=5)

        # ---- Table ----
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

        # Double click / right-click for history
        self.tree.bind("<Double-1>", self.show_history)
        self.tree.bind("<Button-3>", self.show_history)

        self.load_filter_options()
        self.load_data()

    def load_filter_options(self):
        """Populate Holder and Yarn Type filter dropdowns."""
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

        # Date filter
        if self.from_date.get().strip():
            query += " AND date >= ?"
            params.append(self.from_date.get().strip())
        if self.to_date.get().strip():
            query += " AND date <= ?"
            params.append(self.to_date.get().strip())

        # Holder filter
        if self.holder_filter.get().strip():
            query += " AND delivered_to = ?"
            params.append(self.holder_filter.get().strip())

        # Yarn filter
        if self.yarn_filter.get().strip():
            query += " AND yarn_type = ?"
            params.append(self.yarn_filter.get().strip())

        query += " GROUP BY delivered_to, yarn_type ORDER BY delivered_to, yarn_type"
        cur.execute(query, tuple(params))

        search_text = self.search_entry.get().strip().lower()

        for holder, yarn_type, total_kg, total_rolls in cur.fetchall():
            if search_text and (search_text not in str(holder).lower() and search_text not in str(yarn_type).lower()):
                continue

            row_id = self.tree.insert("", "end", values=(
                holder or "Unknown", yarn_type, total_kg or 0, total_rolls or 0
            ))

            # Low stock highlighting
            if (total_kg or 0) < 50:
                self.tree.item(row_id, tags=("low_stock",))

        self.tree.tag_configure("low_stock", background="#ffcccc")

        conn.close()
        self.load_filter_options()

    def show_history(self, event=None):
        """Show full transaction history for selected holder + yarn type."""
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        holder, yarn_type = values[0], values[1]

        hist_win = tk.Toplevel(self)
        hist_win.title(f"Stock History - {holder} / {yarn_type}")
        hist_win.geometry("800x400")

        cols = ("date", "batch_id", "supplier", "yarn_type", "qty_kg", "qty_rolls", "delivered_to")
        hist_tree = ttk.Treeview(hist_win, columns=cols, show="headings")
        headings = ["Date", "Batch ID", "Supplier", "Yarn Type", "Qty (kg)", "Qty (rolls)", "Delivered To"]

        for col, head in zip(cols, headings):
            hist_tree.heading(col, text=head)
            hist_tree.column(col, width=100)

        hist_tree.pack(fill="both", expand=True)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to
            FROM purchases
            WHERE delivered_to=? AND yarn_type=?
            ORDER BY date DESC
        """, (holder, yarn_type))

        for row in cur.fetchall():
            hist_tree.insert("", "end", values=row)

        conn.close()
