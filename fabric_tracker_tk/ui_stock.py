# ui_stock.py
import tkinter as tk
from tkinter import ttk, messagebox
from db import Database

class StockUI:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        self.frame = ttk.Frame(master)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(self.frame, text="Stock", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")

        # Table
        self.tree = ttk.Treeview(
            self.frame,
            columns=("id", "item", "quantity", "unit", "location"),
            show="headings"
        )
        for col, text in zip(
            ("id", "item", "quantity", "unit", "location"),
            ("ID", "Item", "Quantity", "Unit", "Location")
        ):
            self.tree.heading(col, text=text)
        self.tree.grid(row=1, column=0, columnspan=4, sticky="nsew")

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

        # Form
        ttk.Label(self.frame, text="Item:").grid(row=2, column=0, sticky="w")
        self.item_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.item_var).grid(row=2, column=1, sticky="ew")

        ttk.Label(self.frame, text="Quantity:").grid(row=3, column=0, sticky="w")
        self.quantity_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.quantity_var).grid(row=3, column=1, sticky="ew")

        ttk.Label(self.frame, text="Unit:").grid(row=4, column=0, sticky="w")
        self.unit_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.unit_var).grid(row=4, column=1, sticky="ew")

        ttk.Label(self.frame, text="Location:").grid(row=5, column=0, sticky="w")
        self.location_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.location_var).grid(row=5, column=1, sticky="ew")

        # Buttons
        ttk.Button(self.frame, text="Add", command=self.add_stock).grid(row=6, column=0, pady=5)
        ttk.Button(self.frame, text="Update", command=self.update_stock).grid(row=6, column=1, pady=5)
        ttk.Button(self.frame, text="Delete", command=self.delete_stock).grid(row=6, column=2, pady=5)

        self.load_stock()
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_stock(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self.db.fetch_stock()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def add_stock(self):
        item = self.item_var.get().strip()
        quantity = self.quantity_var.get().strip()
        unit = self.unit_var.get().strip()
        location = self.location_var.get().strip()

        if not item:
            messagebox.showerror("Error", "Item is required")
            return
        try:
            qty = float(quantity)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be numeric")
            return

        self.db.insert_stock(item, qty, unit, location)
        self.load_stock()
        self.clear_form()

    def update_stock(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a stock record to update")
            return

        stock_id = self.tree.item(selected)["values"][0]
        item = self.item_var.get().strip()
        quantity = self.quantity_var.get().strip()
        unit = self.unit_var.get().strip()
        location = self.location_var.get().strip()

        try:
            qty = float(quantity)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be numeric")
            return

        self.db.update_stock(stock_id, item, qty, unit, location)
        self.load_stock()
        self.clear_form()

    def delete_stock(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a stock record to delete")
            return

        stock_id = self.tree.item(selected)["values"][0]
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this record?")
        if confirm:
            self.db.delete_stock(stock_id)
            self.load_stock()
            self.clear_form()

    def clear_form(self):
        self.item_var.set("")
        self.quantity_var.set("")
        self.unit_var.set("")
        self.location_var.set("")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected)["values"]
        self.item_var.set(values[1])
        self.quantity_var.set(values[2])
        self.unit_var.set(values[3])
        self.location_var.set(values[4])
