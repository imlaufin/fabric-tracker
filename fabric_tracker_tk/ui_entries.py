import tkinter as tk
from tkinter import ttk
import db
from datetime import datetime

class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_dropdown_options()

    def build_ui(self):
        form_frame = ttk.Frame(self)
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="Date:").grid(row=0, column=0, sticky="w")
        self.date_entry = ttk.Entry(form_frame, width=15)
        self.date_entry.grid(row=0, column=1, sticky="w")
        self.date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))

        ttk.Label(form_frame, text="Batch ID:").grid(row=0, column=2, sticky="w")
        self.batch_entry = ttk.Entry(form_frame, width=15)
        self.batch_entry.grid(row=0, column=3, sticky="w")

        ttk.Label(form_frame, text="Supplier:").grid(row=1, column=0, sticky="w")
        self.supplier_cb = ttk.Combobox(form_frame, width=20)
        self.supplier_cb.grid(row=1, column=1, sticky="w")

        ttk.Label(form_frame, text="Yarn Type:").grid(row=1, column=2, sticky="w")
        self.yarn_cb = ttk.Combobox(form_frame, width=20)
        self.yarn_cb.grid(row=1, column=3, sticky="w")

        ttk.Label(form_frame, text="Qty (kg):").grid(row=2, column=0, sticky="w")
        self.qty_kg_entry = ttk.Entry(form_frame, width=15)
        self.qty_kg_entry.grid(row=2, column=1, sticky="w")

        ttk.Label(form_frame, text="Qty (rolls):").grid(row=2, column=2, sticky="w")
        self.qty_rolls_entry = ttk.Entry(form_frame, width=15)
        self.qty_rolls_entry.grid(row=2, column=3, sticky="w")

        ttk.Label(form_frame, text="Delivered To:").grid(row=3, column=0, sticky="w")
        self.delivered_to_cb = ttk.Combobox(form_frame, width=20)
        self.delivered_to_cb.grid(row=3, column=1, sticky="w")

        save_btn = ttk.Button(form_frame, text="Save Entry", command=self.save_entry)
        save_btn.grid(row=4, column=0, columnspan=4, pady=10)

        # Table of entries
        self.tree = ttk.Treeview(self, columns=("date", "batch", "supplier", "yarn", "kg", "rolls", "delivered"),
                                 show="headings")
        self.tree.heading("date", text="Date")
        self.tree.heading("batch", text="Batch ID")
        self.tree.heading("supplier", text="Supplier")
        self.tree.heading("yarn", text="Yarn Type")
        self.tree.heading("kg", text="Qty (kg)")
        self.tree.heading("rolls", text="Qty (rolls)")
        self.tree.heading("delivered", text="Delivered To")

        self.tree.column("date", width=100)
        self.tree.column("batch", width=100)
        self.tree.column("supplier", width=150)
        self.tree.column("yarn", width=150)
        self.tree.column("kg", width=80)
        self.tree.column("rolls", width=80)
        self.tree.column("delivered", width=150)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_entries()

    def load_dropdown_options(self):
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT supplier FROM purchases WHERE supplier IS NOT NULL AND supplier != '' ORDER BY supplier")
        suppliers = [row[0] for row in cur.fetchall()]
        self.supplier_cb["values"] = suppliers

        cur.execute("SELECT DISTINCT yarn_type FROM purchases WHERE yarn_type IS NOT NULL AND yarn_type != '' ORDER BY yarn_type")
        yarns = [row[0] for row in cur.fetchall()]
        self.yarn_cb["values"] = yarns

        cur.execute("SELECT DISTINCT delivered_to FROM purchases WHERE delivered_to IS NOT NULL AND delivered_to != '' ORDER BY delivered_to")
        holders = [row[0] for row in cur.fetchall()]
        self.delivered_to_cb["values"] = holders

        conn.close()

    def load_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to FROM purchases ORDER BY date DESC")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def save_entry(self):
        date = self.date_entry.get().strip()
        batch_id = self.batch_entry.get().strip()
        supplier = self.supplier_cb.get().strip()
        yarn_type = self.yarn_cb.get().strip()
        qty_kg = self.qty_kg_entry.get().strip()
        qty_rolls = self.qty_rolls_entry.get().strip()
        delivered_to = self.delivered_to_cb.get().strip()

        if not date or not supplier or not yarn_type or not qty_kg or not delivered_to:
            return  # could show an error message

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO purchases (date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to))
        conn.commit()
        conn.close()

        self.load_entries()
        self.load_dropdown_options()

        self.qty_kg_entry.delete(0, tk.END)
        self.qty_rolls_entry.delete(0, tk.END)
        self.batch_entry.delete(0, tk.END)

    def prefill_from_dashboard(self, delivered_to, yarn_type):
        """Called by Dashboard double-click to prefill fields."""
        self.delivered_to_cb.set(delivered_to)
        self.yarn_cb.set(yarn_type)
        self.qty_kg_entry.focus()
