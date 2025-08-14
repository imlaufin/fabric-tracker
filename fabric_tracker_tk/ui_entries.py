# ui_entries.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from fabric_tracker_tk import db
# ---------------- Autocomplete Combobox ----------------
class AutocompleteCombobox(ttk.Combobox):
    """
    ttk.Combobox with live filtering.
    - Typing filters dropdown items (case-insensitive, startswith match)
    - If exactly one match, auto-completes
    - Allows free text not in the master list
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._all_values = []
        self._casefold_values = []
        self._last_typed = ""
        self._nav_keys = {"Up", "Down", "Left", "Right", "Home", "End", "PageUp", "PageDown"}
        self.bind("<KeyRelease>", self._on_keyrelease, add="+")
        self.bind("<<ComboboxSelected>>", self._on_select, add="+")
        self.bind("<FocusIn>", self._on_focusin, add="+")
        self.bind("<FocusOut>", self._on_focusout, add="+")
    def set_completion_list(self, values):
        self._all_values = list(values or [])
        self._casefold_values = [(v, v.casefold()) for v in self._all_values]
        self["values"] = self._all_values
    def _on_focusin(self, _e):
        self.after_idle(lambda: self.select_range(0, tk.END))
    def _on_focusout(self, _e):
        # If leaving field and text is empty, do nothing
        txt = self.get().strip()
        if not txt:
            return
        # Keep text as-is (do not force snap) so free entries are allowed
    def _on_select(self, _e):
        self["values"] = self._all_values
    def _on_keyrelease(self, e):
        if e.keysym in self._nav_keys:
            return
        txt = self.get()
        if not txt:
            self["values"] = self._all_values
            return
        cf = txt.casefold()
        matches = [orig for (orig, c) in self._casefold_values if c.startswith(cf)]
        # Update dropdown list
        self["values"] = matches if matches else self._all_values
        # Only auto-fill if exactly 1 match AND not deleting
        if len(matches) == 1 and e.keysym != "BackSpace":
            self.set(matches[0])
            self.icursor(len(txt))
            self.select_range(len(txt), tk.END)
        # Show dropdown when typing new characters
        if txt != self._last_typed:
            self.event_generate("<Down>")
        self._last_typed = txt
class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.selected_purchase_id = None
        self.selected_dyeing_id = None
        # Remember last entered values for faster bulk entry
        self._last_purchase_defaults = {
            "date": datetime.today().strftime("%d/%m/%Y"),
            "batch": "",
            "supplier": "",
            "yarn": "",
            "price": "",
            "delivered": "",
        }
        self.build_ui()
        self.refresh_lists()
        self.reload_entries()
        self.reload_dyeing_outputs()
    def build_ui(self):
        # Notebook for Purchases / Dyeing Outputs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        # --- Purchases Tab ---
        self.tab_purchases = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_purchases, text="Purchases")
        self.build_purchase_form(self.tab_purchases)
        self.build_purchase_table(self.tab_purchases)
        # --- Dyeing Outputs Tab ---
        self.tab_dyeing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dyeing, text="Dyeing Outputs")
        self.build_dyeing_form(self.tab_dyeing)
        self.build_dyeing_table(self.tab_dyeing)
    # ---------------- Purchases ----------------
    def build_purchase_form(self, parent):
        frm = ttk.Frame(parent)
        frm.pack(fill="x", padx=8, pady=8)
        # Form labels and entries
        ttk.Label(frm, text="Date").grid(row=0, column=0, sticky="w")
        self.date_e = ttk.Entry(frm, width=12)
        self.date_e.grid(row=0, column=1, sticky="w")
        self.date_e.insert(0, self._last_purchase_defaults["date"])
        ttk.Label(frm, text="Batch ID").grid(row=0, column=2, sticky="w")
        self.batch_e = ttk.Entry(frm, width=12)
        self.batch_e.grid(row=0, column=3, sticky="w")
        ttk.Label(frm, text="Lot No").grid(row=0, column=4, sticky="w")
        self.lot_e = ttk.Entry(frm, width=12)
        self.lot_e.grid(row=0, column=5, sticky="w")
        ttk.Label(frm, text="Supplier").grid(row=1, column=0, sticky="w")
        self.supplier_cb = AutocompleteCombobox(frm, width=25)
        self.supplier_cb.grid(row=1, column=1, sticky="w")
        ttk.Label(frm, text="Yarn Type").grid(row=1, column=2, sticky="w")
        self.yarn_cb = AutocompleteCombobox(frm, width=25)
        self.yarn_cb.grid(row=1, column=3, sticky="w")
        ttk.Label(frm, text="Qty (kg)").grid(row=2, column=0, sticky="w")
        self.kg_e = ttk.Entry(frm, width=12)
        self.kg_e.grid(row=2, column=1, sticky="w")
        ttk.Label(frm, text="Qty (rolls)").grid(row=2, column=2, sticky="w")
        self.rolls_e = ttk.Entry(frm, width=12)
        self.rolls_e.grid(row=2, column=3, sticky="w")
        ttk.Label(frm, text="Price/unit").grid(row=2, column=4, sticky="w")
        self.price_e = ttk.Entry(frm, width=12)
        self.price_e.grid(row=2, column=5, sticky="w")
        ttk.Label(frm, text="Delivered To").grid(row=3, column=0, sticky="w")
        self.delivered_cb = AutocompleteCombobox(frm, width=25)
        self.delivered_cb.grid(row=3, column=1, sticky="w")
        # Action buttons
        ttk.Button(frm, text="Save", command=self.save_purchase).grid(row=4, column=0, pady=8, sticky="w")
        ttk.Button(frm, text="Clear (Qty/Lot)", command=self.clear_purchase_form).grid(row=4, column=1, sticky="w")
        ttk.Button(frm, text="Create Lots", command=self.create_lot_dialog).grid(row=4, column=2, sticky="w")
        ttk.Button(frm, text="Reload Lists", command=self.refresh_lists).grid(row=4, column=3, sticky="w")
        # Ensure delivered-to snaps to best match on Enter
        self.delivered_cb.bind("<Return>", lambda e: self._snap_autocomplete(self.delivered_cb))
    def _snap_autocomplete(self, combo: AutocompleteCombobox):
        txt = combo.get().strip()
        if not txt:
            return
        # If typed text is a prefix of any value, set to first match
        values = list(combo["values"])
        for v in values:
            if v.lower().startswith(txt.lower()):
                combo.set(v)
                break
    def build_purchase_table(self, parent):
        cols = ("date","batch","lot","supplier","yarn","kg","rolls","price","delivered")
        headings = ["Date","Batch","Lot","Supplier","Yarn Type","Kg","Rolls","Price/unit","Delivered"]
        widths = [90,90,110,150,150,80,80,80,140]
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        # Scrollbars
        self.tree_scroll_y = ttk.Scrollbar(frame, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x = ttk.Scrollbar(frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12,
                                yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill="both", expand=True)
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        for c,h,w in zip(cols, headings, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.bind("<Double-1>", self.on_purchase_double_click)
    # ---------------- Dyeing Outputs ----------------
    def build_dyeing_form(self, parent):
        frm = ttk.Frame(parent)
        frm.pack(fill="x", padx=8, pady=8)
        ttk.Label(frm, text="Lot ID").grid(row=0, column=0, sticky="w")
        self.dyeing_lot_e = ttk.Entry(frm, width=12)
        self.dyeing_lot_e.grid(row=0, column=1, sticky="w")
        ttk.Label(frm, text="Dyeing Unit").grid(row=0, column=2, sticky="w")
        self.dyeing_unit_cb = AutocompleteCombobox(frm, width=25)
        self.dyeing_unit_cb.grid(row=0, column=3, sticky="w")
        ttk.Label(frm, text="Returned Date").grid(row=1, column=0, sticky="w")
        self.returned_date_e = ttk.Entry(frm, width=12)
        self.returned_date_e.grid(row=1, column=1, sticky="w")
        self.returned_date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))
        ttk.Label(frm, text="Qty (kg)").grid(row=1, column=2, sticky="w")
        self.returned_kg_e = ttk.Entry(frm, width=12)
        self.returned_kg_e.grid(row=1, column=3, sticky="w")
        ttk.Label(frm, text="Qty (rolls)").grid(row=1, column=4, sticky="w")
        self.returned_rolls_e = ttk.Entry(frm, width=12)
        self.returned_rolls_e.grid(row=1, column=5, sticky="w")
        ttk.Label(frm, text="Notes").grid(row=2, column=0, sticky="w")
        self.returned_notes_e = ttk.Entry(frm, width=50)
        self.returned_notes_e.grid(row=2, column=1, columnspan=5, sticky="w")
        # Action buttons
        ttk.Button(frm, text="Save", command=self.save_dyeing).grid(row=3, column=0, pady=8, sticky="w")
        ttk.Button(frm, text="Clear", command=self.clear_dyeing_form).grid(row=3, column=1, sticky="w")
    def build_dyeing_table(self, parent):
        cols = ("lot_id","unit","date","kg","rolls","notes")
        headings = ["Lot","Dyeing Unit","Returned Date","Kg","Rolls","Notes"]
        widths = [100,150,90,80,80,200]
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.dye_tree_scroll_y = ttk.Scrollbar(frame, orient="vertical")
        self.dye_tree_scroll_y.pack(side="right", fill="y")
        self.dye_tree_scroll_x = ttk.Scrollbar(frame, orient="horizontal")
        self.dye_tree_scroll_x.pack(side="bottom", fill="x")
        self.dye_tree = ttk.Treeview(frame, columns=cols, show="headings", height=12,
                                    yscrollcommand=self.dye_tree_scroll_y.set,
                                    xscrollcommand=self.dye_tree_scroll_x.set)
        self.dye_tree.pack(fill="both", expand=True)
        self.dye_tree_scroll_y.config(command=self.dye_tree.yview)
        self.dye_tree_scroll_x.config(command=self.dye_tree.xview)
        for c,h,w in zip(cols, headings, widths):
            self.dye_tree.heading(c, text=h)
            self.dye_tree.column(c, width=w)
        self.dye_tree.bind("<Double-1>", self.on_dyeing_double_click)
    # ---------------- Lists / Refresh ----------------
    def refresh_lists(self):
        # Suppliers, delivered_to, yarn types, dyeing units
        suppliers = [r["name"] for r in db.list_suppliers()]
        yarn_types = db.list_yarn_types()
        dyeing_units = [r["name"] for r in db.list_suppliers("dyeing_unit")]
        # Set full lists and bind to autocompletes
        self.supplier_cb.set_completion_list(suppliers)
        self.delivered_cb.set_completion_list(suppliers)
        self.yarn_cb.set_completion_list(yarn_types)
        self.dyeing_unit_cb.set_completion_list(dyeing_units)
        # If we have remembered defaults, set them (useful after first save)
        if self._last_purchase_defaults["supplier"]:
            self.supplier_cb.set(self._last_purchase_defaults["supplier"])
        if self._last_purchase_defaults["yarn"]:
            self.yarn_cb.set(self._last_purchase_defaults["yarn"])
        if self._last_purchase_defaults["delivered"]:
            self.delivered_cb.set(self._last_purchase_defaults["delivered"])
    # ---------------- Helpers: ensure masters exist ----------------
    def _ensure_supplier_exists(self, name, supplier_type=None):
        """Insert supplier into masters if missing."""
        name = (name or "").strip()
        if not name:
            return
        conn = db.get_connection()
        cur = conn.cursor()
        if supplier_type:
            cur.execute("SELECT id FROM suppliers WHERE name=? AND type=?", (name, supplier_type))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO suppliers (name, type) VALUES (?, ?)", (name, supplier_type))
        else:
            cur.execute("SELECT id FROM suppliers WHERE name=?", (name,))
            row = cur.fetchone()
            if not row:
                # If your schema requires type, this will store as generic/NULL
                try:
                    cur.execute("INSERT INTO suppliers (name) VALUES (?)", (name,))
                except Exception:
                    # fallback with type as 'supplier'
                    cur.execute("INSERT INTO suppliers (name, type) VALUES (?, ?)", (name, "supplier"))
        conn.commit()
        conn.close()
    def _ensure_yarn_type_exists(self, name):
        """Insert yarn type into masters if missing."""
        name = (name or "").strip()
        if not name:
            return
        conn = db.get_connection()
        cur = conn.cursor()
        # Common table name is 'yarn_types' with column 'name'
        cur.execute("SELECT name FROM yarn_types WHERE name=?", (name,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO yarn_types (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
    # ---------------- Purchases Functions ----------------
    def reload_entries(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM purchases ORDER BY date DESC")
        for row in cur.fetchall():
            display_date = db.db_to_ui_date(row["date"])
            self.tree.insert("", "end", iid=row["id"], values=(
                display_date,row["batch_id"],row["lot_no"],row["supplier"],row["yarn_type"],
                row["qty_kg"],row["qty_rolls"],row["price_per_unit"],row["delivered_to"]
            ))
        conn.close()
    def save_purchase(self):
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
        messagebox.showerror("Invalid", "Qty or Price must be numeric")
        return

    # Call validation & snapping helper
    self.validate_and_snap(date, yarn, kg, rolls, delivered, supplier, batch, lot, price)


def validate_and_snap(self, date, yarn, kg, rolls, delivered, supplier, batch, lot, price):
    # Check required fields
    if not date or not yarn or (kg == 0 and rolls == 0) or not delivered:
        messagebox.showwarning("Missing", "Please fill required fields")
        return

    # Snap delivered-to to first matching master (autocomplete behavior)
    self._snap_autocomplete(self.delivered_cb)
    delivered = self.delivered_cb.get().strip()

    # Auto-add Delivered To if new
    if delivered and delivered not in list(self.delivered_cb["values"]):
        self._ensure_supplier_exists(delivered, supplier_type="supplier")

    # Auto-add Supplier if new
    if supplier and supplier not in list(self.supplier_cb["values"]):
        self._ensure_supplier_exists(supplier, supplier_type="supplier")

    # Auto-add Yarn if new
    if yarn and yarn not in list(self.yarn_cb["values"]):
        self._ensure_yarn_type_exists(yarn)

    # Record or edit purchase in database
    try:
        if self.selected_purchase_id:
            db.edit_purchase(self.selected_purchase_id, date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
        else:
            db.record_purchase(date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
    except ValueError as e:
        messagebox.showerror("Invalid Date", str(e))
        return

    # Remember values for bulk entries (preserve on clear)
    self._last_purchase_defaults.update({
        "date": date,
        "batch": batch,
        "supplier": supplier,
        "yarn": yarn,
        "price": self.price_e.get().strip(),
        "delivered": delivered,
    })

    # Update dropdown lists so the new masters are immediately available
    self.refresh_lists()
    self.reload_entries()
    # Clear only fields that change per item (Lot/Qty), keep the rest
    self.clear_purchase_form(keep_defaults=True)
    self.selected_purchase_id = None
    if self.controller and hasattr(self.controller, "fabricators_frame"):
        try:
            self.controller.fabricators_frame.build_tabs()
        except Exception:
            pass
    def clear_purchase_form(self, keep_defaults=True):
        """If keep_defaults=True, preserve date/batch/supplier/yarn/price/delivered."""
        # Always clear lot/qty fields for bulk entry speed
        self.lot_e.delete(0, tk.END)
        self.kg_e.delete(0, tk.END)
        self.rolls_e.delete(0, tk.END)
        if keep_defaults:
            # Re-apply remembered defaults
            self.date_e.delete(0, tk.END)
            self.date_e.insert(0, self._last_purchase_defaults["date"])
            self.batch_e.delete(0, tk.END)
            self.batch_e.insert(0, self._last_purchase_defaults["batch"])
            self.supplier_cb.set(self._last_purchase_defaults["supplier"])
            self.yarn_cb.set(self._last_purchase_defaults["yarn"])
            self.price_e.delete(0, tk.END)
            self.price_e.insert(0, self._last_purchase_defaults["price"])
            self.delivered_cb.set(self._last_purchase_defaults["delivered"])
        else:
            # Full reset
            self.batch_e.delete(0, tk.END)
            self.price_e.delete(0, tk.END)
            self.date_e.delete(0, tk.END)
            self.date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))
            self.supplier_cb.set("")
            self.yarn_cb.set("")
            self.delivered_cb.set("")
            # Update defaults too
            self._last_purchase_defaults = {
                "date": self.date_e.get(),
                "batch": "",
                "supplier": "",
                "yarn": "",
                "price": "",
                "delivered": "",
            }
        self.selected_purchase_id = None
    def create_lot_dialog(self):
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
    def on_purchase_double_click(self, event):
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
        # Also refresh the remembered defaults based on this record
        self._last_purchase_defaults.update({
            "date": self.date_e.get(),
            "batch": self.batch_e.get(),
            "supplier": self.supplier_cb.get(),
            "yarn": self.yarn_cb.get(),
            "price": self.price_e.get(),
            "delivered": self.delivered_cb.get(),
        })
    # ---------------- Dyeing Outputs Functions ----------------
    def reload_dyeing_outputs(self):
        for r in self.dye_tree.get_children():
            self.dye_tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.id, d.lot_id, s.name as unit, d.returned_date, d.returned_qty_kg, d.returned_qty_rolls, d.notes
            FROM dyeing_outputs d
            LEFT JOIN suppliers s ON d.dyeing_unit_id = s.id
            ORDER BY d.returned_date DESC
        """)
        for row in cur.fetchall():
            display_date = db.db_to_ui_date(row["returned_date"])
            self.dye_tree.insert("", "end", iid=row["id"], values=(
                row["lot_id"], row["unit"], display_date, row["returned_qty_kg"], row["returned_qty_rolls"], row["notes"]
            ))
        conn.close()
    def save_dyeing(self):
        lot_id = self.dyeing_lot_e.get().strip()
        unit = self.dyeing_unit_cb.get().strip()
        returned_date = self.returned_date_e.get().strip()
        try:
            kg = float(self.returned_kg_e.get().strip() or 0)
            rolls = int(self.returned_rolls_e.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Qty must be numeric")
            return
        notes = self.returned_notes_e.get().strip()
        if not lot_id or not unit or (kg==0 and rolls==0):
            messagebox.showwarning("Missing", "Please fill required fields")
            return
        # Get dyeing unit ID (must exist)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM suppliers WHERE name=? AND type='dyeing_unit'", (unit,))
        row = cur.fetchone()
        if not row:
            messagebox.showerror("Invalid Unit", f"Dyeing unit '{unit}' not found")
            conn.close()
            return
        unit_id = row["id"]
        try:
            if self.selected_dyeing_id:
                cur.execute("""
                    UPDATE dyeing_outputs
                    SET lot_id=?, dyeing_unit_id=?, returned_date=?, returned_qty_kg=?, returned_qty_rolls=?, notes=?
                    WHERE id=?
                """, (lot_id, unit_id, db.ui_to_db_date(returned_date), kg, rolls, notes, self.selected_dyeing_id))
            else:
                db.record_dyeing_output(lot_id, unit_id, returned_date, kg, rolls, notes)
        except ValueError as e:
            messagebox.showerror("Invalid Date", str(e))
            conn.close()
            return
        conn.commit()
        conn.close()
        self.clear_dyeing_form()
        self.selected_dyeing_id = None
        self.reload_dyeing_outputs()
    def clear_dyeing_form(self):
        self.dyeing_lot_e.delete(0, tk.END)
        self.dyeing_unit_cb.set("")
        self.returned_date_e.delete(0, tk.END)
        self.returned_date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))
        self.returned_kg_e.delete(0, tk.END)
        self.returned_rolls_e.delete(0, tk.END)
        self.returned_notes_e.delete(0, tk.END)
        self.selected_dyeing_id = None
    def on_dyeing_double_click(self, event):
        item = self.dye_tree.selection()
        if not item:
            return
        dyeing_id = int(item[0])
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT d.*, s.name as unit_name FROM dyeing_outputs d LEFT JOIN suppliers s ON d.dyeing_unit_id=s.id WHERE d.id=?", (dyeing_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return
        self.selected_dyeing_id = dyeing_id
        self.dyeing_lot_e.delete(0, tk.END)
        self.dyeing_lot_e.insert(0, row["lot_id"])
        self.dyeing_unit_cb.set(row["unit_name"])
        self.returned_date_e.delete(0, tk.END)
        self.returned_date_e.insert(0, db.db_to_ui_date(row["returned_date"]))
        self.returned_kg_e.delete(0, tk.END)
        self.returned_kg_e.insert(0, row["returned_qty_kg"])
        self.returned_rolls_e.delete(0, tk.END)
        self.returned_rolls_e.insert(0, row["returned_qty_rolls"])
        self.returned_notes_e.delete(0, tk.END)
        self.returned_notes_e.insert(0, row["notes"])
