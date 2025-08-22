import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from fabric_tracker_tk import db

MASTER_TYPES = [
    ("Yarn Supplier", "yarn_supplier"),
    ("Knitting Unit", "knitting_unit"),import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from fabric_tracker_tk import db

MASTER_TYPES = [
    ("Yarn Supplier", "yarn_supplier"),
    ("Knitting Unit", "knitting_unit"),
    ("Dyeing Unit", "dyeing_unit"),
    ("Yarn Type", "yarn_type"),
    ("Fabric Type", "fabric_type")  # future-proof
]

class MastersFrame(ttk.Frame):
    def __init__(self, parent, controller=None, on_change_callback=None):
        super().__init__(parent)
        self.controller = controller
        self.on_change_callback = on_change_callback
        self.chosen_color = ""
        self.color_imgs = {}  # store small color rectangles for treeview
        # Set theme to support background colors
        style = ttk.Style()
        style.theme_use("clam")
        print(f"[DEBUG] Tkinter theme set to: {style.theme_use()}")
        self.build_ui()
        self.load_masters()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(top, width=30)
        self.name_entry.grid(row=0, column=1, padx=5)

        ttk.Label(top, text="Type:").grid(row=0, column=2, sticky="w")
        self.type_cb = ttk.Combobox(top, values=[t[0] for t in MASTER_TYPES], state="readonly", width=18)
        self.type_cb.grid(row=0, column=3, padx=5)
        self.type_cb.current(0)

        ttk.Label(top, text="Color:").grid(row=0, column=4, sticky="w")
        self.color_btn = ttk.Button(top, text="Choose", command=self.choose_color)
        self.color_btn.grid(row=0, column=5, padx=5)

        ttk.Button(top, text="Add / Update", command=self.add_or_update).grid(row=0, column=6, padx=8)
        ttk.Button(top, text="Reload Masters", command=self.reload_cb_and_notify).grid(row=0, column=7, padx=8)

        # Treeview
        self.tree = ttk.Treeview(self, columns=("name", "type", "color"), show="headings", height=10)
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("color", text="Color")
        self.tree.column("name", width=200)
        self.tree.column("type", width=150)
        self.tree.column("color", width=100)  # Ensure color column is visible
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Right-click context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit", command=self.edit_selected)
        self.menu.add_command(label="Delete", command=self.delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Bottom buttons
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side="left")
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=8)

    def show_context_menu(self, event):
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose color")
        if color and color[1]:
            self.chosen_color = color[1]  # e.g., "#800040"
            style_name = "Custom.TButton"
            s = ttk.Style()
            s.configure(style_name, background=self.chosen_color, foreground="white")
            print(f"[DEBUG] Configuring style {style_name} with background={self.chosen_color}")
            self.color_btn.configure(text=self.chosen_color, style=style_name)

    def add_or_update(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return

        type_label = self.type_cb.get()
        type_map = {t[0]: t[1] for t in MASTER_TYPES}
        mtype = type_map.get(type_label, "yarn_supplier")
        color_hex = getattr(self, "chosen_color", "")

        if mtype in ("yarn_supplier", "knitting_unit", "dyeing_unit"):
            print(f"[DEBUG] Adding/Updating master: name={name}, type={mtype}, color={color_hex}")
            db.add_master(name, mtype, color_hex)
            db.update_master_color_and_type(name, mtype, color_hex)
        elif mtype == "yarn_type":
            db.add_yarn_type(name)
        elif mtype == "fabric_type":
            db.add_fabric_type(name)

        messagebox.showinfo("Saved", f"{name} saved/updated.")

        # Reset inputs
        self.name_entry.delete(0, tk.END)
        self.type_cb.current(0)
        self.chosen_color = ""
        self.color_btn.configure(text="Choose", style="TButton")

        self.load_masters()
        self.reload_cb_and_notify()

    def load_masters(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        self.color_imgs.clear()

        for t in MASTER_TYPES:
            mtype = t[1]
            rows = []

            if mtype in ("yarn_supplier", "knitting_unit", "dyeing_unit"):
                rows = db.list_suppliers(mtype)
            elif mtype == "yarn_type":
                rows = [{"name": n, "type": mtype, "color_code": ""} for n in db.list_yarn_types()]
            elif mtype == "fabric_type":
                rows = [{"name": n, "type": mtype, "color_code": ""} for n in db.list_fabric_types()]

            print(f"[DEBUG] Loading masters for type={mtype}, rows={rows}")
            for row in rows:
                try:
                    name = row["name"]
                    typ = row["type"] if "type" in row.keys() else mtype
                    color = row["color_code"] if "color_code" in row.keys() else ""
                    type_label = next((x[0] for x in MASTER_TYPES if x[1] == typ), typ)

                    print(f"[DEBUG] Inserting row: name={name}, type={type_label}, color={color}")
                    if color:
                        img = tk.PhotoImage(width=16, height=16)
                        img.put(color, to=(0, 0, 16, 16))
                        self.color_imgs[name] = img
                        self.tree.insert("", "end", values=(name, type_label, color), image=img)
                    else:
                        self.tree.insert("", "end", values=(name, type_label, ""))
                except KeyError as e:
                    print(f"[DEBUG] KeyError in load_masters: {e}, row={row}")
                    continue

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name, typelabel, _ = self.tree.item(sel[0])["values"]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            success = False
            type_map = {t[0]: t[1] for t in MASTER_TYPES}
            mtype = type_map.get(typelabel, "yarn_supplier")
            if mtype in ("yarn_supplier", "knitting_unit", "dyeing_unit"):
                success = db.delete_master_by_name(name)
            elif mtype == "yarn_type":
                success = db.delete_yarn_type(name)  # Use new function
            elif mtype == "fabric_type":
                success = db.delete_fabric_type(name)  # Assume similar function exists

            if not success:
                messagebox.showwarning("Cannot Delete", f"{name} cannot be deleted (maybe in use).")
            self.load_masters()
            self.reload_cb_and_notify()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name, typelabel, color = self.tree.item(sel[0])["values"]

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)

        labels = [t[0] for t in MASTER_TYPES]
        try:
            self.type_cb.current(labels.index(typelabel))
        except Exception:
            self.type_cb.current(0)

        if typelabel in ("Yarn Supplier", "Knitting Unit", "Dyeing Unit"):
            self.chosen_color = color or ""
            style_name = "Custom.TButton" if self.chosen_color else "TButton"
            if self.chosen_color:
                s = ttk.Style()
                s.configure(style_name, background=self.chosen_color, foreground="white")
                print(f"[DEBUG] Configuring style {style_name} with background={self.chosen_color} in edit_selected")
            self.color_btn.configure(text=color or "Choose", style=style_name)
        else:
            self.chosen_color = ""
            self.color_btn.configure(text="Choose", style="TButton")

    def reload_cb_and_notify(self):
        if self.on_change_callback:
            self.on_change_callback()
    ("Dyeing Unit", "dyeing_unit"),
    ("Yarn Type", "yarn_type"),
    ("Fabric Type", "fabric_type")  # future-proof
]

class MastersFrame(ttk.Frame):
    def __init__(self, parent, controller=None, on_change_callback=None):
        super().__init__(parent)
        self.controller = controller
        self.on_change_callback = on_change_callback
        self.chosen_color = ""
        self.color_imgs = {}  # store small color rectangles for treeview
        # Set theme to support background colors
        style = ttk.Style()
        style.theme_use("clam")
        print(f"[DEBUG] Tkinter theme set to: {style.theme_use()}")
        self.build_ui()
        self.load_masters()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(top, width=30)
        self.name_entry.grid(row=0, column=1, padx=5)

        ttk.Label(top, text="Type:").grid(row=0, column=2, sticky="w")
        self.type_cb = ttk.Combobox(top, values=[t[0] for t in MASTER_TYPES], state="readonly", width=18)
        self.type_cb.grid(row=0, column=3, padx=5)
        self.type_cb.current(0)

        ttk.Label(top, text="Color:").grid(row=0, column=4, sticky="w")
        self.color_btn = ttk.Button(top, text="Choose", command=self.choose_color)
        self.color_btn.grid(row=0, column=5, padx=5)

        ttk.Button(top, text="Add / Update", command=self.add_or_update).grid(row=0, column=6, padx=8)
        ttk.Button(top, text="Reload Masters", command=self.reload_cb_and_notify).grid(row=0, column=7, padx=8)

        # Treeview
        self.tree = ttk.Treeview(self, columns=("name", "type", "color"), show="headings", height=10)
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("color", text="Color")
        self.tree.column("name", width=200)
        self.tree.column("type", width=150)
        self.tree.column("color", width=100)  # Ensure color column is visible
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Right-click context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit", command=self.edit_selected)
        self.menu.add_command(label="Delete", command=self.delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Bottom buttons
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side="left")
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=8)

    def show_context_menu(self, event):
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose color")
        if color and color[1]:
            self.chosen_color = color[1]  # e.g., "#800040"
            style_name = "Custom.TButton"
            s = ttk.Style()
            s.configure(style_name, background=self.chosen_color, foreground="white")
            print(f"[DEBUG] Configuring style {style_name} with background={self.chosen_color}")
            self.color_btn.configure(text=self.chosen_color, style=style_name)

    def add_or_update(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return

        type_label = self.type_cb.get()
        type_map = {t[0]: t[1] for t in MASTER_TYPES}
        mtype = type_map.get(type_label, "yarn_supplier")
        color_hex = getattr(self, "chosen_color", "")

        if mtype in ("yarn_supplier", "knitting_unit", "dyeing_unit"):
            print(f"[DEBUG] Adding/Updating master: name={name}, type={mtype}, color={color_hex}")
            db.add_master(name, mtype, color_hex)
            db.update_master_color_and_type(name, mtype, color_hex)
        elif mtype == "yarn_type":
            db.add_yarn_type(name)
        elif mtype == "fabric_type":
            db.add_fabric_type(name)

        messagebox.showinfo("Saved", f"{name} saved/updated.")

        # Reset inputs
        self.name_entry.delete(0, tk.END)
        self.type_cb.current(0)
        self.chosen_color = ""
        self.color_btn.configure(text="Choose", style="TButton")

        self.load_masters()
        self.reload_cb_and_notify()

    def load_masters(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        self.color_imgs.clear()

        for t in MASTER_TYPES:
            mtype = t[1]
            rows = []

            if mtype in ("yarn_supplier", "knitting_unit", "dyeing_unit"):
                rows = db.list_suppliers(mtype)
            elif mtype == "yarn_type":
                rows = [{"name": n, "type": mtype, "color_code": ""} for n in db.list_yarn_types()]
            elif mtype == "fabric_type":
                rows = [{"name": n, "type": mtype, "color_code": ""} for n in db.list_fabric_types()]

            print(f"[DEBUG] Loading masters for type={mtype}, rows={rows}")
            for row in rows:
                try:
                    name = row["name"]
                    typ = row["type"] if "type" in row.keys() else mtype
                    color = row["color_code"] if "color_code" in row.keys() else ""
                    type_label = next((x[0] for x in MASTER_TYPES if x[1] == typ), typ)

                    print(f"[DEBUG] Inserting row: name={name}, type={type_label}, color={color}")
                    if color:
                        img = tk.PhotoImage(width=16, height=16)
                        img.put(color, to=(0, 0, 16, 16))
                        self.color_imgs[name] = img
                        self.tree.insert("", "end", values=(name, type_label, color), image=img)
                    else:
                        self.tree.insert("", "end", values=(name, type_label, ""))
                except KeyError as e:
                    print(f"[DEBUG] KeyError in load_masters: {e}, row={row}")
                    continue

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name, typelabel, _ = self.tree.item(sel[0])["values"]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            success = db.delete_master_by_name(name)
            if not success:
                messagebox.showwarning("Cannot Delete", f"{name} cannot be deleted (maybe in use).")
            self.load_masters()
            self.reload_cb_and_notify()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name, typelabel, color = self.tree.item(sel[0])["values"]

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)

        labels = [t[0] for t in MASTER_TYPES]
        try:
            self.type_cb.current(labels.index(typelabel))
        except Exception:
            self.type_cb.current(0)

        if typelabel in ("Yarn Supplier", "Knitting Unit", "Dyeing Unit"):
            self.chosen_color = color or ""
            style_name = "Custom.TButton" if self.chosen_color else "TButton"
            if self.chosen_color:
                s = ttk.Style()
                s.configure(style_name, background=self.chosen_color, foreground="white")
                print(f"[DEBUG] Configuring style {style_name} with background={self.chosen_color} in edit_selected")
            self.color_btn.configure(text=color or "Choose", style=style_name)
        else:
            self.chosen_color = ""
            self.color_btn.configure(text="Choose", style="TButton")

    def reload_cb_and_notify(self):
        if self.on_change_callback:
            self.on_change_callback()
