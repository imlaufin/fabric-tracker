# ui_sales.py
import tkinter as tk
from tkinter import ttk, messagebox
from fabric_tracker_tk.db import Database

class SalesUI:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        self.frame = ttk.Frame(master)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(self.frame, text="Sales", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")

        # Table
        self.tree = ttk.Treeview(
            self.frame,
            columns=("id", "customer", "item", "quantity", "price", "date"),
            show="headings"
        )
        for col, text in zip(
            ("id", "customer", "item", "quantity", "price", "date"),
            ("ID", "Customer", "Item", "Quantity", "Price", "Date")
        ):
            self.tree.heading(col, text=text)
        self.tree.grid(row=1, column=0, columnspan=4, sticky="nsew")

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

        # Form
        ttk.Label(self.frame, text="Customer:").grid(row=2, column=0, sticky="w")
        self.customer_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.customer_var).grid(row=2, column=1, sticky="ew")

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
        ttk.Button(self.frame, text="Add", command=self.add_sale).grid(row=7, column=0, pady=5)
        ttk.Button(self.frame, text="Update", command=self.update_sale).grid(row=7, column=1, pady=5)
        ttk.Button(self.frame, text="Delete", command=self.delete_sale).grid(row=7, column=2, pady=5)

        self.load_sales()
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_sales(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self.db.fetch_sales()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def add_sale(self):
        customer = self.customer_var.get().strip()
        item = self.item_var.get().strip()
        quantity = self.quantity_var.get().strip()
        price = self.price_var.get().strip()
        date = self.date_var.get().strip()

        if not customer or not item:
            messagebox.showerror("Error", "Customer and item are required")
            return
        try:
            qty = float(quantity)
            prc = float(price)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Price must be numeric")
            return

        self.db.insert_sale(customer, item, qty, prc, date)
        self.load_sales()
        self.clear_form()

    def update_sale(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a sale to update")
            return

        sale_id = self.tree.item(selected)["values"][0]
        customer = self.customer_var.get().strip()
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

        self.db.update_sale(sale_id, customer, item, qty, prc, date)
        self.load_sales()
        self.clear_form()

    def delete_sale(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a sale to delete")
            return

        sale_id = self.tree.item(selected)["values"][0]
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this sale?")
        if confirm:
            self.db.delete_sale(sale_id)
            self.load_sales()
            self.clear_form()

    def clear_form(self):
        self.customer_var.set("")
        self.item_var.set("")
        self.quantity_var.set("")
        self.price_var.set("")
        self.date_var.set("")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected)["values"]
        self.customer_var.set(values[1])
        self.item_var.set(values[2])
        self.quantity_var.set(values[3])
        self.price_var.set(values[4])
        self.date_var.set(values[5])
