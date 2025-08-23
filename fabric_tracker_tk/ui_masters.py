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
        self.frame_positions = {}  # Store positions for moveable frames
        self.frame_sizes = {}  # Store sizes for resizable frames
        # Set theme to support background colors
        style = ttk.Style()
        style.theme_use("clam")
        print(f"[DEBUG] Tkinter theme set to: {style.theme_use()}")
        self.build_ui()
        self.load_masters()

    def build_ui(self):
        # Main canvas with scrollbar
        self.canvas = tk.Canvas(self, bg="white", width=800, height=1000)  # Larger initial size
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.inner_frame = ttk.Frame(self.canvas)  # Remove fixed size
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        print(f"[DEBUG] Canvas created with scrollregion: {self.canvas.bbox('all')}")

        # Supplier Section
        supplier_frame = ttk.LabelFrame(self.inner_frame, text="Suppliers")
        supplier_frame.place(x=10, y=10, width=760, height=180)  # Minimum size
        print(f"[DEBUG] Supplier frame placed at (10, 10)")
        self.build_supplier_ui(supplier_frame)

        # Yarn Types Section
        yarn_frame = ttk.LabelFrame(self.inner_frame, text="Yarn Types")
        yarn_frame.place(x=10, y=200, width=760, height=180)  # Minimum size
        print(f"[DEBUG] Yarn frame placed at (10, 200)")
        self.build_yarn_type_ui(yarn_frame)

        # Fabric Compositions Section (combined)
        fabric_comp_frame = ttk.LabelFrame(self.inner_frame, text="Fabric Compositions")
        fabric_comp_frame.place(x=10, y=400, width=760, height=180)  # Minimum size
        print(f"[DEBUG] Fabric comp frame placed at (10, 400)")
        self.build_fabric_composition_ui(fabric_comp_frame)

        # Make frames moveable and resizable
        for frame in [supplier_frame, yarn_frame, fabric_comp_frame]:
            frame.bind("<Button-1>", self.start_move)
            frame.bind("<B1-Motion>", self.do_move)
            frame.bind("<Button-3>", self.start_resize)
            frame.bind("<B3-Motion>", self.do_resize)

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
        self.yarn_tree.column("name", width=100)
        self.yarn_tree.pack(fill="x", padx=5, pady=5)

        # Right-click context menu for yarn types
        self.yarn_menu = tk.Menu(self, tearoff=0)
        self.yarn_menu.add_command(label="Edit", command=self.edit_yarn_type)
        self.yarn_menu.add_command(label="Delete", command=self.delete_yarn_type)
        self.yarn_tree.bind("<Button-3>", self.show_yarn_context_menu)

    def build_fabric_composition_ui(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=5, pady=5)

        # Fabric Name Input
        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.fabric_name_entry = ttk.Entry(top, width=30)
        self.fabric_name_entry.grid(row=0, column=1, padx=5)

        ttk.Button(top, text="Add / Update Fabric", command=self.add_or_update_fabric).grid(row=0, column=2, padx=8)
        ttk.Button(top, text="Delete Fabric", command=self.delete_fabric).grid(row=0, column=3, padx=5)

        # Composition Fields
        ttk.Label(top, text="Component:").grid(row=1, column=0, sticky="w")
        self.comp_component_cb = ttk.Combobox(top, values=["Main Fabric", "Rib", "Collar"], state="readonly", width=12)
        self.comp_component_cb.grid(row=1, column=1, padx=5)
        self.comp_component_cb.current(0)

        ttk.Label(top, text="Yarn Type:").grid(row=1, column=2, sticky="w")
        self.comp_yarn_cb = ttk.Combobox(top, values=db.list_yarn_types(), state="readonly", width=20)
        self.comp_yarn_cb.grid(row=1, column=3, padx=5)

        ttk.Label(top, text="Ratio:").grid(row=1, column=4, sticky="w")
        self.ratio_entry = ttk.Entry(top, width=10)
        self.ratio_entry.grid(row=1, column=5, padx=5)

        ttk.Button(top, text="Add / Update Composition", command=self.add_or_update_composition).grid(row=1, column=6, padx=5)
        ttk.Button(top, text="Delete Composition", command=self.delete_composition).grid(row=1, column=7, padx=5)

        # Combined Treeview
        self.fabric_comp_tree = ttk.Treeview(parent, columns=("name", "component", "yarn_type", "ratio"), show="headings", height=5)
        self.fabric_comp_tree.heading("name", text="Fabric Name")
        self.fabric_comp_tree.heading("component", text="Component")
        self.fabric_comp_tree.heading("yarn_type", text="Yarn Type")
        self.fabric_comp_tree.heading("ratio", text="Ratio")
        self.fabric_comp_tree.column("name", width=150)
        self.fabric_comp_tree.column("component", width=100)
        self.fabric_comp_tree.column("yarn_type", width=150)
        self.fabric_comp_tree.column("ratio", width=100)
        self.fabric_comp_tree.pack(fill="x", padx=5, pady=5)

        # Add resize handle (visual cue)
        self.resize_handle = tk.Label(parent, bg="gray", width=10, height=10)
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_handle.bind("<Button-3>", self.start_resize)
        self.resize_handle.bind("<B3-Motion>", self.do_resize)

        # Right-click context menu for fabric compositions
        self.fabric_comp_menu = tk.Menu(self, tearoff=0)
        self.fabric_comp_menu.add_command(label="Edit Fabric", command=self.edit_fabric)
        self.fabric_comp_menu.add_command(label="Delete Fabric", command=self.delete_fabric)
        self.fabric_comp_menu.add_command(label="Edit Composition", command=self.edit_composition)
        self.fabric_comp_menu.add_command(label="Delete Composition", command=self.delete_composition)
        self.fabric_comp_tree.bind("<Button-3>", self.show_fabric_comp_context_menu)

    def choose_supplier_color(self):
        color = colorchooser.askcolor(title="Choose color")
        if color and color[1]:
            self.chosen_color = color[1]
            style_name = "Custom.TButton"
            s = ttk.Style()
            s.configure(style_name, background=self.chosen_color, foreground="white" if self.is_light_color(self.chosen_color) else "black")
            self.supplier_color_btn.configure(text=self.chosen_color, style=style_name)

    def is_light_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance > 0.5

    def add_or_update_supplier(self):
        name = self.supplier_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return
        type_label = self.supplier_type_cb.get()
        type_map = {t[0]: t[1] for t in MASTER_TYPES}
        mtype = type_map.get(type_label, "yarn_supplier")
        color_hex = self.chosen_color
        try:
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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save supplier: {str(e)}")

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
            s.configure(style_name, background=self.chosen_color, foreground="white" if self.is_light_color(self.chosen_color) else "black")
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
        try:
            db.add_yarn_type(name)
            messagebox.showinfo("Saved", f"{name} saved/updated.")
            self.yarn_name_entry.delete(0, tk.END)
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save yarn type: {str(e)}")

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

    def add_or_update_fabric(self):
        name = self.fabric_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Name required")
            return
        try:
            # Add fabric as a composition with no yarn (can be updated later)
            db.add_fabric_composition(name, db.list_yarn_types()[0] if db.list_yarn_types() else "", 0.0, "Main Fabric")
            messagebox.showinfo("Saved", f"{name} saved/updated.")
            self.fabric_name_entry.delete(0, tk.END)
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save fabric: {str(e)}")

    def delete_fabric(self):
        sel = self.fabric_comp_tree.selection()
        if not sel:
            return
        name, _, _, _ = self.fabric_comp_tree.item(sel[0])["values"]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            if not db.delete_fabric_composition(name, "", ""):  # Delete all compositions for this fabric
                messagebox.showwarning("Cannot Delete", f"{name} cannot be deleted (maybe in use).")
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()

    def edit_fabric(self):
        sel = self.fabric_comp_tree.selection()
        if not sel:
            return
        name, _, _, _ = self.fabric_comp_tree.item(sel[0])["values"]
        self.fabric_name_entry.delete(0, tk.END)
        self.fabric_name_entry.insert(0, name)

    def add_or_update_composition(self):
        fabric_name = self.fabric_name_entry.get().strip() or self.selected_fabric
        if not fabric_name:
            messagebox.showwarning("Missing", "Fabric name required")
            return
        component = self.comp_component_cb.get()
        yarn_name = self.comp_yarn_cb.get()
        ratio_str = self.ratio_entry.get().strip()
        if not yarn_name or not ratio_str:
            messagebox.showwarning("Missing", "Yarn and Ratio are required")
            return
        try:
            ratio = float(ratio_str)
            if ratio <= 0 or ratio > 100:
                raise ValueError("Ratio must be between 0 and 100.")
            db.add_fabric_composition(fabric_name, yarn_name, ratio, component)
            messagebox.showinfo("Saved", f"Composition for {fabric_name} ({component}) updated.")
            self.ratio_entry.delete(0, tk.END)
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save composition: {str(e)}")

    def delete_composition(self):
        sel = self.fabric_comp_tree.selection()
        if not sel:
            return
        name, component, yarn_type, _ = self.fabric_comp_tree.item(sel[0])["values"]
        if messagebox.askyesno("Confirm", f"Delete {component} composition for {yarn_type} from {name}?"):
            if not db.delete_fabric_composition(name, component, yarn_type):
                messagebox.showwarning("Cannot Delete", f"Composition cannot be deleted (maybe in use).")
            self.load_masters()
            if self.on_change_callback:
                self.on_change_callback()

    def edit_composition(self):
        sel = self.fabric_comp_tree.selection()
        if not sel:
            return
        name, component, yarn_type, ratio = self.fabric_comp_tree.item(sel[0])["values"]
        self.fabric_name_entry.delete(0, tk.END)
        self.fabric_name_entry.insert(0, name)
        self.comp_component_cb.set(component)
        self.comp_yarn_cb.set(yarn_type)
        self.ratio_entry.delete(0, tk.END)
        self.ratio_entry.insert(0, ratio)
        self.selected_fabric = name

    def show_fabric_comp_context_menu(self, event):
        selected = self.fabric_comp_tree.identify_row(event.y)
        if selected:
            self.fabric_comp_tree.selection_set(selected)
            self.fabric_comp_menu.post(event.x_root, event.y_root)

    def load_masters(self):
        # Clear all trees and images
        for tree in [self.supplier_tree, self.yarn_tree, self.fabric_comp_tree]:
            for r in tree.get_children():
                tree.delete(r)
        self.color_imgs.clear()
        print(f"[DEBUG] Loading masters...")

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
        print(f"[DEBUG] Loaded {len(db.list_suppliers())} suppliers")

        # Load Yarn Types
        for name in db.list_yarn_types():
            self.yarn_tree.insert("", "end", values=(name,))
        print(f"[DEBUG] Loaded {len(db.list_yarn_types())} yarn types")

        # Load Fabric Compositions
        for comp in db.list_fabric_compositions():
            self.fabric_comp_tree.insert("", "end", values=(comp["name"], comp["component"], comp["yarn_type"], comp["ratio"]))
        print(f"[DEBUG] Loaded {len(db.list_fabric_compositions())} fabric compositions")

        # Update comboboxes
        self.comp_yarn_cb['values'] = db.list_yarn_types()

    def start_move(self, event):
        frame = event.widget
        self.frame_positions[frame] = (event.x, event.y)

    def do_move(self, event):
        frame = event.widget
        dx = event.x - self.frame_positions[frame][0]
        dy = event.y - self.frame_positions[frame][1]
        x, y = frame.winfo_x() + dx, frame.winfo_y() + dy
        frame.place(x=x, y=y)
        self.frame_positions[frame] = (event.x, event.y)
        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def start_resize(self, event):
        frame = event.widget
        self.frame_sizes[frame] = (frame.winfo_width(), frame.winfo_height())
        self.resize_start = (event.x, event.y)

    def do_resize(self, event):
        frame = event.widget
        dx = event.x - self.resize_start[0]
        dy = event.y - self.resize_start[1]
        new_width = max(100, self.frame_sizes[frame][0] + dx)
        new_height = max(100, self.frame_sizes[frame][1] + dy)
        frame.configure(width=new_width, height=new_height)
        self.frame_sizes[frame] = (new_width, new_height)
        # Update resize handle and canvas scroll region
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def reload_cb_and_notify(self):
        self.load_masters()
        if self.on_change_callback:
            self.on_change_callback()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Masters Management")
    app = MastersFrame(root)
    app.pack(fill="both", expand=True)
    root.geometry("850x1050")  # Set initial window size to fit content
    root.mainloop()
