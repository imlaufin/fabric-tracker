import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from fabric_tracker_tk import db

MASTER_TYPES = [
    ("Yarn Supplier", "yarn_supplier"),
    ("Knitting Unit", "knitting_unit"),
    ("Dyeing Unit", "dyeing_unit"),
    ("Yarn Type", "yarn_type"),
    ("Fabric Type", "fabric_type")
]

class MastersFrame(ttk.Frame):
    def __init__(self, parent, controller=None, on_change_callback=None):
        super().__init__(parent)
        self.controller = controller
        self.on_change_callback = on_change_callback
        self.chosen_color = ""
        self.color_imgs = {}  # Store small color rectangles for treeview
        self.selected_fabric = None  # Track selected fabric for composition
        # Set theme to support background colors
        style = ttk.Style()
        style.theme_use("clam")
        print(f"[DEBUG] Tkinter theme set to: {style.theme_use()}")
        self.build_ui()
        self.load_masters()

    def build_ui(self):
        # Main frame with padding
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # Supplier Section
        supplier_frame = ttk.LabelFrame(self, text="Suppliers")
        supplier_frame.pack(fill="x", pady=5)
        self.build_supplier_ui(supplier_frame)

        # Yarn Types Section
        yarn_frame = ttk.LabelFrame(self, text="Yarn Types")
        yarn_frame.pack(fill="x", pady=5)
        self.build_yarn_type_ui(yarn_frame)

        # Fabric Types Section
        fabric_frame = ttk.LabelFrame(self, text="Fabric Types")
        fabric_frame.pack(fill="x", pady=5)
        self.build_fabric_type_ui(fabric_frame)

        # Fabric Composition Section
        comp_frame = ttk.LabelFrame(self, text="Fabric Yarn Composition")
        comp_frame.pack(fill="x", pady=5)
        self.build_composition_ui(comp_frame)

    def build_supplier_ui(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.supplier_name_entry = ttk.Entry(top, width=30)
        self.supplier_name_entry.grid(row=0, column=1, padx=5)

        ttk.Label(top, text="Type:").grid(row=0, column=2, sticky="w")
        self.supplier_type_cb = ttk.Combobox(top, values=[t[0] for t in MASTER_TYPES if t[1] in ("yarn_supplier", "knitting_unit", "dyeing_unit")], state="readonly", width=18)
        self.supplier_type_cb.grid(row=0, column=3, padx=5)
        self.supplier_type_cb.current(0)

        ttk.Label(top, text="Color:").grid(row=0, column=4, sticky="w")
        self.supplier_color_btn = ttk.Button(top, text="Choose", command=self.choose_supplier_color)
        self.supplier_color_btn.grid(row=0, column=5, padx=5)

        ttk.Button(top, text="Add / Update", command=self.add_or_update_supplier).grid(row=0, column=6, padx=8)
        ttk.Button(top, text="Delete", command=self.delete_supplier).grid(row=0, column=7, padx=5)

        self.supplier_tree = ttk.Treeview(parent, columns=("name", "type", "color"), show="headings", height=5)
        self.supplier_tree.heading("name", text="Name")
        self.supplier_tree.heading("type", text="Type")
        self.supplier_tree.heading("color", text="Color")
        self.supplier_tree.column("name", width=200)
        self.supplier_tree.column("type", width=150)
        self.supplier_tree.column("color", width=100)
        self.supplier_tree.pack(fill="x", padx=5, pady=5)

        # Right-click context menu for suppliers
        self.supplier_menu = tk.Menu(self, tearoff=0)
        self.supplier_menu.add_command(label="Edit", command=self.edit_supplier)
        self.supplier_menu.add_command(label="Delete", command=self.delete_supplier)
        self.supplier_tree.bind("<Button-3>", self.show_supplier_context_menu)

    def build_yarn_type_ui(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.yarn_name_entry = ttk.Entry(top, width=30)
        self.yarn_name_entry.grid(row=0, column=1, padx=5)

        ttk.Button(top, text="Add / Update", command=self.add_or_update_yarn_type).grid(row=0, column=2, padx=8)
        ttk.Button(top, text="Delete", command=self.delete_yarn_type).grid(row=0, column=3, padx=5)

        self.yarn_tree = ttk.Treeview(parent, columns=("name",), show="headings", height=5)
        self.yarn_tree.heading("name", text="Yarn Type")
        self.yarn_tree.column("name", width=350)
        self.yarn_tree.pack(fill="x", padx=5, pady=5)

        # Right-click context menu for yarn types
        self.yarn_menu = tk.Menu(self, tearoff=0)
        self.yarn_menu.add_command(label="Edit", command=self.edit_yarn_type)
        self.yarn_menu.add_command(label="Delete", command=self.delete_yarn_type)
        self.yarn_tree.bind("<Button-3>", self.show_yarn_context_menu)

    def build_fabric_type_ui(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.fabric_name_entry = ttk.Entry(top, width=30)
        self.fabric_name_entry.grid(row=0, column=1, padx=5)

        ttk.Button(top, text="Add / Update", command=self.add_or_update_fabric_type).grid(row=0, column=2, padx=8)
        ttk.Button(top, text="Delete", command=self.delete_fabric_type).grid(row=0, column=3, padx=5)

        self.fabric_tree = ttk.Treeview(parent, columns=("name",), show="headings", height=5)
        self.fabric_tree.heading("name", text="Fabric Type")
        self.fabric_tree.column("name", width=350)
        self.fabric_tree.pack(fill="x", padx=5, pady=5)

        # Right-click context menu for fabric types
        self.fabric_menu = tk.Menu(self, tearoff=0)
        self.fabric_menu.add_command(label="Edit", command=self.edit_fabric_type)
        self.fabric_menu.add_command(label="Delete", command=self.delete_fabric_type)
        self.fabric_tree.bind("<Button-3>", self.show_fabric_context_menu)

    def build_composition_ui(self, parent):
        # Fabric Type Selection
        ttk.Label(parent, text="Fabric Type:").grid(row=0, column=0, sticky="w")
        self.comp_fabric_cb = ttk.Combobox(parent, values=db.list_fabric_types(), state="readonly", width=20)
        self.comp_fabric_cb.grid(row=0, column=1, padx=5)
        self.comp_fabric_cb.bind("<<ComboboxSelected>>", self.load_composition)

        # Composition Fields
        ttk.Label(parent, text="Component:").grid(row=0, column=2, sticky="w")
        self.comp_component_cb = ttk.Combobox(parent, values=["Main Fabric", "Rib", "Collar"], state="readonly", width=12)
        self.comp_component_cb.grid(row=0, column=3, padx=5)
        self.comp_component_cb.current(0)

        ttk.Label(parent, text="Yarn Type:").grid(row=0, column=4, sticky="w")
        self.comp_yarn_cb = ttk.Combobox(parent, values=db.list_yarn_types(), state="readonly", width=20)
        self.comp_yarn_cb.grid(row=0, column=5, padx=5)

        ttk.Label(parent, text="Ratio:").grid(row=0, column=6, sticky="w")
        self.ratio_entry = ttk.Entry(parent, width=10)
        self.ratio_entry.grid(row=0, column=7, padx=5)

        ttk.Button(parent, text="Add / Update Composition", command=self.add_or_update_composition).grid(row=0, column=8, padx=5)
        ttk.Button(parent, text="Delete Composition", command=self.delete_composition).grid(row=0, column=9, padx=5)

        self.comp_tree = ttk.Treeview(parent, columns=("component", "yarn_type", "ratio"), show="headings", height=5)
        self.comp_tree.heading("component", text="Component")
        self.comp_tree.heading("yarn_type", text="Yarn Type")
        self.comp_tree.heading("ratio", text="Ratio")
        self.comp_tree.column("component", width=100)
        self.comp_tree.column("yarn_type", width=150)
        self.comp_tree.column("ratio", width=100)
        self.comp_tree.grid(row=1, column=0, columnspan=10, padx=5, pady=5, sticky="ew")

    def choose_supplier_color(self):
        color = colorchooser.askcolor(title="Choose color")
        if color and color[1]:
            self.chosen_color = color[1]
            style_name = "Custom.TButton"
            s = ttk.Style()
            s.configure(style_name, background=self.chosen_color, foreground="white")
            self.supplier_color_btn.configure(text=self.chosen_color, style=style_name)

    def add_or_update_supplier(self):
        name = self.supplier_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return
        type_label = self.supplier_type_cb.get()
        type_map = {t[0]: t[1] for t in MASTER_TYPES}
        mtype = type_map.get(type_label, "yarn_supplier")
        color_hex = self.chosen_color
        db.add_master(name, mtype, color_hex)
        db.update_master_color_and_type(name, mtype, color_hex)
        messagebox.showinfo("Saved", f"{name} saved/updated.")
        self.supplier_name_entry.delete(0, tk.END)
        self.supplier_type_cb.current(0)
        self.chosen_color = ""
        self.supplier_color_btn.configure(text="Choose", style="TButton")
        self.load_masters()
        if self.on_change_callback:
            self.on_change_callback()

    def delete_supplier(self):
        sel = self.supplier_tree.selection()
        if not sel:
            return
        name, _, _ = self.supplier_tree.item(sel[0])["values"]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            if not db.delete_master_by_name(name):
                messagebox.showwarning("Cannot Delete", f"{name} cannot be deleted (maybe in use).")
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()

    def edit_supplier(self):
        sel = self.supplier_tree.selection()
        if not sel:
            return
        name, typelabel, color = self.supplier_tree.item(sel[0])["values"]
        self.supplier_name_entry.delete(0, tk.END)
        self.supplier_name_entry.insert(0, name)
        labels = [t[0] for t in MASTER_TYPES if t[1] in ("yarn_supplier", "knitting_unit", "dyeing_unit")]
        try:
            self.supplier_type_cb.current(labels.index(typelabel))
        except ValueError:
            self.supplier_type_cb.current(0)
        self.chosen_color = color or ""
        style_name = "Custom.TButton" if self.chosen_color else "TButton"
        if self.chosen_color:
            s = ttk.Style()
            s.configure(style_name, background=self.chosen_color, foreground="white")
        self.supplier_color_btn.configure(text=color or "Choose", style=style_name)

    def show_supplier_context_menu(self, event):
        selected = self.supplier_tree.identify_row(event.y)
        if selected:
            self.supplier_tree.selection_set(selected)
            self.supplier_menu.post(event.x_root, event.y_root)

    def add_or_update_yarn_type(self):
        name = self.yarn_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return
        db.add_yarn_type(name)
        messagebox.showinfo("Saved", f"{name} saved/updated.")
        self.yarn_name_entry.delete(0, tk.END)
        self.load_masters()
        if self.on_change_callback:
            self.on_change_callback()

    def delete_yarn_type(self):
        sel = self.yarn_tree.selection()
        if not sel:
            return
        name = self.yarn_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            if not db.delete_yarn_type(name):
                messagebox.showwarning("Cannot Delete", f"{name} cannot be deleted (maybe in use).")
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()

    def edit_yarn_type(self):
        sel = self.yarn_tree.selection()
        if not sel:
            return
        name = self.yarn_tree.item(sel[0])["values"][0]
        self.yarn_name_entry.delete(0, tk.END)
        self.yarn_name_entry.insert(0, name)

    def show_yarn_context_menu(self, event):
        selected = self.yarn_tree.identify_row(event.y)
        if selected:
            self.yarn_tree.selection_set(selected)
            self.yarn_menu.post(event.x_root, event.y_root)

    def add_or_update_fabric_type(self):
        name = self.fabric_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return
        db.add_fabric_type(name)
        messagebox.showinfo("Saved", f"{name} saved/updated.")
        self.fabric_name_entry.delete(0, tk.END)
        self.load_masters()
        if self.on_change_callback:
            self.on_change_callback()

    def delete_fabric_type(self):
        sel = self.fabric_tree.selection()
        if not sel:
            return
        name = self.fabric_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            if not db.delete_fabric_type(name):
                messagebox.showwarning("Cannot Delete", f"{name} cannot be deleted (maybe in use).")
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()

    def edit_fabric_type(self):
        sel = self.fabric_tree.selection()
        if not sel:
            return
        name = self.fabric_tree.item(sel[0])["values"][0]
        self.fabric_name_entry.delete(0, tk.END)
        self.fabric_name_entry.insert(0, name)

    def show_fabric_context_menu(self, event):
        selected = self.fabric_tree.identify_row(event.y)
        if selected:
            self.fabric_tree.selection_set(selected)
            self.fabric_menu.post(event.x_root, event.y_root)

    def load_composition(self, event=None):
        fabric_name = self.comp_fabric_cb.get()
        if not fabric_name:
            for r in self.comp_tree.get_children():
                self.comp_tree.delete(r)
            return
        self.selected_fabric = fabric_name
        for r in self.comp_tree.get_children():
            self.comp_tree.delete(r)
        compositions = db.get_fabric_yarn_composition(fabric_name)
        for comp in compositions:
            self.comp_tree.insert("", "end", values=(comp["component"], comp["yarn_type"], comp["ratio"]))

    def add_or_update_composition(self):
        fabric_name = self.comp_fabric_cb.get()
        component = self.comp_component_cb.get()
        yarn_name = self.comp_yarn_cb.get()
        ratio = float(self.ratio_entry.get()) if self.ratio_entry.get().strip() else 0.0
        if not fabric_name or not yarn_name or ratio <= 0 or ratio > 100:
            messagebox.showwarning("Missing", "All fields (Fabric, Component, Yarn, Ratio) are required, and Ratio must be between 0 and 100.")
            return
        try:
            db.add_fabric_yarn_composition(fabric_name, yarn_name, ratio, component)
            messagebox.showinfo("Saved", f"Composition for {fabric_name} ({component}) updated.")
            self.load_composition()
            if self.on_change_callback:
                self.on_change_callback()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def delete_composition(self):
        selected = self.comp_tree.selection()
        if not selected:
            return
        component, yarn_type, _ = self.comp_tree.item(selected[0])["values"]
        fabric_name = self.comp_fabric_cb.get()
        if messagebox.askyesno("Confirm", f"Delete {component} composition for {yarn_type} from {fabric_name}?"):
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    DELETE FROM fabric_yarn_composition
                    WHERE fabric_type_id = (SELECT id FROM fabric_types WHERE name = ?)
                    AND yarn_type_id = (SELECT id FROM yarn_types WHERE name = ?)
                    AND component = ?
                """, (fabric_name, yarn_type, component))
                conn.commit()
            self.load_composition()
            if self.on_change_callback:
                self.on_change_callback()

    def load_masters(self):
        # Clear all trees
        for tree in [self.supplier_tree, self.yarn_tree, self.fabric_tree]:
            for r in tree.get_children():
                tree.delete(r)
        self.color_imgs.clear()

        # Load Suppliers
        for row in db.list_suppliers():
            name = row["name"]
            type_label = next((t[0] for t in MASTER_TYPES if t[1] == row["type"]), row["type"])
            color = row["color_code"]
            if color:
                img = tk.PhotoImage(width=16, height=16)
                img.put(color, to=(0, 0, 16, 16))
                self.color_imgs[name] = img
                self.supplier_tree.insert("", "end", values=(name, type_label, color), image=img)
            else:
                self.supplier_tree.insert("", "end", values=(name, type_label, ""))

        # Load Yarn Types
        for name in db.list_yarn_types():
            self.yarn_tree.insert("", "end", values=(name,))

        # Load Fabric Types
        for name in db.list_fabric_types():
            self.fabric_tree.insert("", "end", values=(name,))

        # Update comboboxes
        self.comp_fabric_cb['values'] = db.list_fabric_types()
        self.comp_yarn_cb['values'] = db.list_yarn_types()

    def reload_cb_and_notify(self):
        self.load_masters()
        if self.on_change_callback:
            self.on_change_callback()
