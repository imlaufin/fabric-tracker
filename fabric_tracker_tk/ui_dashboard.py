import tkinter as tk
from tkinter import ttk
import sqlite3
from fabric_tracker_tk import db
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

        # Fabricator filter
        self.fabricator_var = tk.StringVar()
        fabricators = [f["name"] for f in db.get_fabricators("knitting_unit")] + [f["name"] for f in db.get_fabricators("dyeing_unit")]
        fabricators.insert(0, "")  # Empty option for all
        ttk.Label(summary_frame, text="Fabricator:").pack(side="left", padx=6)
        ttk.OptionMenu(summary_frame, self.fabricator_var, "", *fabricators, command=lambda x: self.reload_all()).pack(side="left", padx=4)

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
        cols = ("date", "batch_id", "lot_no", "supplier", "yarn_type", "qty_kg", "qty_rolls", "delivered_to", "status", "shortage_kg", "net_price")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        for col, width, heading in zip(cols, [100, 100, 80, 150, 120, 100, 100, 150, 100, 100, 100], 
                                      ["Date", "Batch", "Lot", "Supplier", "Yarn Type", "Kg", "Rolls", "Delivered To", "Status", "Shortage (kg)", "Net Price"]):
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
        except ValueError as e:
            tk.messagebox.showerror("Invalid Date", f"Invalid date format: {e}")
            return

        with db.get_connection() as conn:
            cur = conn.cursor()
            sql = """
                SELECT p.date, p.batch_id, p.lot_no, p.supplier, p.yarn_type, p.qty_kg, p.qty_rolls, p.delivered_to,
                       b.status AS batch_status,
                       COALESCE(SUM(d.returned_qty_kg), 0) AS returned_kg,
                       db.calculate_net_price(p.batch_id) AS net_price
                FROM purchases p
                LEFT JOIN batches b ON b.batch_ref = p.batch_id
                LEFT JOIN lots l ON l.lot_no = p.lot_no
                LEFT JOIN dyeing_outputs d ON d.lot_id = l.id
                GROUP BY p.id
            """
            params = ()
            fabricator = self.fabricator_var.get()
            if from_db and to_db:
                sql += " WHERE p.date BETWEEN ? AND ?"
                params = (from_db, to_db)
            if fabricator:
                sql += " WHERE p.delivered_to = ?" if not params else " AND p.delivered_to = ?"
                params += (fabricator,)
            sql += " ORDER BY p.date DESC"
            try:
                cur.execute(sql, params)
                rows = cur.fetchall()
            except sqlite3.Error as e:
                tk.messagebox.showerror("Database Error", f"Failed to load data: {e}")
                return

            total_purchases = 0
            total_kg = 0
            batch_set = set()
            fabricator_balances = {}  # Track kg by fabricator

            for r in rows:
                display_date = r["date"]
                try:
                    display_date = db.db_to_ui_date(r["date"])
                except:
                    pass
                status = r["batch_status"] or "Ordered"
                returned_kg = r["returned_kg"] or 0
                shortage_kg = max(0, r["qty_kg"] - returned_kg)  # Simple shortage calculation
                net_price = r["net_price"] or 0

                self.tree.insert("", "end", values=(display_date, r["batch_id"], r["lot_no"], r["supplier"], 
                                                  r["yarn_type"], r["qty_kg"], r["qty_rolls"], r["delivered_to"],
                                                  status, round(shortage_kg, 2), round(net_price, 2)))
                total_purchases += 1
                total_kg += r["qty_kg"] or 0
                batch_set.add(r["batch_id"])
                fabricator_balances[r["delivered_to"]] = fabricator_balances.get(r["delivered_to"], 0) + (r["qty_kg"] or 0)

            self.total_purchases_label.config(text=f"Total Purchases: {total_purchases}")
            self.total_yarn_kg_label.config(text=f"Total Yarn (kg): {total_kg}")
            self.total_batches_label.config(text=f"Total Batches: {len(batch_set)}")

            # Update fabricator-specific balances (simplified display for now)
            for fab, kg in fabricator_balances.items():
                print(f"Fabricator {fab}: {kg} kg")  # Placeholder; consider a dedicated UI element
