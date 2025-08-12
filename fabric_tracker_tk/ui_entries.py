import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import db
from datetime import datetime


class AutocompleteCombobox(ttk.Combobox):
    """A combobox that autocompletes as you type."""
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self['values'] = self._completion_list
        self.bind('<KeyRelease>', self._handle_keyrelease)

    def _handle_keyrelease(self, event):
        if event.keysym in ("BackSpace", "Left", "Right", "Up", "Down"):
            return
        value = self.get()
        if value == '':
            self['values'] = self._completion_list
        else:
            data = [item for item in self._completion_list if item.lower().startswith(value.lower())]
            self['values'] = data
        if self['values']:
            self.event_generate('<Down>')


class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        form_frame = ttk.Frame(self)
        form_frame.pack(side="top", fill="x", padx=10, pady=10)

        # Date
        ttk.Label(form_frame, text="Date (dd/mm/yyyy):").grid(row=0, column=0, sticky="w")
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(form_frame, textvariable=self.date_var)
        self.date_entry.grid(row=0, column=1, sticky="ew")
        self.date_var.set(datetime.now().strftime("%d/%m/%Y"))

        # Supplier
        ttk.Label(form_frame, text="Supplier:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.supplier_var = tk.StringVar()
        self.supplier_combo = AutocompleteCombobox(form_frame, textvariable=self.supplier_var)
        self.supplier_combo.grid(row=0, column=3, sticky="ew")

        # Delivered To
        ttk.Label(form_frame, text="Delivered To:").grid(row=0, column=4, sticky="w", padx=(10, 0))
        self.delivered_to_var = tk.StringVar()
        self.delivered_to_combo = AutocompleteCombobox(form_frame, textvariable=self.delivered_to_var)
        self.delivered_to_combo.grid(row=0, column=5, sticky="ew")
        self.delivered_to_combo.bind("<Return>", self.save_entry)

        # Yarn Type
        ttk.Label(form_frame, text="Yarn Type:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.yarn_var = tk.StringVar()
        self.yarn_entry = ttk.Entry(form_frame, textvariable=self.yarn_var)
        self.yarn_entry.grid(row=1, column=1, sticky="ew", pady=(10, 0))

        # Quantity kg
        ttk.Label(form_frame, text="Qty (kg):").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=(10, 0))
        self.kg_var = tk.DoubleVar()
        self.kg_entry = ttk.Entry(form_frame, textvariable=self.kg_var)
        self.kg_entry.grid(row=1, column=3, sticky="ew", pady=(10, 0))

        # Quantity rolls
        ttk.Label(form_frame, text="Qty (rolls):").grid(row=1, column=4, sticky="w", padx=(10, 0), pady=(10, 0))
        self.rolls_var = tk.IntVar()
        self.rolls_entry = ttk.Entry(form_frame, textvariable=self.rolls_var)
        self.rolls_entry.grid(row=1, column=5, sticky="ew", pady=(10, 0))

        # Save button
        save_btn = ttk.Button(form_frame, text="Save Entry", command=self.save_entry)
        save_btn.grid(row=2, column=0, columnspan=6, pady=10)

        # List of entries
        self.tree = ttk.Treeview(self, columns=("date", "supplier", "delivered_to", "yarn", "kg", "rolls"), show="headings")
        for col, txt, w in [
            ("date", "Date", 90),
            ("supplier", "Supplier", 150),
            ("delivered_to", "Delivered To", 150),
            ("yarn", "Yarn Type", 120),
            ("kg", "Qty (kg)", 80),
            ("rolls", "Qty (rolls)", 90)
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_dropdowns()
        self.load_entries()

    def load_dropdowns(self):
        suppliers = [s["name"] for s in db.list_suppliers()]
        self.supplier_combo.set_completion_list(suppliers)
        self.delivered_to_combo.set_completion_list(suppliers)

    def load_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM purchases ORDER BY date DESC").fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(
                db.db_to_ui_date(r["date"]),
                r["supplier"],
                r["delivered_to"],
                r["yarn_type"],
                r["qty_kg"],
                r["qty_rolls"]
            ))

    def save_entry(self, event=None):
        try:
            date_db = db.ui_to_db_date(self.date_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid date", "Please enter the date in dd/mm/yyyy format.")
            return

        supplier = self.supplier_var.get().strip()
        delivered_to = self.delivered_to_var.get().strip()
        yarn = self.yarn_var.get().strip()
        qty_kg = self.kg_var.get()
        qty_rolls = self.rolls_var.get()

        if not supplier or not delivered_to or not yarn:
            messagebox.showerror("Missing Data", "Please fill all fields.")
            return

        conn = db.get_connection()
        conn.execute("""
            INSERT INTO purchases (date, supplier, delivered_to, yarn_type, qty_kg, qty_rolls)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_db, supplier, delivered_to, yarn, qty_kg, qty_rolls))
        conn.commit()
        conn.close()

        self.load_entries()
        self.clear_form()

    def clear_form(self):
        self.date_var.set(datetime.now().strftime("%d/%m/%Y"))
        self.supplier_var.set("")
        self.delivered_to_var.set("")
        self.yarn_var.set("")
        self.kg_var.set(0)
        self.rolls_var.set(0)
