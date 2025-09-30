import tkinter as tk
from tkinter import ttk
from .theme import FONTS, COLORS

class ControlWidget(ttk.Frame):
    """Base class for control widgets to ensure a consistent interface."""
    def __init__(self, parent, option_key, details, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.option_key = option_key
        self.details = details
        self.label = details.get("label", option_key)
        self.configure(style="TFrame")

    def get_value(self):
        """Return the current value of the control."""
        raise NotImplementedError

class LabeledCheckbox(ControlWidget):
    """A styled checkbox for boolean options."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent, option_key, details)
        self.configure(style="Panel.TFrame")
        self.var = tk.BooleanVar(value=details.get("default", False))
        self.checkbox = ttk.Checkbutton(self, text=self.label, variable=self.var, style="TCheckbutton")
        self.checkbox.pack(fill=tk.X, padx=5, pady=5)

    def get_value(self):
        return self.var.get()

class LabeledEntry(ControlWidget):
    """A styled entry field for numeric or text input."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent, option_key, details)
        self.configure(style="Panel.TFrame")

        ttk.Label(self, text=self.label, font=FONTS["label"], background=COLORS["panel"]).pack(fill=tk.X, padx=5, pady=(5, 0))
        self.var = tk.StringVar(value=details.get("default", ""))
        self.entry = ttk.Entry(self, textvariable=self.var, style="TEntry")
        self.entry.pack(fill=tk.X, padx=5, pady=5, expand=True)

    def get_value(self):
        val = self.var.get()
        dtype = self.details.get("type")
        try:
            if dtype == "integer":
                if not val: return self.details.get("default", 0)
                return int(val)
            if dtype == "float":
                if not val: return self.details.get("default", 0.0)
                return float(val)
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for '{self.label}'. Expected an {dtype}.")

class LabeledDropdown(ControlWidget):
    """A styled dropdown menu for single-selection options."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent, option_key, details)
        self.configure(style="Panel.TFrame")

        ttk.Label(self, text=self.label, font=FONTS["label"], background=COLORS["panel"]).pack(fill=tk.X, padx=5, pady=(5, 0))
        self.var = tk.StringVar(value=details.get("default"))

        self.dropdown = ttk.Combobox(
            self,
            textvariable=self.var,
            values=details.get("options", []),
            font=FONTS["body"],
            state="readonly"
        )
        self.dropdown.pack(fill=tk.X, padx=5, pady=5, expand=True)

    def get_value(self):
        return self.var.get()

class LabeledMultiSelect(ControlWidget):
    """A styled listbox for multiple-selection options."""
    def __init__(self, parent, option_key, details, data_columns):
        super().__init__(parent, option_key, details)
        self.configure(style="Panel.TFrame")

        ttk.Label(self, text=self.label, font=FONTS["label"], background=COLORS["panel"]).pack(fill=tk.X, padx=5, pady=(5, 0))

        list_frame = ttk.Frame(self, style="TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            height=6,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONTS["body"],
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            borderwidth=1,
            relief="solid"
        )

        options = details.get("options", [])
        if options == "data_columns":
            options = data_columns

        for option in options:
            self.listbox.insert(tk.END, option)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

    def get_value(self):
        selected_indices = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected_indices]