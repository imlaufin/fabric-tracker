# ui_entries.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db
from datetime import datetime

class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.selected_purchase_id = None  # for editing
        self.build_ui()
        self.refresh_lists()

    def build_ui(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=8, pady=8)

        # Form Labels and Entries
        ttk.Label(frm, text="Date").grid(row=0, column=0)
        self.date_e = ttk.Entry(frm, width=12)
        self.date_e.grid(row=0, column=1)
        self.date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))

        ttk.Label(frm, text="Batch ID").grid(row=0, column=2)
        self.batch_e = ttk.Entry(frm, width=12)
        self.batch_e.grid(row=0, column=3)

        ttk.Label(frm, text="Lot No").grid(row=0, column=4)
        self.lot_e = ttk.Entry(frm, width=12)
        self.lot_e.grid(row=0, column=5)

        ttk.Label(frm, text="Supplier").grid(row=1, column=0)
        self.supplier_cb = ttk.Combobox(frm, width=25)
        self.supplier_cb.grid(row=1, column=1)

        ttk.Label(frm, text="Yarn Type").grid(row=1, column=2)
        self.yarn_cb = ttk.Combobox(frm, width=25)
        self.yarn_cb.grid(row=1, column=3)

        ttk.Label(frm, text="Qty (kg)").grid(row=2, column=0)
        self.kg_e = ttk.Entry(frm, width=12)
        self.kg_e.grid(row=2, column=1)
        ttk.Label(frm, text="Qty (rolls)").grid(row=2, column=2)
        self.rolls_e = ttk.Entry(frm, width=12)
        self.rolls_e.grid(row=2, column=3)

        ttk.Label(frm, text="Price/unit").grid(row=2, column=4)
        self.price_e = ttk.Entry(frm, width=12)
        self.price_e.grid(row=2, column=5)

        ttk.Label(frm, text="Delivered To").grid(row=3, column=0)
        self.delivered_cb = ttk.Combobox(frm, width=25)
        self.delivered_cb.grid(row=3, column=1)

        # Action Buttons
        ttk.Button(frm, text="Save", command=self.save).grid(row=4, column=0, pady=8)
        ttk.Button(frm, text="Clear", command=self.clear_form).grid(row=4, column=1)
        ttk.Button(frm, text="Create Lot for Batch", command=self.create_lot_dialog).grid(row=4, column=2)
        ttk.Button(frm, text="Reload Lists", command=self.refresh_lists).grid(row=4, column=3)

        # Recent entries table
        cols = ("date","batch","lot","supplier","yarn","kg","rolls","price","delivered")
        headings = ["Date","Batch","Lot","Supplier","Yarn Type","Kg","Rolls","Price/unit","Delivered"]
        widths = [90,90,110,150,150,80,80,80,140]
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c,h,w in zip(cols, headings, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Return>", lambda e: self.save())
        self.delivered_cb.bind("<Return>", lambda e: self.save())

        self.reload_entries()

    def refresh_lists(self):
        """Refresh suppliers, delivered-to, and yarn type lists from DB."""
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        masters = [r["name"] for r in cur.fetchall()]

        self.delivered_cb["values"] = masters
        cur.execute("SELECT DISTINCT name FROM suppliers ORDER BY name")
        self.supplier_cb["values"] = [r["name"] for r in cur.fetchall()]

        cur.execute("SELECT name FROM yarn_types ORDER BY name")
        self.yarn_cb["values"] = [r["name"] for r in cur.fetchall()]

        conn.close()

    def reload_entries(self):
        """Load existing purchases into the table."""
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id,date,batch_id,lot_no,supplier,yarn_type,qty_kg,qty_rolls,price_per_unit,delivered_to
            FROM purchases ORDER BY date DESC
        """)
        for row in cur.fetchall():
            display_date = db.db_to_ui_date(row["date"])
            self.tree.insert("", "end", iid=row["id"], values=(
                display_date,row["batch_id"],row["lot_no"],row["supplier"],row["yarn_type"],
                row["qty_kg"],row["qty_rolls"],row["price_per_unit"],row["delivered_to"]
            ))
        conn.close()

    def save(self):
        """Save or update a purchase entry."""
        date = self.date_e.get().strip()
        batch = self.batch_e.get().strip()
        lot = self.lot_e.get().strip()
        supplier = self.supplier_cb.get().strip()
        yarn = self.yarn_cb.get().strip()
        delivered = self.delivered_cb.get().strip()
        try:
            kg = float(self.kg_e.get().strip() or 0)
            rolls = int(self.rolls_e.get().strip() or 0)
            price = float(self.price_e.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Qty or Price fields must be numeric")
            return

        if not date or not yarn or (kg==0 and rolls==0) or not delivered:
            messagebox.showwarning("Missing", "Please fill required fields")
            return

        if delivered not in self.delivered_cb["values"]:
            messagebox.showerror("Invalid Delivered To", f"'{delivered}' must be in Masters list")
            return

        try:
            if self.selected_purchase_id:
                db.edit_purchase(self.selected_purchase_id, date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
            else:
                db.record_purchase(date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
        except ValueError as e:
            messagebox.showerror("Invalid Date", str(e))
            return

        self.refresh_lists()
        self.reload_entries()
        self.clear_form()
        self.selected_purchase_id = None

        if self.controller and hasattr(self.controller, "fabricators_frame"):
            try:
                self.controller.fabricators_frame.build_tabs()
            except Exception:
                pass

    def clear_form(self):
        """Reset form fields."""
        self.batch_e.delete(0, tk.END)
        self.lot_e.delete(0, tk.END)
        self.kg_e.delete(0, tk.END)
        self.rolls_e.delete(0, tk.END)
        self.price_e.delete(0, tk.END)
        self.date_e.delete(0, tk.END)
        self.date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))
        self.selected_purchase_id = None

    def create_lot_dialog(self):
        """Dialog to create multiple lots for a batch."""
        batch_ref = self.batch_e.get().strip()
        if not batch_ref:
            messagebox.showwarning("Batch required", "Enter the batch id first.")
            return
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, expected_lots FROM batches WHERE batch_ref=?", (batch_ref,))
        row = cur.fetchone()
        if not row:
            if messagebox.askyesno("Batch not found", "Batch not found. Create new batch?"):
                fabricator_name = self.delivered_cb.get().strip()
                cur.execute("SELECT id FROM suppliers WHERE name=?", (fabricator_name,))
                fr = cur.fetchone()
                fid = fr["id"] if fr else None
                b_id = db.create_batch(batch_ref, fid, "", 0, "")
            else:
                conn.close()
                return
        else:
            b_id = row["id"]

        try:
            lots = int(simpledialog.askstring("Lots", "How many lots to create?", parent=self) or "0")
        except Exception:
            lots = 0
        if lots <= 0:
            conn.close()
            return

        cur.execute("SELECT MAX(lot_index) as maxidx FROM lots WHERE batch_id=?", (b_id,))
        maxidx = cur.fetchone()["maxidx"] or 0
        for i in range(1, lots+1):
            db.create_lot(b_id, maxidx+i)
        conn.close()
        messagebox.showinfo("Done", f"{lots} lots created.")

    def on_tree_double_click(self, event):
        """Load selected purchase into form for editing."""
        item = self.tree.selection()
        if not item:
            return
        purchase_id = int(item[0])
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return
        self.selected_purchase_id = purchase_id
        self.date_e.delete(0, tk.END)
        self.date_e.insert(0, db.db_to_ui_date(row["date"]))
        self.batch_e.delete(0, tk.END)
        self.batch_e.insert(0, row["batch_id"])
        self.lot_e.delete(0, tk.END)
        self.lot_e.insert(0, row["lot_no"])
        self.supplier_cb.set(row["supplier"])
        self.yarn_cb.set(row["yarn_type"])
        self.kg_e.delete(0, tk.END)
        self.kg_e.insert(0, row["qty_kg"])
        self.rolls_e.delete(0, tk.END)
        self.rolls_e.insert(0, row["qty_rolls"])
        self.price_e.delete(0, tk.END)
        self.price_e.insert(0, row["price_per_unit"])
        self.delivered_cb.set(row["delivered_to"])
