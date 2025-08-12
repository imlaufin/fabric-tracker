import tkinter as tk
from tkinter import ttk
import db


def lighten_color(hex_color, factor=0.85):
    """Lighten the given hex color for row backgrounds."""
    if not hex_color or not hex_color.startswith("#"):
        return ""
    try:
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(int(min(255, c + (255 - c) * (1 - factor))) for c in rgb)
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
    except:
        return ""


class FabricatorsFrame(ttk.Notebook):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.tabs_by_name = {}
        self.build_tabs()

    def build_tabs(self):
        # Remove existing tabs first
        for tab_id in self.tabs():
            self.forget(tab_id)
        self.tabs_by_name.clear()

        fabricators = db.list_suppliers()  # Now returns name, type, color_code
        for fab in fabricators:
            if fab["type"] == "knitting_unit":
                frame = KnittingUnitFrame(self, fab, self.controller)
            elif fab["type"] == "dyeing_unit":
                frame = DyeingUnitFrame(self, fab)
            else:
                continue
            self.add(frame, text=fab["name"])
            self.tabs_by_name[fab["name"]] = frame

    def open_dyeing_tab_for_batch(self, dyeer_name, batch_ref):
        """Switch to dyeing tab and filter to that batch."""
        if dyeer_name in self.tabs_by_name:
            self.select(self.tabs_by_name[dyeer_name])
            frame = self.tabs_by_name[dyeer_name]
            if hasattr(frame, "filter_by_batch"):
                frame.filter_by_batch(batch_ref)


class KnittingUnitFrame(ttk.Frame):
    def __init__(self, parent, fabricator, controller):
        super().__init__(parent)
        self.fabricator = fabricator
        self.controller = controller
        self.tint_color = lighten_color(fabricator["color_code"])
        self.build_ui()
        self.load_data()

    def build_ui(self):
        ttk.Label(self, text=f"Knitting Unit — {self.fabricator['name']}",
                  font=("Arial", 12, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("date", "batch", "lot", "yarn", "kg", "rolls"), show="headings")
        for col, txt, w in [
            ("date", "Date", 90),
            ("batch", "Batch", 80),
            ("lot", "Lot", 80),
            ("yarn", "Yarn Type", 120),
            ("kg", "Qty (kg)", 80),
            ("rolls", "Qty (rolls)", 90)
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.tag_configure("tinted", background=self.tint_color)

        self.tree.bind("<Double-1>", self.open_in_dyeing)

        self.summary_label = ttk.Label(self, text="Net Yarn Stock: 0 kg, 0 rolls",
                                       font=("Arial", 10, "bold"))
        self.summary_label.pack(pady=4)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = db.get_connection()
        rows = conn.execute("""
            SELECT date, batch_id, lot_no, yarn_type, qty_kg, qty_rolls
            FROM purchases
            WHERE delivered_to=?
            ORDER BY date
        """, (self.fabricator["name"],)).fetchall()
        conn.close()

        total_kg = total_rolls = 0
        for r in rows:
            self.tree.insert("", "end", values=(
                db.db_to_ui_date(r["date"]),
                r["batch_id"] or "",
                r["lot_no"] or "",
                r["yarn_type"] or "",
                r["qty_kg"] or 0,
                r["qty_rolls"] or 0
            ), tags=("tinted",))
            total_kg += r["qty_kg"] or 0
            total_rolls += r["qty_rolls"] or 0

        self.summary_label.config(text=f"Net Yarn Stock: {total_kg} kg, {total_rolls} rolls")

    def open_in_dyeing(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        batch_id = vals[1]
        # Placeholder: in a real DB, you'd also store which dyeer is linked to this batch
        dyeer_name = "Sample Dyeing Unit"
        self.controller.open_dyeing_tab_for_batch(dyeer_name, batch_id)


class DyeingUnitFrame(ttk.Frame):
    def __init__(self, parent, fabricator):
        super().__init__(parent)
        self.fabricator = fabricator
        self.tint_color = lighten_color(fabricator["color_code"])
        self.build_ui()
        self.load_data()

    def build_ui(self):
        ttk.Label(self, text=f"Dyeing Unit — {self.fabricator['name']}",
                  font=("Arial", 12, "bold")).pack(pady=5)

        self.pending_tree = ttk.Treeview(self,
                                         columns=("batch", "lot", "before_kg", "after_kg", "short_kg", "short_pct"),
                                         show="headings")
        for col, txt, w in [
            ("batch", "Batch", 80),
            ("lot", "Lot", 80),
            ("before_kg", "Before (kg)", 90),
            ("after_kg", "After (kg)", 90),
            ("short_kg", "Shortage (kg)", 110),
            ("short_pct", "Shortage (%)", 110)
        ]:
            self.pending_tree.heading(col, text=txt)
            self.pending_tree.column(col, width=w)
        self.pending_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.pending_tree.tag_configure("high_short", background="#ffcccc")
        self.pending_tree.tag_configure("tinted", background=self.tint_color)

    def load_data(self):
        for row in self.pending_tree.get_children():
            self.pending_tree.delete(row)

        # Placeholder: This should join knitting dispatches with dyeing returns
        # For now, just empty data to avoid crashes
        sample_rows = [
            ("200", "200/1", 160, 152, 8, 5.0),
            ("200", "200/2", 160, 150, 10, 6.25),
        ]
        for batch, lot, before, after, short_kg, short_pct in sample_rows:
            tags = ("tinted",)
            if short_pct > 5:
                tags = ("high_short",)
            self.pending_tree.insert("", "end", values=(
                batch, lot, before, after, short_kg, f"{short_pct:.2f}%"
            ), tags=tags)

    def filter_by_batch(self, batch_ref):
        for row in self.pending_tree.get_children():
            vals = self.pending_tree.item(row, "values")
            if vals[0] != batch_ref:
                self.pending_tree.detach(row)
