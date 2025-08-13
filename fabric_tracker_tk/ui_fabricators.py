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
        self.tx_tree.pack(fill="both", expand=True)

        # Batch Status
        batch_frame = ttk.LabelFrame(self, text="Batches & Status")
        batch_frame.pack(fill="x", padx=6, pady=6)
        self.batch_tree = ttk.Treeview(batch_frame, columns=("batch_ref","product","expected","delivered","pending"), show="headings", height=6)
        for col, text, w in zip(("batch_ref","product","expected","delivered","pending"), ["Batch","Product","Expected","Delivered","Pending"], [120,200,80,80,80]):
            self.batch_tree.heading(col, text=text)
            self.batch_tree.column(col, width=w)
        self.batch_tree.pack(fill="x", expand=True)
        self.batch_tree.bind("<Double-1>", self.on_batch_double)

        # Stock Summary
        summary_frame = ttk.LabelFrame(self, text="Yarn Stock Summary (Current balance)")
        summary_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.summary_tree = ttk.Treeview(summary_frame, columns=("yarn_type","balance_kg","balance_rolls"), show="headings", height=8)
        for col, text, w in zip(("yarn_type","balance_kg","balance_rolls"), ["Yarn Type","Balance (kg)","Balance (rolls)"], [200,120,120]):
            self.summary_tree.heading(col, text=text)
            self.summary_tree.column(col, width=w)
        self.summary_tree.pack(fill="both", expand=True)

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
            self.tx_tree.insert("", "end", values=(row["date"], row["supplier"], row["yarn_type"], row["qty_kg"], row["qty_rolls"], row["batch_id"], row["lot_no"]))
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
        if self.controller and hasattr(self.controller, "open_dyeing_tab_for_batch"):
            self.controller.open_dyeing_tab_for_batch(self.fabricator["name"], batch_ref)

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
        self.pending_tree.pack(fill="both", expand=True)

        completed_frame = ttk.LabelFrame(self, text="Completed Batches")
        completed_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.completed_tree = ttk.Treeview(completed_frame, columns=cols, show="headings", height=8)
        for c,h,w in zip(cols, headings, widths):
            self.completed_tree.heading(c, text=h)
            self.completed_tree.column(c, width=w)
        self.completed_tree.pack(fill="both", expand=True)

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
        lots = cur.fetchall()
        for lot in lots:
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
        lots = cur.fetchall()
        for lot in lots:
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
        for child in self.parent_nb.winfo_children():
            child.destroy()
        # Fetch all fabricators
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM fabricators ORDER BY name")
        fabricators = cur.fetchall()
        conn.close()
        # Create tabs
        self.tabs = {}
        kn_tab_frame = ttk.Frame(self.parent_nb)
        self.parent_nb.add(kn_tab_frame, text="Knitting Units")
        dy_tab_frame = ttk.Frame(self.parent_nb)
        self.parent_nb.add(dy_tab_frame, text="Dyeing Units")
        for f in fabricators:
            kn_tab = KnittingTab(kn_tab_frame, f, controller=self.controller)
            kn_tab.pack(fill="both", expand=True)
            dy_tab = DyeingTab(dy_tab_frame, f, controller=self.controller)
            dy_tab.pack(fill="both", expand=True)
            self.tabs[f["name"]] = {"knitting": kn_tab, "dyeing": dy_tab}

    def open_dyeing_tab_for_batch(self, fabricator_name, batch_ref):
        idx = self.parent_nb.index("end") - 1  # last tab is Dyeing Units
        self.parent_nb.select(idx)  # switch to Dyeing Units
        dy_tab = self.tabs.get(fabricator_name, {}).get("dyeing")
        if dy_tab:
            dy_tab.reload_all()
