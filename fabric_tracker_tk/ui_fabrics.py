import tkinter as tk
from tkinter import ttk, messagebox
import db

class FabricsScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_data()

    def build_ui(self):
        ttk.Label(self, text="Fabrics Master", font=("Arial", 14, "bold")).pack(pady=10)

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=5)

        ttk.Label(form_frame, text="Fabric Name:").grid(row=0, column=0, sticky="e")
        self.entry_name = ttk.Entry(form_frame, width=30)
        self.entry_name.grid(row=0, column=1, padx=5)

        ttk.Label(form_frame, text="Fabric Type:").grid(row=1, column=0, sticky="e")
        self.entry_type = ttk.Entry(form_frame, width=30)
        self.entry_type.grid(row=1, column=1, padx=5)

        ttk.Button(form_frame, text="Add / Update", command=self.save_fabric).grid(row=0, column=2, rowspan=2, padx=5)
        ttk.Button(form_frame, text="Delete", command=self.delete_fabric).grid(row=0, column=3, rowspan=2, padx=5)

        columns = ("id", "name", "type")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Fabric Name")
        self.tree.heading("type", text="Fabric Type")
        self.tree.column("id", width=50)
        self.tree.column("name", width=200)
        self.tree.column("type", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, type FROM fabrics ORDER BY name")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def save_fabric(self):
        name = self.entry_name.get().strip()
        fabric_type = self.entry_type.get().strip()

        if not name:
            messagebox.showwarning("Validation", "Fabric name cannot be empty.")
            return

        selected = self.tree.selection()
        conn = db.get_connection()
        cur = conn.cursor()
        if selected:
            fabric_id = self.tree.item(selected[0])["values"][0]
            cur.execute("UPDATE fabrics SET name=?, type=? WHERE id=?", (name, fabric_type, fabric_id))
        else:
            cur.execute("INSERT INTO fabrics (name, type) VALUES (?, ?)", (name, fabric_type))
        conn.commit()
        conn.close()
        self.entry_name.delete(0, tk.END)
        self.entry_type.delete(0, tk.END)
        self.load_data()

    def delete_fabric(self):
        selected = self.tree.selection()
        if not selected:
            return
        fabric_id = self.tree.item(selected[0])["values"][0]
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM fabrics WHERE id=?", (fabric_id,))
        conn.commit()
        conn.close()
        self.entry_name.delete(0, tk.END)
        self.entry_type.delete(0, tk.END)
        self.load_data()

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, self.tree.item(selected[0])["values"][1])
            self.entry_type.delete(0, tk.END)
            self.entry_type.insert(0, self.tree.item(selected[0])["values"][2])
