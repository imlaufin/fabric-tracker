import tkinter as tk
from tkinter import ttk, messagebox
import db

class MastersFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Suppliers Section
        suppliers_frame = ttk.LabelFrame(self, text="Suppliers")
        suppliers_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.supplier_entry = ttk.Entry(suppliers_frame)
        self.supplier_entry.pack(side="left", padx=5, pady=5)
        ttk.Button(suppliers_frame, text="Add Supplier", command=self.add_supplier).pack(side="left", padx=5, pady=5)

        self.suppliers_tree = ttk.Treeview(suppliers_frame, columns=("name",), show="headings", height=5)
        self.suppliers_tree.heading("name", text="Supplier Name")
        self.suppliers_tree.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(suppliers_frame, text="Delete Selected", command=self.delete_supplier).pack(pady=5)

        # Yarn Types Section
        yarn_frame = ttk.LabelFrame(self, text="Yarn Types")
        yarn_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.yarn_entry = ttk.Entry(yarn_frame)
        self.yarn_entry.pack(side="left", padx=5, pady=5)
        ttk.Button(yarn_frame, text="Add Yarn Type", command=self.add_yarn_type).pack(side="left", padx=5, pady=5)

        self.yarn_tree = ttk.Treeview(yarn_frame, columns=("name",), show="headings", height=5)
        self.yarn_tree.heading("name", text="Yarn Type Name")
        self.yarn_tree.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(yarn_frame, text="Delete Selected", command=self.delete_yarn_type).pack(pady=5)

        # Load data initially
        self.load_suppliers()
        self.load_yarn_types()

    # -------- Suppliers --------
    def load_suppliers(self):
        for row in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        for (name,) in cur.fetchall():
            self.suppliers_tree.insert("", "end", values=(name,))
        conn.close()

    def add_supplier(self):
        name = self.supplier_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Supplier name cannot be empty.")
            return
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO suppliers (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        self.supplier_entry.delete(0, tk.END)
        self.load_suppliers()

    def delete_supplier(self):
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a supplier to delete.")
            return
        name = self.suppliers_tree.item(selected[0], "values")[0]
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE name=?", (name,))
        conn.commit()
        conn.close()
        self.load_suppliers()

    # -------- Yarn Types --------
    def load_yarn_types(self):
        for row in self.yarn_tree.get_children():
            self.yarn_tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM yarn_types ORDER BY name")
        for (name,) in cur.fetchall():
            self.yarn_tree.insert("", "end", values=(name,))
        conn.close()

    def add_yarn_type(self):
        name = self.yarn_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Yarn type cannot be empty.")
            return
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO yarn_types (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        self.yarn_entry.delete(0, tk.END)
        self.load_yarn_types()

    def delete_yarn_type(self):
        selected = self.yarn_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a yarn type to delete.")
            return
        name = self.yarn_tree.item(selected[0], "values")[0]
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM yarn_types WHERE name=?", (name,))
        conn.commit()
        conn.close()
        self.load_yarn_types()
