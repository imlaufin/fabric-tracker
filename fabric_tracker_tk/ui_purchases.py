# ui_purchases.py
import tkinter as tk
from tkinter import ttk, messagebox
from db import Database

class PurchasesUI:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        self.frame = ttk.Frame(master)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(self.frame, text="Purchases", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")

        # Table
        self.tree = ttk.Treeview(
            self.frame,
            columns=("id", "supplier", "item", "quantity", "price", "date"),
            show="headings"
        )
        for col, text in zip(
            ("id", "supplier", "item", "quantity", "price", "date"),
            ("ID", "Supplier", "Item", "Quantity", "Price", "Date")
        ):
            self.tree.heading(col, text=text)
        self.tree.grid(row=1, column=0, columnspan=4, sticky="nsew")

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

        # Form
        ttk.Label(self.frame, text="Supplier:").grid(row=2, column=0, sticky="w")
        self.supplier_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.supplier_var).grid(row=2, column=1, sticky="ew")

        ttk.Label(self.frame, text="Item:").grid(row=3, column=0, sticky="w")
        self.item_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.item_var).grid(row=3, column=1, sticky="ew")

        ttk.Label(self.frame, text="Quantity:").grid(row=4, column=0, sticky="w")
        self.quantity_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.quantity_var).grid(row=4, column=1, sticky="ew")

        ttk.Label(self.frame, text="Price:").grid(row=5, column=0, sticky="w")
        self.price_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.price_var).grid(row=5, column=1, sticky="ew")

        ttk.Label(self.frame, text="Date:").grid(row=6, column=0, sticky="w")
        self.date_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.date_var).grid(row=6, column=1, sticky="ew")

        # Buttons
        ttk.Button(self.frame, text="Add", command=self.add_purchase).grid(row=7, column=0, pady=5)
        ttk.Button(self.frame, text="Update", command=self.update_purchase).grid(row=7, column=1, pady=5)
        ttk.Button(self.frame, text="Delete", command=self.delete_purchase).grid(row=7, column=2, pady=5)

        self.load_purchases()
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_purchases(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self.db.fetch_purchases()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def add_purchase(self):
        supplier = self.supplier_var.get().strip()
        item = self.item_var.get().strip()
        quantity = self.quantity_var.get().strip()
        price = self.price_var.get().strip()
        date = self.date_var.get().strip()

        if not supplier or not item:
            messagebox.showerror("Error", "Supplier and item are required")
            return
        try:
            qty = float(quantity)
            prc = float(price)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Price must be numeric")
            return

        self.db.insert_purchase(supplier, item, qty, prc, date)
        self.load_purchases()
        self.clear_form()

    def update_purchase(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a purchase to update")
            return

        item_data = self.tree.item(selected)["values"]
        purchase_id = item_data[0]

        supplier = self.supplier_var.get().strip()
        item = self.item_var.get().strip()
        quantity = self.quantity_var.get().strip()
        price = self.price_var.get().strip()
        date = self.date_var.get().strip()

        try:
            qty = float(quantity)
            prc = float(price)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Price must be numeric")
            return

        self.db.update_purchase(purchase_id, supplier, item, qty, prc, date)
        self.load_purchases()
        self.clear_form()

    def delete_purchase(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a purchase to delete")
            return

        purchase_id = self.tree.item(selected)["values"][0]
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this purchase?")
        if confirm:
            self.db.delete_purchase(purchase_id)
            self.load_purchases()
            self.clear_form()

    def clear_form(self):
        self.supplier_var.set("")
        self.item_var.set("")
        self.quantity_var.set("")
        self.price_var.set("")
        self.date_var.set("")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected)["values"]
        self.supplier_var.set(values[1])
        self.item_var.set(values[2])
        self.quantity_var.set(values[3])
        self.price_var.set(values[4])
        self.date_var.set(values[5])
