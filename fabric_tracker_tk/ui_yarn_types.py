import tkinter as tk
from tkinter import ttk, messagebox
from . import db

class YarnTypesScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.load_data()

    def build_ui(self):
        ttk.Label(self, text="Yarn Types Master", font=("Arial", 14, "bold")).pack(pady=10)

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=5)

        ttk.Label(form_frame, text="Yarn Type:").grid(row=0, column=0, sticky="e")
        self.entry_name = ttk.Entry(form_frame, width=30)
        self.entry_name.grid(row=0, column=1, padx=5)

        ttk.Button(form_frame, text="Add / Update", command=self.save_yarn_type).grid(row=0, column=2, padx=5)
        ttk.Button(form_frame, text="Delete", command=self.delete_yarn_type).grid(row=0, column=3, padx=5)

        columns = ("id", "name")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Yarn Type")
        self.tree.column("id", width=50)
        self.tree.column("name", width=250)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM yarn_types ORDER BY name")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def save_yarn_type(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Yarn type cannot be empty.")
            return

        selected = self.tree.selection()
        conn = db.get_connection()
        cur = conn.cursor()
        if selected:
            yarn_type_id = self.tree.item(selected[0])["values"][0]
            cur.execute("UPDATE yarn_types SET name=? WHERE id=?", (name, yarn_type_id))
        else:
            cur.execute("INSERT INTO yarn_types (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        self.entry_name.delete(0, tk.END)
        self.load_data()

    def delete_yarn_type(self):
        selected = self.tree.selection()
        if not selected:
            return
        yarn_type_id = self.tree.item(selected[0])["values"][0]
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM yarn_types WHERE id=?", (yarn_type_id,))
        conn.commit()
        conn.close()
        self.entry_name.delete(0, tk.END)
        self.load_data()

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.entry_name.delete(0, tk.END)
            s
