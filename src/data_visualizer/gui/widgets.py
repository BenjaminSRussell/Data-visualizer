import tkinter as tk
from tkinter import ttk

class ControlWidget(tk.Frame):
    """Base class for control widgets."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent)
        self.option_key = option_key
        self.details = details
        self.label = details.get("label", option_key)

    def get_value(self):
        raise NotImplementedError

class LabeledCheckbox(ControlWidget):
    """A checkbox with a label."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent, option_key, details)
        self.var = tk.BooleanVar(value=details.get("default", False))
        self.checkbox = ttk.Checkbutton(self, text=self.label, variable=self.var)
        self.checkbox.pack(fill=tk.X, padx=5, pady=2)

    def get_value(self):
        return self.var.get()

class LabeledEntry(ControlWidget):
    """An entry field with a label."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent, option_key, details)

        ttk.Label(self, text=self.label).pack(fill=tk.X, padx=5)
        self.var = tk.StringVar(value=details.get("default", ""))
        self.entry = ttk.Entry(self, textvariable=self.var)
        self.entry.pack(fill=tk.X, padx=5, pady=2)

    def get_value(self):
        # Attempt to cast to the correct type (int, float)
        val = self.var.get()
        if self.details.get("type") == "integer":
            return int(val) if val else self.details.get("default", 0)
        if self.details.get("type") == "float":
            return float(val) if val else self.details.get("default", 0.0)
        return val

class LabeledDropdown(ControlWidget):
    """A dropdown with a label."""
    def __init__(self, parent, option_key, details):
        super().__init__(parent, option_key, details)

        ttk.Label(self, text=self.label).pack(fill=tk.X, padx=5)
        self.var = tk.StringVar(value=details.get("default"))
        self.dropdown = ttk.Combobox(self, textvariable=self.var, values=details.get("options", []))
        self.dropdown.pack(fill=tk.X, padx=5, pady=2)

    def get_value(self):
        return self.var.get()

class LabeledMultiSelect(ControlWidget):
    """A multi-select listbox with a label."""
    def __init__(self, parent, option_key, details, data_columns):
        super().__init__(parent, option_key, details)

        ttk.Label(self, text=self.label).pack(fill=tk.X, padx=5)
        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=5, exportselection=False)

        options = details.get("options", [])
        if options == "data_columns":
            options = data_columns

        for option in options:
            self.listbox.insert(tk.END, option)

        self.listbox.pack(fill=tk.X, padx=5, pady=2)

    def get_value(self):
        selected_indices = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected_indices]