# ui_entries.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db
from datetime import datetime

class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.refresh_lists()

    def build_ui(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=8, pady=8)

        ttk.Label(frm, text="Date").grid(row=0, column=0)
        self.date_e = ttk.Entry(frm, width=12); self.date_e.grid(row=0, column=1); self.date_e.insert(0, datetime.today().strftime("%Y-%m-%d"))
        ttk.Label(frm, text="Batch ID").grid(row=0, column=2)
        self.batch_e = ttk.Entry(frm, width=12); self.batch_e.grid(row=0, column=3)

        ttk.Label(frm, text="Lot No (optional)").grid(row=0, column=4)
        self.lot_e = ttk.Entry(frm, width=12); self.lot_e.grid(row=0, column=5)

        ttk.Label(frm, text="Supplier").grid(row=1, column=0)
        self.supplier_cb = ttk.Combobox(frm, width=25); self.supplier_cb.grid(row=1, column=1)

        ttk.Label(frm, text="Yarn Type").grid(row=1, column=2)
        self.yarn_cb = ttk.Combobox(frm, width=25); self.yarn_cb.grid(row=1, column=3)

        ttk.Label(frm, text="Qty (kg)").grid(row=2, column=0)
        self.kg_e = ttk.Entry(frm, width=12); self.kg_e.grid(row=2, column=1)
        ttk.Label(frm, text="Qty (rolls)").grid(row=2, column=2)
        self.rolls_e = ttk.Entry(frm, width=12); self.rolls_e.grid(row=2, column=3)

        ttk.Label(frm, text="Delivered To").grid(row=3, column=0)
        self.delivered_cb = ttk.Combobox(frm, width=25); self.delivered_cb.grid(row=3, column=1)

        ttk.Button(frm, text="Save", command=self.save).grid(row=4, column=0, pady=8)
        ttk.Button(frm, text="Clear", command=self.clear_form).grid(row=4, column=1)

        ttk.Button(frm, text="Create Lot for Batch", command=self.create_lot_dialog).grid(row=4, column=2)
        ttk.Button(frm, text="Reload Lists", command=self.refresh_lists).grid(row=4, column=3)

        # recent entries table
        cols = ("date","batch","lot","supplier","yarn","kg","rolls","delivered")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c, h, w in zip(cols, ["Date","Batch","Lot","Supplier","Yarn Type","Kg","Rolls","Delivered"], [90,90,110,150,150,80,80,140]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.reload_entries()

        # enter key in delivered to saves
        self.delivered_cb.bind("<Return>", lambda e: self.save())

    def refresh_lists(self):
        # suppliers for comboboxes including masters and existing used suppliers
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        masters = [r["name"] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT supplier FROM purchases WHERE supplier IS NOT NULL AND supplier != ''")
        used = [r["supplier"] for r in cur.fetchall() if r["supplier"]]
        cur.execute("SELECT DISTINCT delivered_to FROM purchases WHERE delivered_to IS NOT NULL AND delivered_to != ''")
        used2 = [r["delivered_to"] for r in cur.fetchall() if r["delivered_to"]]
        all_suppliers = sorted(set(masters + used + used2))
        self.supplier_cb["values"] = all_suppliers
        self.delivered_cb["values"] = all_suppliers

        cur.execute("SELECT name FROM yarn_types ORDER BY name")
        yarns = [r["name"] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT yarn_type FROM purchases WHERE yarn_type != ''")
        usedy = [r["yarn_type"] for r in cur.fetchall() if r["yarn_type"]]
        self.yarn_cb["values"] = sorted(set(yarns + usedy))
        conn.close()

    def reload_entries(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT date, batch_id, lot_no, supplier, yarn_type, qty_kg, qty_rolls, delivered_to FROM purchases ORDER BY date DESC")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=(row["date"], row["batch_id"], row["lot_no"], row["supplier"], row["yarn_type"], row["qty_kg"], row["qty_rolls"], row["delivered_to"]))
        conn.close()

    def save(self):
        date = self.date_e.get().strip()
        batch = self.batch_e.get().strip()
        lot = self.lot_e.get().strip()
        supplier = self.supplier_cb.get().strip()
        yarn = self.yarn_cb.get().strip()
        try:
            kg = float(self.kg_e.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Qty kg must be a number")
            return
        try:
            rolls = int(self.rolls_e.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Qty rolls must be integer")
            return
        delivered = self.delivered_cb.get().strip()
        if not date or not supplier or not yarn or (kg==0 and rolls==0) or not delivered:
            messagebox.showwarning("Missing", "Please fill required fields")
            return

        # Record in purchases table
        db.record_purchase(date, batch, lot, supplier, yarn, kg, rolls, delivered, notes="")
        # refresh lists and entries
        self.refresh_lists()
        self.reload_entries()

        # keep delivered and yarn filled but clear batch/quantities for quick repeated entry
        self.kg_e.delete(0, tk.END)
        self.rolls_e.delete(0, tk.END)
        self.batch_e.delete(0, tk.END)
        self.lot_e.delete(0, tk.END)
        self.kg_e.focus()

        # If controller provided and has knitting/dyeing tabs, reload relevant tabs
        if self.controller and hasattr(self.controller, "fabricators_frame"):
            try:
                self.controller.fabricators_frame.build_tabs()
            except Exception:
                pass

    def clear_form(self):
        self.batch_e.delete(0, tk.END)
        self.lot_e.delete(0, tk.END)
        self.kg_e.delete(0, tk.END)
        self.rolls_e.delete(0, tk.END)

    def create_lot_dialog(self):
        batch_ref = self.batch_e.get().strip()
        if not batch_ref:
            messagebox.showwarning("Batch required", "Enter the batch id first (temporary allowed).")
            return
        # find batch id in DB or ask to create
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, expected_lots FROM batches WHERE batch_ref=?", (batch_ref,))
        row = cur.fetchone()
        if not row:
            if messagebox.askyesno("Batch not found", "Batch not found. Create new batch entry?"):
                # create batch with zero expected lots initially
                fabricator_name = self.delivered_cb.get().strip()
                # find fabricator id
                cur.execute("SELECT id FROM suppliers WHERE name=?", (fabricator_name,))
                fr = cur.fetchone()
                fid = fr["id"] if fr else None
                b_id = db.create_batch(batch_ref, fid if fid else None, "", 0, "")
            else:
                conn.close()
                return
        else:
            b_id = row["id"]
        # ask how many lots to create or index
        try:
            lots = int(simpledialog.askstring("Lots", "How many lots to create?", parent=self) or "0")
        except Exception:
            lots = 0
        if lots <= 0:
            conn.close()
            return
        # create sequential lots
        # find current max index
        cur.execute("SELECT MAX(lot_index) as maxidx FROM lots WHERE batch_id=?", (b_id,))
        maxidx = cur.fetchone()["maxidx"] or 0
        for i in range(1, lots+1):
            db.create_lot(b_id, maxidx + i)
        conn.close()
        messagebox.showinfo("Done", f"{lots} lots created.")
