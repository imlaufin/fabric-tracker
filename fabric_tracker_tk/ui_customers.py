# ui_customers.py
import tkinter as tk
from tkinter import ttk, messagebox
from fabric_tracker_tk.db import Database

class CustomersUI:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        self.frame = ttk.Frame(master)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ttk.Label(self.frame, text="Customers", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")

        # Table
        self.tree = ttk.Treeview(self.frame, columns=("id", "name", "contact"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Customer Name")
        self.tree.heading("contact", text="Contact")
        self.tree.grid(row=1, column=0, columnspan=3, sticky="nsew")

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)

        # Form fields
        ttk.Label(self.frame, text="Customer Name:").grid(row=2, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.name_var).grid(row=2, column=1, sticky="ew")

        ttk.Label(self.frame, text="Contact:").grid(row=3, column=0, sticky="w")
        self.contact_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.contact_var).grid(row=3, column=1, sticky="ew")

        # Buttons
        ttk.Button(self.frame, text="Add", command=self.add_customer).grid(row=4, column=0, pady=5)
        ttk.Button(self.frame, text="Update", command=self.update_customer).grid(row=4, column=1, pady=5)
        ttk.Button(self.frame, text="Delete", command=self.delete_customer).grid(row=4, column=2, pady=5)

        # Load initial data
        self.load_customers()

        # Select row binding
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_customers(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self.db.fetch_customers()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def add_customer(self):
        name = self.name_var.get().strip()
        contact = self.contact_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Customer name is required")
            return
        self.db.insert_customer(name, contact)
        self.load_customers()
        self.clear_form()

    def update_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a customer to update")
            return
        item = self.tree.item(selected)
        customer_id = item["values"][0]
        name = self.name_var.get().strip()
        contact = self.contact_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Customer name is required")
            return
        self.db.update_customer(customer_id, name, contact)
        self.load_customers()
        self.clear_form()

    def delete_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a customer to delete")
            return
        item = self.tree.item(selected)
        customer_id = item["values"][0]
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this customer?")
        if confirm:
            self.db.delete_customer(customer_id)
            self.load_customers()
            self.clear_form()

    def clear_form(self):
        self.name_var.set("")
        self.contact_var.set("")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected)
        self.name_var.set(item["values"][1])
        self.contact_var.set(item["values"][2])
