import tkinter as tk
from tkinter import ttk, messagebox
import db
import datetime

class EntryScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Form Labels and Inputs
        ttk.Label(self, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = ttk.Entry(self)
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Batch ID:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.batch_id_entry = ttk.Entry(self)
        self.batch_id_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self, text="Supplier:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.supplier_combo = ttk.Combobox(self, values=self.get_suppliers())
        self.supplier_combo.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self, text="Yarn Type:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.yarn_combo = ttk.Combobox(self, values=self.get_yarn_types())
        self.yarn_combo.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(self, text="Qty (kg):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.qty_kg_entry = ttk.Entry(self)
        self.qty_kg_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(self, text="Qty (rolls):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.qty_rolls_entry = ttk.Entry(self)
        self.qty_rolls_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(self, text="Delivered To:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.delivered_to_entry = ttk.Entry(self)
        self.delivered_to_entry.grid(row=6, column=1, padx=5, pady=5)

        # Buttons
        ttk.Button(self, text="Save", command=self.save_record).grid(row=7, column=0, padx=5, pady=10)
        ttk.Button(self, text="Clear", command=self.clear_form).grid(row=7, column=1, padx=5, pady=10)

    def get_suppliers(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        values = [row[0] for row in cur.fetchall()]
        conn.close()
        return values

    def get_yarn_types(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM yarn_types ORDER BY name")
        values = [row[0] for row in cur.fetchall()]
        conn.close()
        return values

    def save_record(self):
        try:
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO purchases (date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.date_entry.get(),
                self.batch_id_entry.get(),
                self.supplier_combo.get(),
                self.yarn_combo.get(),
                float(self.qty_kg_entry.get() or 0),
                int(self.qty_rolls_entry.get() or 0),
                self.delivered_to_entry.get()
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Purchase record saved.")
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.batch_id_entry.delete(0, tk.END)
        self.supplier_combo.set("")
        self.yarn_combo.set("")
        self.qty_kg_entry.delete(0, tk.END)
        self.qty_rolls_entry.delete(0, tk.END)
        self.delivered_to_entry.delete(0, tk.END)
