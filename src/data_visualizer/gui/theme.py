import tkinter as tk
from tkinter import ttk
import platform

# --- Color Palette ---
COLORS = {
    "background": "#F5F5F5",
    "panel": "#FFFFFF",
    "text": "#333D29",
    "accent": "#2E86AB",
    "border": "#E0E0E0",
    "danger": "#C73E1D",
    "success": "#588157",
}

# --- Typography ---
def get_font_family():
    """Return platform-appropriate font family."""
    if platform.system() == "Darwin":  # macOS
        return "Helvetica"
    elif platform.system() == "Windows":
        return "Arial"
    else:  # Linux, etc.
        return "sans-serif"

FONT_FAMILY = get_font_family()
FONTS = {
    "header": (FONT_FAMILY, 14, "bold"),
    "label": (FONT_FAMILY, 10, "normal"),
    "body": (FONT_FAMILY, 10, "normal"),
    "button": (FONT_FAMILY, 10, "bold"),
}

def apply_theme():
    """Apply the custom theme to the application using ttk.Style."""
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')

    # --- General Widget Styling ---
    style.configure(".",
                    background=COLORS["background"],
                    foreground=COLORS["text"],
                    font=FONTS["body"],
                    borderwidth=0,
                    focusthickness=3,
                    focuscolor=COLORS["accent"])

    # --- Frame Styling ---
    style.configure("TFrame",
                    background=COLORS["background"])
    style.configure("Panel.TFrame",
                    background=COLORS["panel"],
                    borderwidth=1,
                    relief="solid")

    # --- LabelFrame Styling ---
    style.configure("TLabelFrame",
                    background=COLORS["panel"],
                    borderwidth=1,
                    relief="solid",
                    padding=10)
    style.configure("TLabelFrame.Label",
                    background=COLORS["panel"],
                    foreground=COLORS["text"],
                    font=FONTS["header"])

    # --- Button Styling ---
    style.configure("TButton",
                    background=COLORS["accent"],
                    foreground="white",
                    font=FONTS["button"],
                    borderwidth=0,
                    padding=(12, 6),
                    relief="flat")
    style.map("TButton",
              background=[('active', '#266A8B')],
              foreground=[('active', 'white')])

    # --- Notebook (Tabs) Styling ---
    style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=COLORS["background"],
                    foreground=COLORS["text"],
                    padding=[10, 5],
                    font=FONTS["label"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["panel"])],
              foreground=[("selected", COLORS["accent"])])

    # --- Treeview Styling ---
    style.configure("Treeview",
                    background=COLORS["panel"],
                    foreground=COLORS["text"],
                    fieldbackground=COLORS["panel"],
                    rowheight=25,
                    font=FONTS["body"])
    style.map("Treeview",
              background=[('selected', COLORS["accent"])],
              foreground=[('selected', 'white')])
    style.configure("Treeview.Heading",
                    background=COLORS["background"],
                    font=FONTS["button"])

    # --- Scrollbar ---
    style.configure("TScrollbar", troughcolor=COLORS["background"], background=COLORS["accent"])