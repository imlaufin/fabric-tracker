import tkinter as tk
from tkinter import ttk
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
