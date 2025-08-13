# ui_fabricators.py
import tkinter as tk
from tkinter import ttk, messagebox
import db
from datetime import datetime

SHORTAGE_THRESHOLD_PERCENT = 5.0  # highlight threshold

def pastel_tint(hex_color, factor=0.85):
    """Return a lighter version of hex_color by mixing with white"""
    if not hex_color:
        return ""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r + (255 - r) * (1 - factor))
    g = int(g + (255 - g) * (1 - factor))
    b = int(b + (255 - b) * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"

class KnittingTab(ttk.Frame):
    def __init__(self, parent, fabricator_row, controller=None):
        super().__init__(parent)
        self.fabricator = fabricator_row
        self.controller = controller
        self.build_ui()
        self.reload_all()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=6)

        ttk.Label(top, text=f"Knitting Unit: {self.fabricator['name']}", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(top, text="New Batch", command=self.create_batch_dialog).pack(side="right", padx=4)
        ttk.Button(top, text="Refresh", command=self.reload_all).pack(side="right", padx=4)

        # Inward Transactions
        tx_frame = ttk.LabelFrame(self, text="Inward Transactions (Yarn received)")
        tx_frame.pack(fill="both", expand=True, padx=6, pady=6)

        cols = ("date", "supplier", "yarn_type", "qty_kg", "qty_rolls", "batch_id", "lot_no")
        self.tx_tree = ttk.Treeview(tx_frame, columns=cols, show="headings", height=8)
        for c, w, h in zip(cols, [100,150,150,90,90,90,120], ["Date","Supplier","Type","Kg","Rolls","Batch","Lot"]):
            self.tx_tree.heading(c, text=h)
            self.tx_tree.column(c, width=w)
        self.tx_tree.pack(fill="both", expand=True, side="left")

        # Add vertical scrollbar
        vsb = ttk.Scrollbar(tx_frame, orient="vertical", command=self.tx_tree.yview)
        vsb.pack(side="right", fill="y")
        self.tx_tree.configure(yscrollcommand=vsb.set)

        # Batch Status
        batch_frame = ttk.LabelFrame(self, text="Batches & Status")
        batch_frame.pack(fill="x", padx=6, pady=6)
        self.batch_tree = ttk.Treeview(batch_frame, columns=("batch_ref","product","expected","delivered","pending"), show="headings", height=6)
        for col, text, w in zip(("batch_ref","product","expected","delivered","pending"), ["Batch","Product","Expected","Delivered","Pending"], [120,200,80,80,80]):
            self.batch_tree.heading(col, text=text)
            self.batch_tree.column(col, width=w)
        self.batch_tree.pack(fill="x", expand=True, side="left")

        vsb2 = ttk.Scrollbar(batch_frame, orient="vertical", command=self.batch_tree.yview)
        vsb2.pack(side="right", fill="y")
        self.batch_tree.configure(yscrollcommand=vsb2.set)

        self.batch_tree.bind("<Double-1>", self.on_batch_double)

        # Stock Summary
        summary_frame = ttk.LabelFrame(self, text="Yarn Stock Summary (Current balance)")
        summary_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.summary_tree = ttk.Treeview(summary_frame, columns=("yarn_type","balance_kg","balance_rolls"), show="headings", height=8)
        for col, text, w in zip(("yarn_type","balance_kg","balance_rolls"), ["Yarn Type","Balance (kg)","Balance (rolls)"], [200,120,120]):
            self.summary_tree.heading(col, text=text)
            self.summary_tree.column(col, width=w)
        self.summary_tree.pack(fill="both", expand=True, side="left")

        vsb3 = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_tree.yview)
        vsb3.pack(side="right", fill="y")
        self.summary_tree.configure(yscrollcommand=vsb3.set)

    def reload_all(self):
        self.load_inward_transactions()
        self.load_batches()
        self.load_stock_summary()

    def load_inward_transactions(self):
        for r in self.tx_tree.get_children():
            self.tx_tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT date, supplier, yarn_type, qty_kg, qty_rolls, batch_id, lot_no
            FROM purchases
            WHERE delivered_to=? ORDER BY date DESC
        """, (self.fabricator["name"],))
        for row in cur.fetchall():
            display_date = row["date"]
            try:
                display_date = db.db_to_ui_date(row["date"])
            except Exception:
                pass
            self.tx_tree.insert("", "end", values=(display_date, row["supplier"], row["yarn_type"], row["qty_kg"], row["qty_rolls"], row["batch_id"], row["lot_no"]))
        conn.close()

    def load_batches(self):
        for r in self.batch_tree.get_children():
            self.batch_tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM batches WHERE fabricator_id=? ORDER BY created_at DESC", (self.fabricator["id"],))
        for b in cur.fetchall():
            cur.execute("SELECT COUNT(*) as cnt FROM purchases WHERE batch_id=? AND delivered_to=?", (b["batch_ref"], self.fabricator["name"]))
            delivered = cur.fetchone()["cnt"] or 0
            expected = b["expected_lots"] or 0
            pending = max(0, expected - delivered)
            self.batch_tree.insert("", "end", values=(b["batch_ref"], b["product_name"], expected, delivered, pending))
        conn.close()

    def on_batch_double(self, event):
        sel = self.batch_tree.selection()
        if not sel:
            return
        vals = self.batch_tree.item(sel[0])["values"]
        batch_ref = vals[0]
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT delivered_to FROM purchases WHERE batch_id=? AND delivered_to IS NOT NULL AND delivered_to != '' LIMIT 1", (batch_ref,))
        row = cur.fetchone()
        conn.close()
        if row and self.controller and hasattr(self.controller, "open_dyeing_tab_for_batch"):
            self.controller.open_dyeing_tab_for_batch(row["delivered_to"], batch_ref)

    def create_batch_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Create Batch")
        tk.Label(dialog, text="Batch ID:").grid(row=0, column=0)
        bid = tk.Entry(dialog); bid.grid(row=0, column=1)
        tk.Label(dialog, text="Product Name:").grid(row=1, column=0)
        pname = tk.Entry(dialog); pname.grid(row=1, column=1)
        tk.Label(dialog, text="Expected Lots:").grid(row=2, column=0)
        lots = tk.Entry(dialog); lots.grid(row=2, column=1)
        tk.Label(dialog, text="Composition (optional):").grid(row=3, column=0)
        comp = tk.Entry(dialog, width=40); comp.grid(row=3, column=1)

        def on_create():
            br = bid.get().strip()
            try:
                expected = int(lots.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Invalid", "Expected lots must be an integer")
                return
            if not br:
                messagebox.showerror("Invalid", "Batch ID required")
                return
            db.create_batch(br, self.fabricator["id"], pname.get().strip(), expected, comp.get().strip())
            self.load_batches()
            dialog.destroy()

        ttk.Button(dialog, text="Create", command=on_create).grid(row=4, column=0, columnspan=2, pady=6)

    def load_stock_summary(self):
        for r in self.summary_tree.get_children():
            self.summary_tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT yarn_type, SUM(qty_kg) as kg_sum, SUM(qty_rolls) as rolls_sum
            FROM purchases
            WHERE delivered_to=?
            GROUP BY yarn_type
        """, (self.fabricator["name"],))
        for r in cur.fetchall():
            self.summary_tree.insert("", "end", values=(r["yarn_type"], r["kg_sum"] or 0, r["rolls_sum"] or 0))
        conn.close()


class DyeingTab(ttk.Frame):
    def __init__(self, parent, fabricator_row, controller=None):
        super().__init__(parent)
        self.fabricator = fabricator_row
        self.controller = controller
        self.build_ui()
        self.reload_all()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text=f"Dyeing Unit: {self.fabricator['name']}", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.reload_all).pack(side="right")

        pending_frame = ttk.LabelFrame(self, text="Pending Batches")
        pending_frame.pack(fill="both", expand=True, padx=6, pady=6)
        cols = ("batch_ref","lot_no","type","orig_kg","orig_rolls","returned_kg","returned_rolls","short_kg","short_pct")
        headings = ["Batch","Lot","Type","Orig (kg)","Orig (rolls)","Returned (kg)","Returned (rolls)","Short (kg)","Short (%)"]
        widths = [80,120,80,100,100,100,100,90,90]
        self.pending_tree = ttk.Treeview(pending_frame, columns=cols, show="headings", height=8)
        for c,h,w in zip(cols, headings, widths):
            self.pending_tree.heading(c, text=h)
            self.pending_tree.column(c, width=w)
        self.pending_tree.pack(fill="both", expand=True, side="left")

        vsb = ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_tree.yview)
        vsb.pack(side="right", fill="y")
        self.pending_tree.configure(yscrollcommand=vsb.set)

        completed_frame = ttk.LabelFrame(self, text="Completed Batches")
        completed_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.completed_tree = ttk.Treeview(completed_frame, columns=cols, show="headings", height=8)
        for c,h,w in zip(cols, headings, widths):
            self.completed_tree.heading(c, text=h)
            self.completed_tree.column(c, width=w)
        self.completed_tree.pack(fill="both", expand=True, side="left")

        vsb2 = ttk.Scrollbar(completed_frame, orient="vertical", command=self.completed_tree.yview)
        vsb2.pack(side="right", fill="y")
        self.completed_tree.configure(yscrollcommand=vsb2.set)

    def reload_all(self):
        self.load_pending()
        self.load_completed()

    def load_pending(self):
        for r in self.pending_tree.get_children():
            self.pending_tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.batch_id, p.lot_no, p.yarn_type, SUM(p.qty_kg) as orig_kg, SUM(p.qty_rolls) as orig_rolls
            FROM purchases p
            WHERE p.delivered_to=?
            GROUP BY p.batch_id, p.lot_no, p.yarn_type
        """, (self.fabricator["name"],))
        for lot in cur.fetchall():
            batch_ref = lot["batch_id"]
            lot_no = lot["lot_no"]
            yarn_type = lot["yarn_type"]
            orig_kg = lot["orig_kg"] or 0
            orig_rolls = lot["orig_rolls"] or 0
            cur.execute("""
                SELECT SUM(d.returned_qty_kg) as rkg, SUM(d.returned_qty_rolls) as rrolls
                FROM dyeing_outputs d
                JOIN lots l ON d.lot_id = l.id
                WHERE l.lot_no=? AND d.dyeing_unit_id=?
            """, (lot_no, self.fabricator["id"]))
            out = cur.fetchone()
            rkg = out["rkg"] or 0
            rrolls = out["rrolls"] or 0
            short_kg = orig_kg - rkg
            short_pct = (short_kg / orig_kg * 100) if orig_kg>0 else 0
            tag = "short" if short_pct > SHORTAGE_THRESHOLD_PERCENT else ""
            self.pending_tree.insert("", "end", values=(batch_ref, lot_no, yarn_type, orig_kg, orig_rolls, rkg, rrolls, round(short_kg,2), round(short_pct,2)), tags=(tag,))
        self.pending_tree.tag_configure("short", background="#ffcccc")
        conn.close()

    def load_completed(self):
        for r in self.completed_tree.get_children():
            self.completed_tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.batch_id, p.lot_no, p.yarn_type, SUM(p.qty_kg) as orig_kg, SUM(p.qty_rolls) as orig_rolls
            FROM purchases p
            WHERE p.delivered_to=?
            GROUP BY p.batch_id, p.lot_no, p.yarn_type
        """, (self.fabricator["name"],))
        for lot in cur.fetchall():
            batch_ref = lot["batch_id"]
            lot_no = lot["lot_no"]
            orig_kg = lot["orig_kg"] or 0
            orig_rolls = lot["orig_rolls"] or 0
            cur.execute("""
                SELECT SUM(d.returned_qty_kg) as rkg, SUM(d.returned_qty_rolls) as rrolls
                FROM dyeing_outputs d
                JOIN lots l ON d.lot_id = l.id
                WHERE l.lot_no=? AND d.dyeing_unit_id=?
            """, (lot_no, self.fabricator["id"]))
            out = cur.fetchone()
            rkg = out["rkg"] or 0
            rrolls = out["rrolls"] or 0
            if rrolls >= orig_rolls and orig_rolls>0:
                short_kg = orig_kg - rkg
                short_pct = (short_kg / orig_kg * 100) if orig_kg>0 else 0
                tag = "short" if short_pct>SHORTAGE_THRESHOLD_PERCENT else ""
                self.completed_tree.insert("", "end", values=(batch_ref, lot_no, "", orig_kg, orig_rolls, rkg, rrolls, round(short_kg,2), round(short_pct,2)), tags=(tag,))
        self.completed_tree.tag_configure("short", background="#ffcccc")
        conn.close()


class FabricatorsFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.build_tabs()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Fabricators").pack(side="left")
        ttk.Button(top, text="Reload Tabs", command=self.build_tabs).pack(side="right")
        self.parent_nb = ttk.Notebook(self)
        self.parent_nb.pack(fill="both", expand=True)

    def build_tabs(self):
        # remove all previous content
        for child in self.parent_nb.winfo_children():
            child.destroy()

        # Knitting and Dyeing parent frames
        kn_parent = ttk.Frame(self.parent_nb)
        dy_parent = ttk.Frame(self.parent_nb)
        self.parent_nb.add(kn_parent, text="Knitting Units")
        self.parent_nb.add(dy_parent, text="Dyeing Units")

        # create sub-notebooks
        kn_nb = ttk.Notebook(kn_parent)
        kn_nb.pack(fill="both", expand=True)
        dy_nb = ttk.Notebook(dy_parent)
        dy_nb.pack(fill="both", expand=True)

        self.kn_nb = kn_nb
        self.dy_nb = dy_nb
        self.tabs = {}

        # fetch fabricators
        knitting_units = db.get_fabricators("knitting_unit")
        dyeing_units = db.get_fabricators("dyeing_unit")

        for r in knitting_units:
            tab = KnittingTab(kn_nb, r, controller=self.controller)
            kn_nb.add(tab, text=r["name"])
            if r["name"] not in self.tabs:
                self.tabs[r["name"]] = {}
            self.tabs[r["name"]]["knitting"] = tab

        for r in dyeing_units:
            tab = DyeingTab(dy_nb, r, controller=self.controller)
            dy_nb.add(tab, text=r["name"])
            if r["name"] not in self.tabs:
                self.tabs[r["name"]] = {}
            self.tabs[r["name"]]["dyeing"] = tab

    def open_dyeing_tab_for_batch(self, fabricator_name, batch_ref):
        for ptab in self.parent_nb.tabs():
            if self.parent_nb.tab(ptab, "text") == "Dyeing Units":
                self.parent_nb.select(ptab)
                break

        if not hasattr(self, "dy_nb"):
            return
        for st in self.dy_nb.tabs():
            if self.dy_nb.tab(st, "text") == fabricator_name:
                self.dy_nb.select(st)
                widget = self.dy_nb.nametowidget(st)
                if hasattr(widget, "reload_all"):
                    widget.reload_all()
                try:
                    for item in widget.pending_tree.get_children():
                        vals = widget.pending_tree.item(item)["values"]
                        if vals and vals[0] == batch_ref:
                            widget.pending_tree.selection_set(item)
                            widget.pending_tree.see(item)
                    for item in widget.completed_tree.get_children():
                        vals = widget.completed_tree.item(item)["values"]
                        if vals and vals[0] == batch_ref:
                            widget.completed_tree.selection_set(item)
                            widget.completed_tree.see(item)
                except Exception:
                    pass
                return
        messagebox.showinfo("Not found", f"Dyeing unit '{fabricator_name}' not found.")
