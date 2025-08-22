import tkinter as tk
from tkinter import ttk, messagebox
from fabric_tracker_tk import db
from datetime import datetime

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.build_ui()
        self.reload_all()

    def build_ui(self):
        # Main container with grid layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # Left Panel: Status Overview
        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.left_frame.columnconfigure(0, weight=1)

        ttk.Label(self.left_frame, text="Status Overview", font=("Helvetica", 14, "bold")).grid(row=0, column=0, pady=5)
        self.status_vars = {}
        statuses = ["Ordered", "Knitted", "Dyed", "Received"]
        for i, status in enumerate(statuses, 1):
            frame = ttk.Frame(self.left_frame)
            frame.grid(row=i, column=0, pady=5, sticky="ew")
            ttk.Label(frame, text=f"{status}:", width=10).pack(side="left")
            self.status_vars[status] = tk.StringVar()
            ttk.Label(frame, textvariable=self.status_vars[status], width=5).pack(side="left")
            ttk.Progressbar(frame, length=150, maximum=100, mode="determinate").pack(side="left", padx=5)

        # Right Panel: Filters and Actions
        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_frame.columnconfigure(0, weight=1)

        # Filters
        ttk.Label(self.right_frame, text="Filters", font=("Helvetica", 14, "bold")).grid(row=0, column=0, pady=5)
        filter_frame = ttk.Frame(self.right_frame)
        filter_frame.grid(row=1, column=0, pady=5, sticky="ew")
        self.fabricator_var = tk.StringVar()
        fabricators = [f["name"] for f in db.get_fabricators("knitting_unit")] + [f["name"] for f in db.get_fabricators("dyeing_unit")]
        fabricators.insert(0, "")  # Empty option for all
        ttk.Label(filter_frame, text="Fabricator:").pack(side="left", padx=4)
        ttk.OptionMenu(filter_frame, self.fabricator_var, "", *fabricators).pack(side="left", padx=4)
        ttk.Label(filter_frame, text="From (dd/mm/yyyy):").pack(side="left", padx=4)
        self.from_entry = ttk.Entry(filter_frame, width=12)
        self.from_entry.pack(side="left", padx=4)
        ttk.Label(filter_frame, text="To (dd/mm/yyyy):").pack(side="left", padx=4)
        self.to_entry = ttk.Entry(filter_frame, width=12)
        self.to_entry.pack(side="left", padx=4)
        ttk.Button(filter_frame, text="Apply Filter", command=self.reload_all).pack(side="left", padx=6)

        # Actions
        ttk.Label(self.right_frame, text="Actions", font=("Helvetica", 14, "bold")).grid(row=2, column=0, pady=5)
        ttk.Button(self.right_frame, text="Refresh Data", command=self.reload_all).grid(row=3, column=0, pady=5)
        ttk.Button(self.right_frame, text="View Fabricators", command=lambda: self.controller.notebook.select(self.controller.fabricators_frame)).grid(row=4, column=0, pady=5)
        ttk.Button(self.right_frame, text="View Entries", command=lambda: self.controller.notebook.select(self.controller.entries_frame)).grid(row=5, column=0, pady=5)

        # Chart Area
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.chart_frame.columnconfigure(0, weight=1)
        ttk.Label(self.chart_frame, text="Status Distribution", font=("Helvetica", 12, "bold")).grid(row=0, column=0, pady=5)
        self.chart_label = ttk.Label(self.chart_frame, text="Chart Placeholder")
        self.chart_label.grid(row=1, column=0)

        # Summary Stats
        self.summary_frame = ttk.Frame(self)
        self.summary_frame.grid(row=2, column=1, sticky="sew", padx=5, pady=5)
        self.total_purchases_label = ttk.Label(self.summary_frame, text="Total Purchases: 0", font=("Arial", 12))
        self.total_purchases_label.pack(side="left", padx=6)
        self.total_yarn_kg_label = ttk.Label(self.summary_frame, text="Total Yarn (kg): 0", font=("Arial", 12))
        self.total_yarn_kg_label.pack(side="left", padx=6)
        self.total_batches_label = ttk.Label(self.summary_frame, text="Total Batches: 0", font=("Arial", 12))
        self.total_batches_label.pack(side="left", padx=6)

        # Batch Management Table
        self.batch_frame = ttk.Frame(self)
        self.batch_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.batch_frame.columnconfigure(0, weight=1)
        ttk.Label(self.batch_frame, text="Batch Management", font=("Helvetica", 14, "bold")).grid(row=0, column=0, pady=5)
        self.batch_tree = ttk.Treeview(self.batch_frame, columns=("batch_ref", "product_name", "expected_lots", "status"), show="headings")
        self.batch_tree.grid(row=1, column=0, sticky="nsew")
        for col, width, heading in zip(["batch_ref", "product_name", "expected_lots", "status"], [120, 150, 100, 100], ["Batch Ref", "Product Name", "Expected Lots", "Status"]):
            self.batch_tree.heading(col, text=heading)
            self.batch_tree.column(col, width=width)
        self.batch_tree.bind("<Button-3>", self.show_batch_context_menu)
        self.batch_tree.bind("<Double-1>", self.on_batch_double_click)

    def show_batch_context_menu(self, event):
        item = self.batch_tree.identify_row(event.y)
        if item:
            self.batch_tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Edit Batch", command=lambda: self.edit_batch(item))
            menu.add_command(label="Delete Batch", command=lambda: self.delete_batch_confirmed(item))
            menu.post(event.x_root, event.y_root)

    def edit_batch(self, item):
        batch_ref = self.batch_tree.item(item)["values"][0]
        dialog = tk.Toplevel(self)
        dialog.title("Edit Batch")
        dialog.geometry("400x300")
        ttk.Label(dialog, text="Batch Ref:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        batch_e = ttk.Entry(dialog, width=30)
        batch_e.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        batch_e.insert(0, batch_ref)

        ttk.Label(dialog, text="Product Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        product_e = ttk.Entry(dialog, width=30)
        product_e.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT product_name FROM batches WHERE batch_ref=?", (batch_ref,))
            row = cur.fetchone()
            if row:
                product_e.insert(0, row["product_name"])

        ttk.Label(dialog, text="Expected Lots:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        lots_e = ttk.Entry(dialog, width=30)
        lots_e.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT expected_lots FROM batches WHERE batch_ref=?", (batch_ref,))
            row = cur.fetchone()
            if row:
                lots_e.insert(0, row["expected_lots"])

        ttk.Label(dialog, text="Status:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        status_var = tk.StringVar(value="Ordered")
        statuses = ["Ordered", "Knitted", "Dyed", "Received"]
        ttk.OptionMenu(dialog, status_var, "Ordered", *statuses).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT status FROM batches WHERE batch_ref=?", (batch_ref,))
            row = cur.fetchone()
            if row:
                status_var.set(row["status"])

        def save_edit():
            new_batch_ref = batch_e.get().strip()
            product_name = product_e.get().strip()
            expected_lots = lots_e.get().strip()
            new_status = status_var.get()

            if not new_batch_ref or not expected_lots or not product_name:
                messagebox.showwarning("Missing Fields", "Batch Ref, Product Name, and Expected Lots are required.")
                return

            try:
                expected_lots = int(expected_lots)
                if expected_lots <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Expected Lots must be a positive integer.")
                return

            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE batches
                    SET batch_ref=?, product_name=?, expected_lots=?, status=?
                    WHERE batch_ref=?
                """, (new_batch_ref, product_name, expected_lots, new_status, batch_ref))
                conn.commit()
            dialog.destroy()
            self.reload_all()

        ttk.Button(dialog, text="Save", command=save_edit).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=5, column=0, columnspan=2, pady=5)

    def delete_batch_confirmed(self, item):
        batch_ref = self.batch_tree.item(item)["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete batch '{batch_ref}'?"):
            success = db.delete_batch(batch_ref)
            if success:
                self.reload_all()
            else:
                messagebox.showwarning("Delete Failed", f"Batch '{batch_ref}' cannot be deleted because it has associated purchases.")

    def on_batch_double_click(self, event):
        item = self.batch_tree.identify_row(event.y)
        if item:
            self.edit_batch(item)

    def reload_all(self):
        # Clear existing status data
        for status in self.status_vars:
            self.status_vars[status].set("0 / 0")

        from_date = self.from_entry.get().strip()
        to_date = self.to_entry.get().strip()
        try:
            from_db = db.ui_to_db_date(from_date) if from_date else None
            to_db = db.ui_to_db_date(to_date) if to_date else None
        except ValueError as e:
            tk.messagebox.showerror("Invalid Date", f"Invalid date format: {e}")
            return

        with db.get_connection() as conn:
            cur = conn.cursor()
            # Status counts
            sql = """
                SELECT b.status, COUNT(DISTINCT b.id) AS batch_count, COUNT(DISTINCT l.id) AS lot_count
                FROM batches b
                LEFT JOIN lots l ON b.id = l.batch_id
                LEFT JOIN purchases p ON b.batch_ref = p.batch_id
            """
            params = ()
            if from_db and to_db:
                sql += " WHERE p.date BETWEEN ? AND ?"
                params = (from_db, to_db)
            fabricator = self.fabricator_var.get()
            if fabricator:
                sql += " WHERE p.delivered_to = ?" if not params else " AND p.delivered_to = ?"
                params += (fabricator,)
            sql += " GROUP BY b.status"
            cur.execute(sql, params)
            status_data = {row["status"] or "Ordered": (row["batch_count"], row["lot_count"]) for row in cur.fetchall()}

            total_batches = sum(c[0] for c in status_data.values())
            total_lots = sum(c[1] for c in status_data.values())
            for status in self.status_vars:
                batch_count, lot_count = status_data.get(status, (0, 0))
                self.status_vars[status].set(f"B: {batch_count} / L: {lot_count}")
                if total_batches > 0:
                    progressbar = self.left_frame.winfo_children()[status == "Ordered" and 1 or status == "Knitted" and 2 or status == "Dyed" and 3 or 4].winfo_children()[2]
                    progressbar["value"] = (batch_count / total_batches) * 100 if total_batches else 0

            # Summary stats
            cur.execute("""
                SELECT COUNT(DISTINCT p.id) AS purchase_count, SUM(p.qty_kg) AS total_kg, COUNT(DISTINCT p.batch_id) AS batch_count
                FROM purchases p
            """, params)
            row = cur.fetchone()
            self.total_purchases_label.config(text=f"Total Purchases: {row['purchase_count'] or 0}")
            self.total_yarn_kg_label.config(text=f"Total Yarn (kg): {row['total_kg'] or 0}")
            self.total_batches_label.config(text=f"Total Batches: {row['batch_count'] or 0}")

            # Update chart
            self.update_chart(status_data, total_batches)

            # Load batches into batch table (excluding yarn batches where fabricator_id is NULL)
            for r in self.batch_tree.get_children():
                self.batch_tree.delete(r)
            cur.execute("""
                SELECT batch_ref, product_name, expected_lots, status
                FROM batches
                WHERE fabricator_id IS NOT NULL
                ORDER BY created_at DESC
            """)
            for row in cur.fetchall():
                self.batch_tree.insert("", "end", values=(row["batch_ref"], row["product_name"], row["expected_lots"], row["status"]))

    def update_chart(self, status_data, total_batches):
        if total_batches > 0:
            chart_text = "\n".join([f"{s}: {'█' * int((c[0]/total_batches)*20) or '▁'} ({c[0]})" for s, c in status_data.items()])
        else:
            chart_text = "No data available"
        self.chart_label.config(text=chart_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardFrame(root, None)
    root.mainloop()
