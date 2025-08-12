import tkinter as tk
from tkinter import ttk, messagebox
import db
import datetime

class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(set(completion_list), key=str.lower)
        self['values'] = self._completion_list
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusIn>', lambda e: self.event_generate('<KeyRelease>'))

    def _matches(self, pattern):
        return [item for item in self._completion_list if pattern.lower() in item.lower()]

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return"):
            return
        typed = self.get()
        self['values'] = self._matches(typed) if typed else self._completion_list
        if len(self['values']) == 1:
            self.set(self['values'][0])
            self.icursor(tk.END)

class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller, dashboard_ref=None):
        super().__init__(parent)
        self.controller = controller
        self.dashboard_ref = dashboard_ref
        self.editing_rowid = None
        self.build_ui()
        self.bind_shortcuts()

    def build_ui(self):
        # Form
        labels = ["Date (YYYY-MM-DD):", "Batch ID:", "Supplier:", "Yarn Type:",
                  "Qty (kg):", "Qty (rolls):", "Delivered To:"]
        for i, text in enumerate(labels):
            ttk.Label(self, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=5)

        self.date_entry = ttk.Entry(self)
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.batch_id_entry = ttk.Entry(self)

        self.supplier_combo = AutocompleteCombobox(self)
        self.supplier_combo.bind("<<ComboboxSelected>>", lambda e: self.auto_fill_yarn_type())

        self.yarn_combo = AutocompleteCombobox(self)
        self.qty_kg_entry = ttk.Entry(self)
        self.qty_rolls_entry = ttk.Entry(self)

        self.delivered_to_combo = AutocompleteCombobox(self)
        self.delivered_to_combo.bind("<Return>", lambda e: self.save_record())  # Enter triggers save

        widgets = [self.date_entry, self.batch_id_entry, self.supplier_combo, self.yarn_combo,
                   self.qty_kg_entry, self.qty_rolls_entry, self.delivered_to_combo]
        for i, w in enumerate(widgets):
            w.grid(row=i, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(self, text="Save", command=self.save_record).grid(row=7, column=0, padx=5, pady=10)
        ttk.Button(self, text="Clear", command=self.clear_form).grid(row=7, column=1, padx=5, pady=10)
        ttk.Button(self, text="Reload Lists", command=self.refresh_autocomplete_lists).grid(row=7, column=2, padx=5, pady=10)

        # Table
        columns = ("rowid", "date", "batch_id", "supplier", "yarn_type", "qty_kg", "qty_rolls", "delivered_to")
        self.entries_tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        headings = ["ID", "Date", "Batch ID", "Supplier", "Yarn Type", "Qty (kg)", "Qty (rolls)", "Delivered To"]
        widths = [40, 90, 80, 120, 120, 70, 80, 150]
        for col, head, w in zip(columns, headings, widths):
            self.entries_tree.heading(col, text=head)
            self.entries_tree.column(col, width=w)
        self.entries_tree.grid(row=8, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        self.entries_tree.bind("<Double-1>", self.edit_selected)
        ttk.Button(self, text="Edit Selected", command=self.edit_selected).grid(row=9, column=0, pady=5)
        ttk.Button(self, text="Delete Selected", command=self.delete_selected).grid(row=9, column=1, pady=5)

        self.grid_rowconfigure(8, weight=1)
        self.refresh_autocomplete_lists()
        self.load_recent_entries()

    def bind_shortcuts(self):
        self.controller.bind_all("<Control-s>", lambda e: self.save_record())
        self.controller.bind_all("<Escape>", lambda e: self.clear_form())

    def get_suppliers(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers")
        master = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT DISTINCT supplier FROM purchases WHERE supplier != ''")
        used = [row[0] for row in cur.fetchall()]
        conn.close()
        return sorted(set(master + used), key=str.lower)

    def get_yarn_types(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM yarn_types")
        master = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT DISTINCT yarn_type FROM purchases WHERE yarn_type != ''")
        used = [row[0] for row in cur.fetchall()]
        conn.close()
        return sorted(set(master + used), key=str.lower)

    def get_delivered_to_list(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers")
        suppliers = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT DISTINCT delivered_to FROM purchases WHERE delivered_to != ''")
        delivered = [row[0] for row in cur.fetchall()]
        conn.close()
        return sorted(set(suppliers + delivered), key=str.lower)

    def refresh_autocomplete_lists(self):
        self.supplier_combo.set_completion_list(self.get_suppliers())
        self.yarn_combo.set_completion_list(self.get_yarn_types())
        self.delivered_to_combo.set_completion_list(self.get_delivered_to_list())

    def auto_fill_yarn_type(self):
        supplier = self.supplier_combo.get().strip()
        if supplier:
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT yarn_type FROM purchases WHERE supplier=? ORDER BY date DESC LIMIT 1", (supplier,))
            row = cur.fetchone()
            conn.close()
            if row:
                self.yarn_combo.set(row[0])

    def check_batch_id(self):
        batch_id = self.batch_id_entry.get().strip()
        if not batch_id:
            return
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT rowid, date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to
            FROM purchases WHERE batch_id=? ORDER BY date DESC LIMIT 1
        """, (batch_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            self.editing_rowid = row[0]
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, row[1])
            self.supplier_combo.set(row[3])
            self.yarn_combo.set(row[4])
            self.qty_kg_entry.delete(0, tk.END)
            self.qty_kg_entry.insert(0, row[5])
            self.qty_rolls_entry.delete(0, tk.END)
            self.qty_rolls_entry.insert(0, row[6])
            self.delivered_to_combo.set(row[7])

    def save_record(self):
        try:
            data = (
                self.date_entry.get().strip(),
                self.batch_id_entry.get().strip(),
                self.supplier_combo.get().strip(),
                self.yarn_combo.get().strip(),
                float(self.qty_kg_entry.get() or 0),
                int(self.qty_rolls_entry.get() or 0),
                self.delivered_to_combo.get().strip()
            )

            # Masters auto-update prompt
            self.update_masters_if_needed(data[2], data[3], data[6])

            conn = db.get_connection()
            cur = conn.cursor()
            if self.editing_rowid is None:
                cur.execute("""
                    INSERT INTO purchases (date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, data)
            else:
                cur.execute("""
                    UPDATE purchases SET date=?, batch_id=?, supplier=?, yarn_type=?, qty_kg=?, qty_rolls=?, delivered_to=?
                    WHERE rowid=?
                """, data + (self.editing_rowid,))
                self.editing_rowid = None
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Record saved.")
            self.refresh_autocomplete_lists()
            self.load_recent_entries(highlight_batch=data[1])

            if self.dashboard_ref:
                self.dashboard_ref.load_data()

            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_masters_if_needed(self, supplier, yarn_type, delivered_to):
        conn = db.get_connection()
        cur = conn.cursor()
        if supplier and supplier not in self.get_suppliers():
            if messagebox.askyesno("Add to Masters", f"Add supplier '{supplier}' to Masters?"):
                cur.execute("INSERT INTO suppliers (name) VALUES (?)", (supplier,))
        if yarn_type and yarn_type not in self.get_yarn_types():
            if messagebox.askyesno("Add to Masters", f"Add yarn type '{yarn_type}' to Masters?"):
                cur.execute("INSERT INTO yarn_types (name) VALUES (?)", (yarn_type,))
        conn.commit()
        conn.close()

    def clear_form(self):
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.batch_id_entry.delete(0, tk.END)
        self.supplier_combo.set("")
        self.yarn_combo.set("")
        self.qty_kg_entry.delete(0, tk.END)
        self.qty_rolls_entry.delete(0, tk.END)
        self.delivered_to_combo.set("")
        self.editing_rowid = None

    def load_recent_entries(self, highlight_batch=None):
        for row in self.entries_tree.get_children():
            self.entries_tree.delete(row)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT rowid, date, batch_id, supplier, yarn_type, qty_kg, qty_rolls, delivered_to
            FROM purchases ORDER BY date DESC, rowid DESC LIMIT 20
        """)
        for rec in cur.fetchall():
            row_id = self.entries_tree.insert("", "end", values=rec)
            if highlight_batch and rec[2] == highlight_batch:
                self.fade_highlight(row_id)
        conn.close()

    def fade_highlight(self, item_id):
        self.entries_tree.tag_configure("highlight", background="#ccffcc")
        self.entries_tree.item(item_id, tags=("highlight",))
        self.after(2000, lambda: self.entries_tree.tag_configure("highlight", background=""))

    def edit_selected(self, event=None):
        selected = self.entries_tree.selection()
        if not selected:
            return
        values = self.entries_tree.item(selected[0], "values")
        self.editing_rowid = values[0]
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, values[1])
        self.batch_id_entry.delete(0, tk.END)
        self.batch_id_entry.insert(0, values[2])
        self.supplier_combo.set(values[3])
        self.yarn_combo.set(values[4])
        self.qty_kg_entry.delete(0, tk.END)
        self.qty_kg_entry.insert(0, values[5])
        self.qty_rolls_entry.delete(0, tk.END)
        self.qty_rolls_entry.insert(0, values[6])
        self.delivered_to_combo.set(values[7])

    def delete_selected(self):
        selected = self.entries_tree.selection()
        if not selected:
            return
        rowid = self.entries_tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm", "Delete this record?"):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM purchases WHERE rowid=?", (rowid,))
            conn.commit()
            conn.close()
            self.load_recent_entries()
            if self.dashboard_ref:
                self.dashboard_ref.load_data()
