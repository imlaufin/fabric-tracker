import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import db

MASTER_TYPES = ["yarn_supplier", "knitting_unit", "dyeing_unit"]

class MastersFrame(ttk.Frame):
    def __init__(self, parent, on_masters_changed=None):
        super().__init__(parent)
        self.on_masters_changed = on_masters_changed
        self.build_ui()
        self.load_data()

    def build_ui(self):
        frm_top = ttk.Frame(self)
        frm_top.pack(fill="x", pady=5)

        ttk.Label(frm_top, text="Name:").grid(row=0, column=0, padx=5, pady=2)
        self.entry_name = ttk.Entry(frm_top)
        self.entry_name.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frm_top, text="Type:").grid(row=0, column=2, padx=5, pady=2)
        self.combo_type = ttk.Combobox(frm_top, values=MASTER_TYPES, state="readonly")
        self.combo_type.grid(row=0, column=3, padx=5, pady=2)
        self.combo_type.set(MASTER_TYPES[0])

        ttk.Label(frm_top, text="Color:").grid(row=0, column=4, padx=5, pady=2)
        self.btn_color = tk.Button(frm_top, text="Pick Color", command=self.pick_color)
        self.btn_color.grid(row=0, column=5, padx=5, pady=2)
        self.selected_color = ""

        ttk.Button(frm_top, text="Add / Update", command=self.add_update_master).grid(row=0, column=6, padx=5, pady=2)
        ttk.Button(frm_top, text="Delete", command=self.delete_selected).grid(row=0, column=7, padx=5, pady=2)

        # Treeview
        columns = ("name", "type", "color")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("color", text="Color")

        self.tree.column("name", width=200)
        self.tree.column("type", width=120)
        self.tree.column("color", width=80)

        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Pick Fabricator Color")
        if color_code and color_code[1]:
            self.selected_color = color_code[1]  # hex
            self.btn_color.configure(bg=self.selected_color)

    def add_update_master(self):
        name = self.entry_name.get().strip()
        mtype = self.combo_type.get()
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return
        if not mtype:
            mtype = "yarn_supplier"
        db.add_master(name, mtype, self.selected_color)
        db.update_master_color_and_type(name, mtype, self.selected_color)
        self.load_data()
        if callable(self.on_masters_changed):
            self.on_masters_changed()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
            db.delete_master_by_name(name)
            self.load_data()
            if callable(self.on_masters_changed):
                self.on_masters_changed()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = db.list_suppliers()
        for r in rows:
            self.tree.insert("", "end", values=(r["name"], r["type"], r["color_code"]))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, vals[0])
        self.combo_type.set(vals[1])
        self.selected_color = vals[2] or ""
        self.btn_color.configure(bg=self.selected_color if self.selected_color else "SystemButtonFace")
