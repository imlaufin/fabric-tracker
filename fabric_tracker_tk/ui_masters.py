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
        self.frame_spans = {"Suppliers": 2, "Yarn Types": 1, "Fabric Compositions": 1}  # Initial spans (Suppliers starts at 1x2)
        self.frame_grid = {"Suppliers": (0, 0), "Yarn Types": (1, 0), "Fabric Compositions": (1, 1)}  # Initial (row, column)
        self.frames = {}  # Store frame references
        # Set theme to support background colors
        style = ttk.Style()
        style.theme_use("clam")
        print(f"[DEBUG] Tkinter theme set to: {style.theme_use()}")
        self.build_ui()
        self.load_masters()

    def build_ui(self):
        # Configure grid layout with dynamic scaling
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        for i in range(4):  # 4 columns
            self.grid_columnconfigure(i, weight=1)

        # Create and place frames with dynamic sizing
        for name in ["Suppliers", "Yarn Types", "Fabric Compositions"]:
            frame = ttk.LabelFrame(self, text=name)
            self.frames[name] = frame
            row, col = self.frame_grid[name]
            span = self.frame_spans[name]
            frame.grid(row=row, column=col, columnspan=span, sticky="nsew")
            frame.bind("<Button-1>", lambda e, n=name: self.start_move(e, n))
            frame.bind("<B1-Motion>", lambda e, n=name: self.do_move(e, n))
            frame.bind("<Button-3>", lambda e, n=name: self.start_resize(e, n))
            frame.bind("<B3-Motion>", lambda e, n=name: self.do_resize(e, n))
            if name == "Suppliers":
                self.build_supplier_ui(frame)
            elif name == "Yarn Types":
                self.build_yarn_type_ui(frame)
            elif name == "Fabric Compositions":
                self.build_fabric_composition_ui(frame)

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
        self.supplier_tree.pack(fill="both", expand=True)
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
        self.yarn_tree.pack(fill="both", expand=True)
        self.yarn_menu = tk.Menu(self, tearoff=0)
        self.yarn_menu.add_command(label="Edit", command=self.edit_yarn_type)
        self.yarn_menu.add_command(label="Delete", command=self.delete_yarn_type)
        self.yarn_tree.bind("<Button-3>", self.show_yarn_context_menu)

    def build_fabric_composition_ui(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=5, pady=5)
        ttk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        self.fabric_name_entry = ttk.Entry(top, width=30)
        self.fabric_name_entry.grid(row=0, column=1, padx=5)
        ttk.Button(top, text="Add / Update Fabric", command=self.add_or_update_fabric).grid(row=0, column=2, padx=8)
        ttk.Button(top, text="Delete Fabric", command=self.delete_fabric).grid(row=0, column=3, padx=5)
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
        self.fabric_comp_tree = ttk.Treeview(parent, columns=("name", "component", "yarn_type", "ratio"), show="headings", height=5)
        self.fabric_comp_tree.heading("name", text="Fabric Name")
        self.fabric_comp_tree.heading("component", text="Component")
        self.fabric_comp_tree.heading("yarn_type", text="Yarn Type")
        self.fabric_comp_tree.heading("ratio", text="Ratio")
        self.fabric_comp_tree.column("name", width=150)
        self.fabric_comp_tree.column("component", width=100)
        self.fabric_comp_tree.column("yarn_type", width=150)
        self.fabric_comp_tree.column("ratio", width=100)
        self.fabric_comp_tree.pack(fill="both", expand=True)
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
            if not db.delete_fabric_composition(name, "", ""):
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

    def start_move(self, event, name):
        frame = self.frames[name]
        self.frame_positions[frame] = (event.x, event.y)

    def do_move(self, event, name):
        frame = self.frames[name]
        dx = event.x - self.frame_positions[frame][0]
        dy = event.y - self.frame_positions[frame][1]
        current_row, current_col = self.frame_grid[name]
        cell_height = self.winfo_height() // 2
        cell_width = self.winfo_width() // 4
        new_row = max(0, min(1, current_row + (dy // cell_height)))  # Snap to row
        new_col = max(0, min(3 - (self.frame_spans[name] - 1), current_col + (dx // cell_width)))  # Snap to column
        if new_row != current_row or new_col != current_col:
            # Check for collisions and adjust spans
            can_move = True
            for n, (r, c) in self.frame_grid.items():
                if n != name and new_row == r:
                    span = self.frame_spans[n]
                    if new_col >= c and new_col < c + span:
                        can_move = False
                        break
            if can_move:
                frame.grid_forget()
                self.frame_grid[name] = (new_row, new_col)
                # Adjust span if another frame is in the same row
                same_row_frames = [n for n, (r, _) in self.frame_grid.items() if r == new_row and n != name]
                if same_row_frames:
                    self.frame_spans[name] = 1  # Force 1x1 if another frame is present
                else:
                    self.frame_spans[name] = min(2, 4 - new_col)  # Allow 1x2 if space permits
                frame.grid(row=new_row, column=new_col, columnspan=self.frame_spans[name], sticky="nsew")
        self.frame_positions[frame] = (event.x, event.y)

    def start_resize(self, event, name):
        frame = self.frames[name]
        self.frame_sizes[frame] = (frame.winfo_width(), frame.winfo_height())
        self.resize_start = (event.x, event.y)

    def do_resize(self, event, name):
        frame = self.frames[name]
        dx = event.x - self.resize_start[0]
        cell_width = self.winfo_width() // 4
        min_width = cell_width
        new_width = max(min_width, self.frame_sizes[frame][0] + dx)
        row, col = self.frame_grid[name]
        current_span = self.frame_spans[name]
        new_span = min(2, max(1, new_width // cell_width))  # Dynamic span based on window width
        if new_span != current_span:
            # Check if expansion to 1x2 is possible
            if new_span == 2:
                can_expand = True
                for n, (r, c) in self.frame_grid.items():
                    if n != name and row == r and col + 1 <= c < col + 2:
                        can_expand = False
                        break
                if can_expand and col + 1 <= 3:
                    self.frame_spans[name] = 2
                else:
                    self.frame_spans[name] = 1
            else:
                self.frame_spans[name] = 1
            frame.grid_forget()
            frame.grid(row=row, column=col, columnspan=self.frame_spans[name], sticky="nsew")
        self.frame_sizes[frame] = (frame.winfo_width(), frame.winfo_height())
        self.resize_start = (event.x, event.y)

    def reload_cb_and_notify(self):
        self.load_masters()
        if self.on_change_callback:
            self.on_change_callback()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Masters Management")
    app = MastersFrame(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
