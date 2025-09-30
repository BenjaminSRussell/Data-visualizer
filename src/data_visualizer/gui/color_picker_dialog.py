import tkinter as tk
from tkinter import ttk, colorchooser
from .theme import FONTS, COLORS

class ColorPickerDialog(tk.Toplevel):
    """A dialog for creating a custom color palette."""

    def __init__(self, parent, initial_colors=None):
        super().__init__(parent)
        self.title("Custom Color Palette")
        self.geometry("350x400")
        self.parent = parent
        self.result = None

        self.transient(parent)
        self.grab_set()

        # --- Data ---
        self.colors = tk.Variable(value=initial_colors or [])

        # --- Widgets ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)

        # Color List
        list_frame = ttk.LabelFrame(main_frame, text="Selected Colors")
        list_frame.grid(row=0, column=0, sticky="nsew", columnspan=2, pady=(0, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.color_listbox = tk.Listbox(
            list_frame,
            listvariable=self.colors,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectmode=tk.SINGLE,
            height=8
        )
        self.color_listbox.grid(row=0, column=0, sticky="nsew")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        add_button = ttk.Button(button_frame, text="Add Color", command=self.add_color)
        add_button.pack(side=tk.LEFT, padx=(0, 5))

        remove_button = ttk.Button(button_frame, text="Remove Selected", command=self.remove_color)
        remove_button.pack(side=tk.LEFT)

        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side=tk.RIGHT)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def add_color(self):
        """Open color chooser and add the selected color to the list."""
        color = colorchooser.askcolor(title="Choose a color")
        if color[1]:
            current_colors = self.colors.get()
            self.colors.set(current_colors + [color[1]])

    def remove_color(self):
        """Remove the selected color from the list."""
        selection = self.color_listbox.curselection()
        if selection:
            self.color_listbox.delete(selection[0])

    def on_ok(self):
        """Set the result and close the dialog."""
        self.result = list(self.color_listbox.get(0, tk.END))
        self.destroy()

    def on_cancel(self):
        """Close the dialog without setting a result."""
        self.destroy()

    def show(self):
        """Show the dialog and wait for it to close."""
        self.wait_window()
        return self.result