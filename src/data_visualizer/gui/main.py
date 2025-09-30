import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Add src to python path to allow for imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from data_visualizer.logger import log
from data_visualizer.gui.theme import apply_theme, FONTS, COLORS
from data_visualizer.gui.widgets import (
    LabeledCheckbox, LabeledEntry, LabeledDropdown, LabeledMultiSelect
)
from data_visualizer.gui.color_picker_dialog import ColorPickerDialog
from data_visualizer import list_visualizations, load_visualization
from data_visualizer.globals import SCHEMA_REQUIREMENTS

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        log.info("Initializing application...")
        self.title("Data Visualizer Toolkit")
        self.geometry("1400x900")

        # App state
        self.df = None
        self.visualizations = {viz.key: viz for viz in list_visualizations()}
        self.control_widgets = []
        self.custom_colors = []
        self.current_canvas = None

        apply_theme()
        self.configure(background=COLORS["background"])

        self.create_layout()
        self.populate_visualizations()
        log.info("Application initialized successfully.")

    def create_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Left Sidebar ---
        left_sidebar = ttk.Frame(self, width=300, style="Panel.TFrame")
        left_sidebar.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        left_sidebar.grid_propagate(False)
        left_sidebar.grid_rowconfigure(1, weight=1)

        load_button = ttk.Button(left_sidebar, text="Load Dataset", command=self.load_csv)
        load_button.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        viz_frame = ttk.LabelFrame(left_sidebar, text="Visualizations")
        viz_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)

        self.viz_listbox = tk.Listbox(
            viz_frame, bg=COLORS["panel"], fg=COLORS["text"], font=FONTS["body"], height=10,
            highlightthickness=0, borderwidth=0, selectbackground=COLORS["accent"],
            selectforeground="white", exportselection=False
        )
        self.viz_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.viz_listbox.bind("<<ListboxSelect>>", self.on_viz_select)

        # --- Center Canvas (Notebook) ---
        center_notebook = ttk.Notebook(self)
        center_notebook.grid(row=0, column=1, sticky="nsew", pady=10)

        self.plot_tab = ttk.Frame(center_notebook, style="TFrame")
        center_notebook.add(self.plot_tab, text="Plot")
        self.plot_tab.grid_rowconfigure(0, weight=1)
        self.plot_tab.grid_columnconfigure(0, weight=1)

        self.plot_frame = ttk.LabelFrame(self.plot_tab, text="Plot")
        self.plot_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.placeholder_label = ttk.Label(self.plot_frame, text="Load a dataset and select a visualization.", font=FONTS["header"], justify=tk.CENTER, background=COLORS["panel"])
        self.placeholder_label.pack(expand=True, fill="both", padx=2, pady=2)

        self.data_tab = ttk.Frame(center_notebook, style="TFrame")
        center_notebook.add(self.data_tab, text="Data Preview")
        self.data_tab.grid_rowconfigure(0, weight=3)
        self.data_tab.grid_rowconfigure(1, weight=1)
        self.data_tab.grid_columnconfigure(0, weight=1)

        table_frame = ttk.LabelFrame(self.data_tab, text="Raw Data (First 1000 Rows)")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5,0))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.data_tree = ttk.Treeview(table_frame, show="headings")
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.data_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.data_tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.data_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        stats_frame = ttk.LabelFrame(self.data_tab, text="Summary Statistics")
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        stats_frame.grid_rowconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(0, weight=1)

        self.stats_text = tk.Text(stats_frame, wrap="none", font=("Courier", 9), bg=COLORS["panel"], fg=COLORS["text"], highlightthickness=0, borderwidth=0)
        self.stats_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.stats_text.insert(tk.END, "Load a dataset to see summary statistics.")
        self.stats_text.config(state="disabled")

        # --- Right Control Panel ---
        right_panel = ttk.Frame(self, width=300, style="Panel.TFrame")
        right_panel.grid(row=0, column=2, sticky="ns", padx=(5, 10), pady=10)
        right_panel.grid_propagate(False)
        right_panel.grid_rowconfigure(1, weight=1)

        action_frame = ttk.Frame(right_panel, style="Panel.TFrame")
        action_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        action_frame.grid_columnconfigure(0, weight=1)

        self.generate_button = ttk.Button(action_frame, text="Generate Plot", command=self.generate_plot)
        self.generate_button.grid(row=0, column=0, sticky="ew")

        self.auto_generate = tk.BooleanVar(value=True)
        ttk.Checkbutton(action_frame, text="Auto-Regenerate", variable=self.auto_generate, style="TCheckbutton").grid(row=1, column=0, sticky="w", pady=(5,0))

        self.controls_frame = ttk.LabelFrame(right_panel, text="Controls")
        self.controls_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5,10))

    def populate_visualizations(self):
        log.info("Populating visualization list.")
        for key in self.visualizations.keys():
            self.viz_listbox.insert(tk.END, self.visualizations[key].title)

    def load_csv(self):
        log.info("Opening file dialog for CSV.")
        file_path = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            log.warning("File loading cancelled.")
            return

        log.info(f"Attempting to load file: {file_path}")
        try:
            self.df = pd.read_csv(file_path)
            self.update_data_preview()
            log.info(f"Successfully loaded '{os.path.basename(file_path)}'.")
            messagebox.showinfo("Success", f"Loaded '{os.path.basename(file_path)}' successfully.")
            if self.viz_listbox.curselection(): self.on_viz_select(None)
        except Exception as e:
            log.error(f"Error loading {file_path}: {e}", exc_info=True)
            messagebox.showerror("Error", f"An error occurred while loading the file:\n{e}")
            self.df = None
            self.update_data_preview()

    def update_data_preview(self):
        self.data_tree.delete(*self.data_tree.get_children())
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)

        if self.df is None:
            self.data_tree["columns"] = []
            self.stats_text.insert(tk.END, "Load a dataset to see summary statistics.")
        else:
            self.data_tree["columns"] = self.df.columns.tolist()
            for col in self.df.columns:
                self.data_tree.heading(col, text=col)
                self.data_tree.column(col, width=120, anchor="w")

            for index, row in self.df.head(1000).iterrows():
                self.data_tree.insert("", "end", values=row.tolist())

            self.stats_text.insert("1.0", self.df.describe(include='all').to_string())
        self.stats_text.config(state="disabled")

    def on_viz_select(self, event):
        if not self.viz_listbox.curselection(): return
        self.update_controls_for_selection()
        if self.auto_generate.get(): self.generate_plot()

    def update_controls_for_selection(self):
        if not self.viz_listbox.curselection(): return
        selected_title = self.viz_listbox.get(self.viz_listbox.curselection()[0])
        selected_key = next(k for k, v in self.visualizations.items() if v.title == selected_title)
        self.update_controls(selected_key)

    def update_controls(self, viz_key):
        for widget in self.controls_frame.winfo_children(): widget.destroy()
        self.control_widgets = []
        self.custom_colors = []

        config_options = SCHEMA_REQUIREMENTS.get(viz_key, {}).get("config_options", {})

        for key, details in config_options.items():
            widget_class, widget_args = None, (self.controls_frame, key, details)
            if details["type"] == "boolean": widget_class = LabeledCheckbox
            elif details["type"] in ["integer", "float", "string"]: widget_class = LabeledEntry
            elif details["type"] == "dropdown": widget_class = LabeledDropdown
            elif details["type"] == "multiselect":
                data_cols = self.df.columns.tolist() if self.df is not None else []
                widget_args = (self.controls_frame, key, details, data_cols)
                widget_class = LabeledMultiSelect

            if widget_class:
                widget = widget_class(*widget_args)
                widget.pack(fill=tk.X, padx=5, pady=5)
                self.control_widgets.append(widget)
                if hasattr(widget, 'var'): widget.var.trace("w", lambda *_: self.on_control_change())
                elif hasattr(widget, 'listbox'): widget.listbox.bind("<<ListboxSelect>>", lambda *_: self.on_control_change())
                elif hasattr(widget, 'dropdown'): widget.dropdown.bind("<<ComboboxSelected>>", lambda *_: self.on_control_change())

        if any('palette' in k or 'color_scheme' in k for k in config_options):
            ttk.Button(self.controls_frame, text="Set Custom Colors", command=self.launch_color_picker).pack(pady=10, fill=tk.X, padx=5)

    def on_control_change(self):
        if self.auto_generate.get(): self.generate_plot()

    def launch_color_picker(self):
        dialog = ColorPickerDialog(self, initial_colors=self.custom_colors)
        result = dialog.show()
        if result is not None:
            self.custom_colors = result
            log.info(f"Custom color palette updated: {self.custom_colors}")
            if self.auto_generate.get():
                self.generate_plot()

    def get_current_config(self):
        config = {}
        for widget in self.control_widgets:
            try:
                config[widget.option_key] = widget.get_value()
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
                log.error(f"Invalid input in control '{widget.label}': {e}")
                return None
        if self.custom_colors:
            config['colors'] = self.custom_colors
        return config

    def get_selected_viz_key(self):
        if not self.viz_listbox.curselection(): return None
        selected_title = self.viz_listbox.get(self.viz_listbox.curselection()[0])
        return next((k for k, v in self.visualizations.items() if v.title == selected_title), None)

    def generate_plot(self):
        selected_key = self.get_selected_viz_key()
        if not selected_key:
            messagebox.showwarning("Warning", "Please select a visualization.")
            return

        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first.")
            return

        log.info(f"Generating plot for '{selected_key}'")
        config = self.get_current_config()
        if config is None: return # Stop if config is invalid

        try:
            if self.current_canvas: self.current_canvas.get_tk_widget().destroy()
            self.placeholder_label.pack_forget()

            viz_class = load_visualization(selected_key)
            viz_instance = viz_class(config=config)

            fig_capture = []
            original_render = viz_instance.render
            def gui_render(df, output_path):
                plt.figure()
                result = original_render(df, output_path)
                fig_capture.append(plt.gcf())
                plt.close()
                return result
            viz_instance.render = gui_render

            processed_df = viz_instance.prepare_data(self.df.copy())

            output_dir = Path("./gui_outputs")
            output_dir.mkdir(exist_ok=True)
            viz_instance.run(processed_df, output_dir)

            if fig_capture and fig_capture[0].get_axes():
                fig = fig_capture[0]
                fig.set_facecolor(COLORS["panel"])
                for ax in fig.get_axes():
                    ax.set_facecolor(COLORS["panel"])
                    ax.tick_params(colors=COLORS["text"])
                    ax.spines['bottom'].set_color(COLORS["border"])
                    ax.spines['top'].set_color(COLORS["border"])
                    ax.spines['right'].set_color(COLORS["border"])
                    ax.spines['left'].set_color(COLORS["border"])
                    ax.yaxis.label.set_color(COLORS["text"])
                    ax.xaxis.label.set_color(COLORS["text"])
                    ax.title.set_color(COLORS["text"])

                self.current_canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                self.current_canvas.draw()
                self.current_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
            else:
                self.placeholder_label.pack(expand=True, fill="both")
                messagebox.showinfo("Info", "Plotting resulted in an empty figure.")
        except Exception as e:
            log.error(f"Failed to generate plot for {selected_key}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate plot:\n{e}\n\nSee app.log for more details.")

def main():
    repo_root = Path(__file__).parent.parent.parent.parent
    os.chdir(repo_root)
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        log.critical(f"Unhandled exception: {e}", exc_info=True)
        messagebox.showerror("Critical Error", "A critical error occurred. See app.log for details.")

if __name__ == "__main__":
    main()