import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime
from fabric_tracker_tk import db

# Always use the same persistent backup directory as db.py
BACKUP_DIR = db.BACKUP_PATH
MAX_BACKUPS = db.MAX_BACKUPS

class BackupRestoreFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup directory: {e}")
            return
        self.build_ui()
        self.refresh_backup_list()

    def build_ui(self):
        ttk.Label(self, text="Backup & Restore Database", font=("Arial", 14, "bold")).pack(pady=10)

        # Show the backup folder path so users know where files are
        ttk.Label(self, text=f"Backup folder: {BACKUP_DIR}", foreground="gray").pack()

        # Backup Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Backup Now (Auto)", command=self.backup_db_auto).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Backup & Save As...", command=self.backup_db_manual).pack(side="left", padx=5)

        # Restore Button
        ttk.Button(self, text="Restore from Selected Backup", command=self.restore_db).pack(pady=10)

        # Backup List
        self.backup_list = ttk.Treeview(self, columns=("file", "date"), show="headings", height=8)
        self.backup_list.heading("file", text="Backup File")
        self.backup_list.heading("date", text="Created At")
        self.backup_list.column("file", width=300)
        self.backup_list.column("date", width=150)
        self.backup_list.pack(fill="x", padx=10, pady=5)

        # Status Label
        self.status_label = ttk.Label(self, text="", foreground="blue")
        self.status_label.pack(pady=5)

    def refresh_backup_list(self):
        for r in self.backup_list.get_children():
            self.backup_list.delete(r)
        try:
            files = sorted(
                [f for f in os.listdir(BACKUP_DIR) if f.startswith("fabric_backup_")],
                reverse=True
            )
            for f in files:
                path = os.path.join(BACKUP_DIR, f)
                created = datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M:%S")
                self.backup_list.insert("", "end", values=(f, created))
        except FileNotFoundError:
            self.status_label.config(text="Backup directory not found.", foreground="red")
        except Exception as e:
            self.status_label.config(text=f"Failed to refresh backup list: {e}", foreground="red")

    def backup_db_auto(self):
        """Use db.backup_db() so both auto-backup paths stay in sync."""
        try:
            dest = db.backup_db()
            self.status_label.config(text=f"Backup created: {dest}", foreground="green")
            self.refresh_backup_list()
        except Exception as e:
            self.status_label.config(text=f"Backup failed: {e}", foreground="red")

    def backup_db_manual(self):
        try:
            db_path = db.get_db_path()
            save_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
                initialfile=f"fabric_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
            )
            if not save_path:
                return
            with open(db_path, "rb") as src, open(save_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            self.status_label.config(text=f"Backup saved to: {save_path}", foreground="green")
            self.refresh_backup_list()
        except Exception as e:
            self.status_label.config(text=f"Backup failed: {e}", foreground="red")

    def restore_db(self):
        try:
            sel = self.backup_list.selection()
            if not sel:
                messagebox.showinfo("Select Backup", "Please select a backup from the list to restore.")
                return
            backup_file = self.backup_list.item(sel[0])["values"][0]
            restore_path = os.path.join(BACKUP_DIR, backup_file)

            confirm = messagebox.askyesno(
                "Confirm Restore",
                "Restoring will overwrite your current database.\n"
                "The app must be restarted after restoring. Continue?"
            )
            if not confirm:
                return

            db_path = db.get_db_path()
            with open(restore_path, "rb") as src, open(db_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            self.status_label.config(
                text="Database restored successfully. Please restart the app to apply changes.",
                foreground="green"
            )
        except Exception as e:
            self.status_label.config(text=f"Restore failed: {e}", foreground="red")
