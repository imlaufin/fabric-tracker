import tkinter as tk
from tkinter import ttk, messagebox
import db

def lighten_color(hex_color, factor=0.85):
    """Lighten the given hex color for row backgrounds."""
    if not hex_color or not hex_color.startswith("#"):
        return ""
    try:
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(int(min(255, c + (255 - c) * (1 - factor))) for c in rgb)
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
    except:
        return ""

class FabricatorsNotebook(ttk.Notebook):
    def __init__(self, parent, fabricators, on_jump_to_tab):
        super().__init__(parent)
        self.fabricators = fabricators  # list of dict/rows
        self.on_jump_to_tab = on_jump_to_tab
        self.tabs_by_id = {}
        self.build_tabs()

    def build_tabs(self):
        for fab in self.fabricators:
            if fab["type"] == "knitting_unit":
                frame = KnittingUnitFrame(self, fab
