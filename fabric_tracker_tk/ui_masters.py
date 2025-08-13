# ui_masters.py
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import db

FAB_TYPES = [("Yarn Supplier", "yarn_supplier"), ("Knitting Unit", "knitting_unit"), ("Dyeing Unit", "dyeing_unit")]

class MastersFrame(ttk.Frame):
    def __init__(self, parent, controller=None, on_change_callback=None):
        super().__init__(parent)
        self.controller = controller
        self.on_change_callback = on_change_callback
        self.chosen_color = ""
        self.build_ui()
        self.load_suppliers()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(top, width=30)
        self.name_entry.grid(row=0, column=1, padx=5)

        ttk.Label(top, text="Type:").grid(row=0, column=2, sticky="w")
        self.type_cb = ttk.Combobox(top, values=[t[0] for t in FAB_TYPES], state="readonly", width=18)
        self.type_cb.grid(row=0, column=3, padx=5)
        self.type_cb.current(0)

        ttk.Label(top, text="Color:").grid(row=0, column=4, sticky="w")
        self.color_btn = ttk.Button(top, text="Choose", command=self.choose_color)
        self.color_btn.grid(row=0, column=5, padx=5)

        ttk.Button(top, text="Add / Update", command=self.add_or_update).grid(row=0, column=6, padx=8)
        ttk.Button(top, text="Reload Fabricators", command=self.reload_cb_and_notify).grid(row=0, column=7, padx=8)

        # Treeview for list of masters
        self.tree = ttk.Treeview(self, columns=("name", "type", "color"), show="headings", height=10)
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("color", text="Color")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side="left")
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=8)

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose fabricator color")
        if color and color[1]:
            self.chosen_color = color[1]
            self.color_btn.configure(text=self.chosen_color, background=self.chosen_color)

    def add_or_update(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return

        type_label = self.type_cb.get()
        type_map = {t[0]: t[1] for t in FAB_TYPES}
        mtype = type_map.get(type_label, "yarn_supplier")
        color_hex = getattr(self, "chosen_color", "")

        db.add_master(name, mtype, color_hex)
        db.update_master_color_and_type(name, mtype, color_hex)
        messagebox.showinfo("Saved", f"{name} saved/updated.")

        # Reset form for next entry
        self.name_entry.delete(0, tk.END)
        self.type_cb.current(0)
        self.chosen_color = ""
        self.color_btn.configure(text="Choose", background=None)

        self.load_suppliers()
        self.reload_cb_and_notify()

    def load_suppliers(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, type, color_code FROM suppliers ORDER BY name")
        for row in cur.fetchall():
            type_label = next((t[0] for t in FAB_TYPES if t[1] == row["type"]), row["type"])
            self.tree.insert("", "end", values=(row["name"], type_label, row["color_code"] or ""))
        conn.close()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM suppliers WHERE name=?", (name,))
            conn.commit()
            conn.close()
            self.load_suppliers()
            self.reload_cb_and_notify()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])["values"]
        name, typelabel, color = vals
        # prefill form
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)

        labels = [t[0] for t in FAB_TYPES]
        try:
            self.type_cb.current(labels.index(typelabel))
        except Exception:
            self.type_cb.current(0)

        self.chosen_color = color or ""
        self.color_btn.configure(text=color or "Choose", background=color or None)

    def reload_cb_and_notify(self):
        # Notify controller to rebuild fabricator tabs if provided
        if self.on_change_callback:
            self.on_change_callback()
