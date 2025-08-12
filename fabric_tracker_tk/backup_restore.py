import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime
import db


class BackupRestoreFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Backup & Restore Database", font=("Arial", 14, "bold")).pack(pady=10)

        # Backup Button
        ttk.Button(self, text="Backup Database", command=self.backup_db).pack(pady=10)

        # Restore Button
        ttk.Button(self, text="Restore Database", command=self.restore_db).pack(pady=10)

        # Status Label
        self.status_label = ttk.Label(self, text="", foreground="blue")
        self.status_label.pack(pady=5)

    def backup_db(self):
        try:
            db_path = db.get_db_path()
            if not os.path.exists(db_path):
                self.status_label.config(text="Database file not found!", foreground="red")
                return

            # Ask where to save
            save_path = filedialog.asksaveasfilename(
                defaultextension=".sqlite",
                filetypes=[("SQLite Database", "*.sqlite")],
                initialfile=f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.sqlite"
            )
            if not save_path:
                return

            shutil.copy2(db_path, save_path)
            self.status_label.config(text=f"Backup saved to {save_path}", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Backup failed: {e}", foreground="red")

    def restore_db(self):
        try:
            restore_path = filedialog.askopenfilename(
                title="Select Backup File",
                filetypes=[("SQLite Database", "*.sqlite")]
            )
            if not restore_path:
                return

            confirm = messagebox.askyesno("Confirm Restore",
                                          "Restoring will overwrite your current database. Continue?")
            if not confirm:
                return

            db_path = db.get_db_path()
            shutil.copy2(restore_path, db_path)
            self.status_label.config(text="Database restored successfully. Restart app to apply changes.",
                                     foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Restore failed: {e}", foreground="red")
