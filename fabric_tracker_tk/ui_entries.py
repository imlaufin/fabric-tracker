import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from fabric_tracker_tk import db

# ---------------- Autocomplete Combobox ----------------
class AutocompleteCombobox(ttk.Combobox):
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
        txt = self.get().strip()
        if not txt:
            return

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
        self["values"] = matches if matches else self._all_values
        if len(matches) == 1 and e.keysym != "BackSpace":
            self.set(matches[0])
            self.icursor(len(txt))
            self.select_range(len(txt), tk.END)
        if txt != self._last_typed:
            self.event_generate("<Down>")
        self._last_typed = txt

class EntriesFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.selected_purchase_id = None
        self.selected_dyeing_id = None
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
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.tab_purchases = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_purchases, text="Purchases")
        self.build_purchase_form(self.tab_purchases)
        self.build_purchase_table(self.tab_purchases)
        self.tab_dyeing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dyeing, text="Dyeing Outputs")
        self.build_dyeing_form(self.tab_dyeing)
        self.build_dyeing_table(self.tab_dyeing)

    def build_purchase_form(self, parent):
        frm = ttk.Frame(parent)
        frm.pack(fill="x", padx=8, pady=8)
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
        self.rib_collar_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Includes Rib/Collar", variable=self.rib_collar_var).grid(row=3, column=2, sticky="w")
        ttk.Button(frm, text="Save", command=self.save_purchase).grid(row=4, column=0, pady=8, sticky="w")
        ttk.Button(frm, text="Clear (Qty/Lot)", command=self.clear_purchase_form).grid(row=4, column=1, sticky="w")
        ttk.Button(frm, text="Create Batch", command=self.create_batch_dialog).grid(row=4, column=2, sticky="w")
        ttk.Button(frm, text="Reload Lists", command=self.refresh_lists).grid(row=4, column=3, sticky="w")
        ttk.Button(frm, text="Show Net Price", command=self.show_net_price).grid(row=4, column=4, pady=5, sticky="w")
        self.delivered_cb.bind("<Return>", lambda e: self._snap_autocomplete(self.delivered_cb))

    def _snap_autocomplete(self, combo):
        txt = combo.get().strip()
        if not txt:
            return
        values = list(combo["values"])
        for v in values:
            if v.lower().startswith(txt.lower()):
                combo.set(v)
                break

    def build_purchase_table(self, parent):
        cols = ("date", "batch", "lot", "supplier", "yarn", "kg", "rolls", "price", "delivered")
        headings = ["Date", "Batch", "Lot", "Supplier", "Yarn Type", "Kg", "Rolls", "Price/unit", "Delivered"]
        widths = [90, 90, 110, 150, 150, 80, 80, 80, 140]
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree_scroll_y = ttk.Scrollbar(frame, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x = ttk.Scrollbar(frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12,
                                yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill="both", expand=True)
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        for c, h, w in zip(cols, headings, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.bind("<Double-1>", self.on_purchase_double_click)
        self.tree.bind("<Button-3>", self.show_purchase_context_menu)

    def show_purchase_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Delete", command=lambda: self.delete_purchase_confirmed(int(item)))
            menu.add_command(label="Delete Batch", command=lambda: self.delete_batch_confirmed(self.tree.set(item, "batch")))
            menu.post(event.x_root, event.y_root)

    def delete_purchase_confirmed(self, purchase_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this purchase?"):
            db.delete_purchase(purchase_id)
            self.reload_entries()
            if self.controller and hasattr(self.controller, "fabricators_frame"):
                self.controller.fabricators_frame.build_tabs()

    def delete_batch_confirmed(self, batch_ref):
        if not batch_ref:
            messagebox.showwarning("Invalid Selection", "No batch selected for deletion.")
            return
        if messagebox.askyesno("Confirm Delete Batch", f"Are you sure you want to delete batch '{batch_ref}' and all its lots? This cannot be undone if no purchases are associated."):
            success = db.delete_batch(batch_ref)
            if success:
                self.reload_entries()
                if self.controller and hasattr(self.controller, "fabricators_frame"):
                    self.controller.fabricators_frame.build_tabs()
            else:
                messagebox.showwarning("Delete Failed", f"Batch '{batch_ref}' cannot be deleted because it has associated purchases.")

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
        ttk.Button(frm, text="Save", command=self.save_dyeing).grid(row=3, column=0, pady=8, sticky="w")
        ttk.Button(frm, text="Clear", command=self.clear_dyeing_form).grid(row=3, column=1, sticky="w")

    def build_dyeing_table(self, parent):
        cols = ("lot_id", "unit", "date", "kg", "rolls", "notes")
        headings = ["Lot", "Dyeing Unit", "Returned Date", "Kg", "Rolls", "Notes"]
        widths = [100, 150, 90, 80, 80, 200]
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
        for c, h, w in zip(cols, headings, widths):
            self.dye_tree.heading(c, text=h)
            self.dye_tree.column(c, width=w)
        self.dye_tree.bind("<Double-1>", self.on_dyeing_double_click)
        self.dye_tree.bind("<Button-3>", self.show_dyeing_context_menu)

    def show_dyeing_context_menu(self, event):
        item = self.dye_tree.identify_row(event.y)
        if item:
            self.dye_tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Delete", command=lambda: self.delete_dyeing_confirmed(int(item)))
            menu.post(event.x_root, event.y_root)

    def delete_dyeing_confirmed(self, dyeing_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this dyeing output?"):
            db.delete_dyeing_output(dyeing_id)
            self.reload_dyeing_outputs()

    def refresh_lists(self):
        suppliers = [r["name"] for r in db.list_suppliers()]
        yarn_types = db.list_yarn_types()
        dyeing_units = [r["name"] for r in db.list_suppliers("dyeing_unit")]
        knitting_units = [r["name"] for r in db.list_suppliers("knitting_unit")]
        self.supplier_cb.set_completion_list(suppliers)
        self.delivered_cb.set_completion_list(knitting_units + dyeing_units)  # Allow delivery to knitting or dyeing
        self.yarn_cb.set_completion_list(yarn_types)
        self.dyeing_unit_cb.set_completion_list(dyeing_units)
        if self._last_purchase_defaults["supplier"]:
            self.supplier_cb.set(self._last_purchase_defaults["supplier"])
        if self._last_purchase_defaults["yarn"]:
            self.yarn_cb.set(self._last_purchase_defaults["yarn"])
        if self._last_purchase_defaults["delivered"]:
            self.delivered_cb.set(self._last_purchase_defaults["delivered"])

    def _ensure_supplier_exists(self, name, supplier_type=None):
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
                cur.execute("INSERT INTO suppliers (name, type) VALUES (?, ?)", (name, "yarn_supplier"))
        conn.commit()
        conn.close()

    def _ensure_yarn_type_exists(self, name):
        name = (name or "").strip()
        if not name:
            return
        db.add_yarn_type(name)

    def reload_entries(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM purchases ORDER BY date DESC")
            for row in cur.fetchall():
                display_date = db.db_to_ui_date(row["date"])
                self.tree.insert("", "end", iid=row["id"], values=(
                    display_date, row["batch_id"], row["lot_no"], row["supplier"], row["yarn_type"],
                    row["qty_kg"], row["qty_rolls"], row["price_per_unit"], row["delivered_to"]
                ))

    def save_purchase(self):
        date = self.date_e.get().strip()
        batch = self.batch_e.get().strip()
        lot = self.lot_e.get().strip()
        supplier = self.supplier_cb.get().strip()
        yarn = self.yarn_cb.get().strip()
        delivered = self.delivered_cb.get().strip()
        includes_rib_collar = self.rib_collar_var.get()

        try:
            kg = float(self.kg_e.get().strip() or 0)
            rolls = int(self.rolls_e.get().strip() or 0)
            price = float(self.price_e.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Qty (kg/rolls) or Price must be numeric")
            return

        if kg <= 0 and rolls <= 0:
            messagebox.showwarning("Invalid Quantity", "At least one of Qty (kg) or Qty (rolls) must be greater than 0")
            return

        self.validate_and_snap(date, yarn, kg, rolls, delivered, supplier, batch, lot, price, includes_rib_collar)

    def validate_and_snap(self, date, yarn, kg, rolls, delivered, supplier, batch, lot, price, includes_rib_collar):
        if not date or not yarn or not delivered:
            messagebox.showwarning("Missing", "Please fill required fields: Date, Yarn Type, Delivered To")
            return

        self._snap_autocomplete(self.delivered_cb)
        delivered = self.delivered_cb.get().strip()

        if delivered and delivered not in list(self.delivered_cb["values"]):
            self._ensure_supplier_exists(delivered)

        if supplier and supplier not in list(self.supplier_cb["values"]):
            self._ensure_supplier_exists(supplier)

        if yarn and yarn not in list(self.yarn_cb["values"]):
            self._ensure_yarn_type_exists(yarn)

        try:
            if self.selected_purchase_id:
                db.edit_purchase(self.selected_purchase_id, date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
                db.update_batch_status(batch, 'Ordered')  # Update status on edit
            else:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT fabric_type_id FROM batches WHERE batch_ref = ?", (batch,))
                    row = cur.fetchone()
                    if row:
                        fabric_type_id = row["fabric_type_id"]
                        db.record_purchase(date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
                        db.update_batch_status(batch, 'Ordered')  # Update status on new purchase
                        # Rib/Collar validation (stock check handled by db.py)
                        if includes_rib_collar:
                            cur.execute("""
                                SELECT yc.yarn_type, yc.ratio
                                FROM fabric_yarn_composition yc
                                WHERE yc.fabric_type_id = ? AND (yc.component = 'Rib' OR yc.component = 'Collar')
                            """, (fabric_type_id,))
                            rib_collar_comps = cur.fetchall()
                            if not rib_collar_comps:
                                messagebox.showwarning("No Composition", "No Rib/Collar composition defined for this batch.")
                    else:
                        db.record_purchase(date, batch, lot, supplier, yarn, kg, rolls, price, delivered)
                        db.update_batch_status(batch, 'Ordered')  # Update status for new batch
        except ValueError as e:
            messagebox.showerror("Invalid Date", str(e))
            return

        self._last_purchase_defaults.update({
            "date": date,
            "batch": batch,
            "supplier": supplier,
            "yarn": yarn,
            "price": self.price_e.get().strip(),
            "delivered": delivered,
        })

        self.refresh_lists()
        self.reload_entries()
        self.clear_purchase_form(keep_defaults=True)
        self.selected_purchase_id = None

        # Notify controller to update statuses
        if self.controller and hasattr(self.controller, "on_purchase_recorded"):
            self.controller.on_purchase_recorded(batch, lot, delivered)

        if self.controller and hasattr(self.controller, "fabricators_frame"):
            self.controller.fabricators_frame.build_tabs()

    def clear_purchase_form(self, keep_defaults=True):
        self.lot_e.delete(0, tk.END)
        self.kg_e.delete(0, tk.END)
        self.rolls_e.delete(0, tk.END)
        if keep_defaults:
            self.date_e.delete(0, tk.END)
            self.date_e.insert(0, self._last_purchase_defaults["date"])
            self.batch_e.delete(0, tk.END)
            self.batch_e.insert(0, self._last_purchase_defaults["batch"])
            self.supplier_cb.set(self._last_purchase_defaults["supplier"])
            self.yarn_cb.set(self._last_purchase_defaults["yarn"])
            self.price_e.delete(0, tk.END)
            self.price_e.insert(0, self._last_purchase_defaults["price"])
            self.delivered_cb.set(self._last_purchase_defaults["delivered"])
            self.rib_collar_var.set(False)  # Reset Rib/Collar checkbox
        else:
            self.batch_e.delete(0, tk.END)
            self.price_e.delete(0, tk.END)
            self.date_e.delete(0, tk.END)
            self.date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))
            self.supplier_cb.set("")
            self.yarn_cb.set("")
            self.delivered_cb.set("")
            self.rib_collar_var.set(False)  # Reset Rib/Collar checkbox
            self._last_purchase_defaults = {
                "date": self.date_e.get(),
                "batch": "",
                "supplier": "",
                "yarn": "",
                "price": "",
                "delivered": "",
            }
        self.selected_purchase_id = None

    def create_batch_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Create New Batch")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        # Fields
        ttk.Label(dialog, text="Batch Number:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        batch_e = ttk.Entry(dialog, width=30)
        batch_e.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(dialog, text="Number of Lots:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        lots_e = ttk.Entry(dialog, width=30)
        lots_e.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(dialog, text="Fabric Type:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        fabric_cb = AutocompleteCombobox(dialog, width=30)
        fabric_cb.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        fabric_types = [comp["name"] for comp in db.list_fabric_compositions()]
        fabric_types = list(dict.fromkeys(fabric_types))  # Remove duplicates
        fabric_cb.set_completion_list(fabric_types)

        ttk.Label(dialog, text="Has Rib?").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        rib_var = tk.StringVar(value="No")
        ttk.Radiobutton(dialog, text="Yes", variable=rib_var, value="Yes").grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(dialog, text="No", variable=rib_var, value="No").grid(row=3, column=1, sticky="e", padx=5)

        ttk.Label(dialog, text="Has Collar?").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        collar_var = tk.StringVar(value="No")
        ttk.Radiobutton(dialog, text="Yes", variable=collar_var, value="Yes").grid(row=4, column=1, sticky="w")
        ttk.Radiobutton(dialog, text="No", variable=collar_var, value="No").grid(row=4, column=1, sticky="e", padx=5)

        ttk.Label(dialog, text="Knitting Unit:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        knitting_cb = AutocompleteCombobox(dialog, width=30)
        knitting_cb.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        knitting_units = [r["name"] for r in db.list_suppliers("knitting_unit")]
        knitting_cb.set_completion_list(knitting_units)

        ttk.Label(dialog, text="Dyeing Unit:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        dyeing_cb = AutocompleteCombobox(dialog, width=30)
        dyeing_cb.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        dyeing_units = [r["name"] for r in db.list_suppliers("dyeing_unit")]
        dyeing_cb.set_completion_list(dyeing_units)

        def save_batch():
            batch_num = batch_e.get().strip()
            lots = lots_e.get().strip()
            fabric_type = fabric_cb.get().strip()
            has_rib = rib_var.get()
            has_collar = collar_var.get()
            knitting_unit = knitting_cb.get().strip()
            dyeing_unit = dyeing_cb.get().strip()

            if not batch_num or not lots or not knitting_unit or not fabric_type:
                messagebox.showwarning("Missing Fields", "Batch Number, Number of Lots, Knitting Unit, and Fabric Type are required.")
                return

            try:
                lots_int = int(lots)
                if lots_int <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Number of Lots must be a positive integer.")
                return

            knitting_id = db.get_supplier_id_by_name(knitting_unit, "knitting_unit")
            if not knitting_id:
                messagebox.showerror("Invalid Unit", f"Knitting unit '{knitting_unit}' not found.")
                return

            dyeing_id = db.get_supplier_id_by_name(dyeing_unit, "dyeing_unit") if dyeing_unit else None
            if dyeing_unit and not dyeing_id:
                messagebox.showerror("Invalid Unit", f"Dyeing unit '{dyeing_unit}' not found.")
                return

            fabric_type_id = db.get_fabric_type_id_by_name(fabric_type)
            if not fabric_type_id:
                messagebox.showerror("Invalid Fabric", f"Fabric type '{fabric_type}' not found.")
                return

            composition = f"Rib: {has_rib}, Collar: {has_collar}"
            db.create_batch(batch_num, knitting_id, fabric_type_id, lots_int, composition, dyeing_id)
            messagebox.showinfo("Success", f"Batch '{batch_num}' created with {lots_int} lots.")
            dialog.destroy()
            self.refresh_lists()
            if self.controller and hasattr(self.controller, "fabricators_frame"):
                self.controller.fabricators_frame.build_tabs()

        ttk.Button(dialog, text="Save", command=save_batch).grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=8, column=0, columnspan=2, pady=5)

    def reload_dyeing_outputs(self):
        for r in self.dye_tree.get_children():
            self.dye_tree.delete(r)
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT d.id, l.lot_no as lot_id, s.name as unit, d.returned_date, d.returned_qty_kg, d.returned_qty_rolls, d.notes
                FROM dyeing_outputs d
                LEFT JOIN lots l ON d.lot_id = l.id
                LEFT JOIN suppliers s ON d.dyeing_unit_id = s.id
                ORDER BY d.returned_date DESC
            """)
            for row in cur.fetchall():
                display_date = db.db_to_ui_date(row["returned_date"])
                self.dye_tree.insert("", "end", iid=row["id"], values=(
                    row["lot_id"], row["unit"], display_date, row["returned_qty_kg"], row["returned_qty_rolls"], row["notes"]
                ))

    def save_dyeing(self):
        lot_no = self.dyeing_lot_e.get().strip()
        unit = self.dyeing_unit_cb.get().strip()
        returned_date = self.returned_date_e.get().strip()
        try:
            kg = float(self.returned_kg_e.get().strip() or 0)
            rolls = int(self.returned_rolls_e.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid", "Qty (kg/rolls) must be numeric")
            return

        if kg <= 0 and rolls <= 0:
            messagebox.showwarning("Invalid Quantity", "At least one of Qty (kg) or Qty (rolls) must be greater than 0")
            return

        notes = self.returned_notes_e.get().strip()
        if not lot_no or not unit:
            messagebox.showwarning("Missing", "Please fill required fields: Lot ID, Dyeing Unit")
            return

        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM suppliers WHERE name=? AND type='dyeing_unit'", (unit,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("Invalid Unit", f"Dyeing unit '{unit}' not found")
                return
            unit_id = row["id"]
            lot_id = db.get_lot_id_by_no(lot_no)
            if lot_id is None:
                messagebox.showerror("Invalid Lot", f"Lot '{lot_no}' does not exist. Create it via the 'Create Batch' dialog first.")
                return

            # Fetch batch and fabric type to validate yarn composition
            cur.execute("""
                SELECT b.id AS batch_id, b.fabric_type_id
                FROM lots l
                JOIN batches b ON l.batch_id = b.id
                WHERE l.lot_no = ?
            """, (lot_no,))
            batch_row = cur.fetchone()
            if not batch_row:
                messagebox.showerror("Invalid Lot", f"Lot '{lot_no}' is not associated with any batch.")
                return
            batch_id = batch_row["batch_id"]
            fabric_type_id = batch_row["fabric_type_id"]

            # Validate yarn quantity against fabric composition
            cur.execute("""
                SELECT yc.yarn_type, yc.ratio
                FROM fabric_yarn_composition yc
                WHERE yc.fabric_type_id = ?
            """, (fabric_type_id,))
            compositions = cur.fetchall()
            if not compositions:
                messagebox.showwarning("No Composition", f"No yarn composition defined for the fabric type of batch '{batch_id}'. Proceed with caution.")
            else:
                total_purchased_kg = 0
                cur.execute("SELECT SUM(qty_kg) AS total FROM purchases WHERE batch_id = ? AND lot_no = ?", (db.get_batch_ref_by_id(batch_id), lot_no))
                total_purchased_kg_row = cur.fetchone()
                total_purchased_kg = total_purchased_kg_row["total"] or 0
                for comp in compositions:
                    yarn_type = comp["yarn_type"]
                    ratio = comp["ratio"]
                    expected_kg = total_purchased_kg * (ratio / 100)
                    if kg > expected_kg:
                        messagebox.showwarning("Over Allocation", f"Returned kg ({kg}) exceeds expected kg ({expected_kg}) for yarn '{yarn_type}' based on composition.")
                        return

            # Record dyeing output
            try:
                if self.selected_dyeing_id:
                    cur.execute("""
                        UPDATE dyeing_outputs
                        SET lot_id=?, dyeing_unit_id=?, returned_date=?, returned_qty_kg=?, returned_qty_rolls=?, notes=?
                        WHERE id=?
                    """, (lot_id, unit_id, db.ui_to_db_date(returned_date), kg, rolls, notes, self.selected_dyeing_id))
                else:
                    cur.execute("""
                        INSERT INTO dyeing_outputs (lot_id, dyeing_unit_id, returned_date, returned_qty_kg, returned_qty_rolls, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (lot_id, unit_id, db.ui_to_db_date(returned_date), kg, rolls, notes))
                    dyeing_id = cur.lastrowid
                    db.record_dyeing_output(dyeing_id, lot_id)  # Trigger yarn reduction
                    db.update_lot_status(lot_id, 'Dyed')  # Update status
            except ValueError as e:
                messagebox.showerror("Invalid Date", str(e))
                return

            conn.commit()

        self.clear_dyeing_form()
        self.selected_dyeing_id = None
        self.reload_dyeing_outputs()

        # Notify controller to update statuses
        if self.controller and hasattr(self.controller, "on_dyeing_output_recorded"):
            self.controller.on_dyeing_output_recorded(lot_id)

        if self.controller and hasattr(self.controller, "fabricators_frame"):
            self.controller.fabricators_frame.build_tabs()

    def clear_dyeing_form(self):
        self.dyeing_lot_e.delete(0, tk.END)
        self.dyeing_unit_cb.set("")
        self.returned_date_e.delete(0, tk.END)
        self.returned_date_e.insert(0, datetime.today().strftime("%d/%m/%Y"))
        self.returned_kg_e.delete(0, tk.END)
        self.returned_rolls_e.delete(0, tk.END)
        self.returned_notes_e.delete(0, tk.END)
        self.selected_dyeing_id = None

    def show_net_price(self):
        batch_id = self.batch_e.get().strip()
        if batch_id:
            price = db.calculate_net_price(batch_id)
            messagebox.showinfo("Net Price", f"Total Cost: ${price:.2f}")
        else:
            messagebox.showwarning("Missing", "Enter a Batch ID")

    def on_purchase_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        purchase_id = int(item[0])
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,))
            row = cur.fetchone()
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
        self.rib_collar_var.set(False)  # Reset Rib/Collar checkbox (no stored state yet)
        self._last_purchase_defaults.update({
            "date": self.date_e.get(),
            "batch": self.batch_e.get(),
            "supplier": self.supplier_cb.get(),
            "yarn": self.yarn_cb.get(),
            "price": self.price_e.get(),
            "delivered": self.delivered_cb.get(),
        })

    def on_dyeing_double_click(self, event):
        item = self.dye_tree.selection()
        if not item:
            return
        dyeing_id = int(item[0])
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT d.*, s.name as unit_name FROM dyeing_outputs d LEFT JOIN suppliers s ON d.dyeing_unit_id=s.id WHERE d.id=?", (dyeing_id,))
                row = cur.fetchone()
            if not row:
                return
            self.selected_dyeing_id = dyeing_id
            self.dyeing_lot_e.delete(0, tk.END)
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT lot_no FROM lots WHERE id=?", (row["lot_id"],))
                lot_row = cur.fetchone()
            if lot_row:
                self.dyeing_lot_e.insert(0, lot_row["lot_no"])
            self.dyeing_unit_cb.set(row["unit_name"])
            self.returned_date_e.delete(0, tk.END)
            self.returned_date_e.insert(0, db.db_to_ui_date(row["returned_date"]))
            self.returned_kg_e.delete(0, tk.END)
            self.returned_kg_e.insert(0, row["returned_qty_kg"])
            self.returned_rolls_e.delete(0, tk.END)
            self.returned_rolls_e.insert(0, row["returned_qty_rolls"])
            self.returned_notes_e.delete(0, tk.END)
            self.returned_notes_e.insert(0, row["notes"])
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load dyeing output: {str(e)}")
            self.selected_dyeing_id = None
