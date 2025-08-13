# ui_dashboard.py
import tkinter as tk
from tkinter import ttk
import db
from datetime import datetime

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.reload_all()

    def build_ui(self):
        # Top summary frame
        summary_frame = ttk.Frame(self)
        summary_frame.pack(fill="x", padx=6, pady=6)

        self.total_purchases_label = ttk.Label(summary_frame, text="Total Purchases: 0", font=("Arial", 12))
        self.total_purchases_label.pack(side="left", padx=6)
        self.total_yarn_kg_label = ttk.Label(summary_frame, text="Total Yarn (kg): 0", font=("Arial", 12))
        self.total_yarn_kg_label.pack(side="left", padx=6)
        self.total_batches_label = ttk.Label(summary_frame, text="Total Batches: 0", font=("Arial", 12))
        self.total_batches_label.pack(side="left", padx=6)

        # Date filter
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=6, pady=6)
        ttk.Label(filter_frame, text="From (dd/mm/yyyy):").pack(side="left")
        self.from_entry = ttk.Entry(filter_frame, width=12)
        self.from_entry.pack(side="left", padx=4)
        ttk.Label(filter_frame, text="To (dd/mm/yyyy):").pack(side="left")
        self.to_entry = ttk.Entry(filter_frame, width=12)
        self.to_entry.pack(side="left", padx=4)
        ttk.Button(filter_frame, text="Apply Filter", command=self.reload_all).pack(side="left", padx=6)

        # Purchase summary table
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=6, pady=6)
        cols = ("date", "batch_id", "lot_no", "supplier", "yarn_type", "qty_kg", "qty_rolls", "delivered_to")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        for col, width, heading in zip(cols, [100,100,80,150,120,100,100,150], ["Date","Batch","Lot","Supplier","Yarn Type","Kg","Rolls","Delivered To"]):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)
        self.tree.pack(fill="both", expand=True)

    def reload_all(self):
        # clear tree
        for r in self.tree.get_children():
            self.tree.delete(r)

        from_date = self.from_entry.get().strip()
        to_date = self.to_entry.get().strip()
        try:
            from_db = db.ui_to_db_date(from_date) if from_date else None
            to_db = db.ui_to_db_date(to_date) if to_date else None
        except Exception:
            from_db = to_db = None

        conn = db.get_connection()
        cur = conn.cursor()
        sql = "SELECT date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to FROM purchases"
        params = ()
        if from_db and to_db:
            sql += " WHERE date BETWEEN ? AND ?"
            params = (from_db, to_db)
        sql += " ORDER BY date DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()

        total_purchases = 0
        total_kg = 0
        batch_set = set()

        for r in rows:
            display_date = r["date"]
            try:
                display_date = db.db_to_ui_date(r["date"])
            except:
                pass
            self.tree.insert("", "end", values=(display_date, r["batch_id"], r["lot_no"], r["supplier"], r["yarn_type"], r["qty_kg"], r["qty_rolls"], r["delivered_to"]))
            total_purchases += 1
            total_kg += r["qty_kg"] or 0
            batch_set.add(r["batch_id"])

        self.total_purchases_label.config(text=f"Total Purchases: {total_purchases}")
        self.total_yarn_kg_label.config(text=f"Total Yarn (kg): {total_kg}")
        self.total_batches_label.config(text=f"Total Batches: {len(batch_set)}")
        conn.close()
