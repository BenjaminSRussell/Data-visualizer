import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
import sys
from pathlib import Path

# Add src to python path to allow for imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))


from data_visualizer import list_visualizations, load_visualization
from data_visualizer.globals import SCHEMA_REQUIREMENTS
from data_visualizer.gui.widgets import (
    LabeledCheckbox, LabeledEntry, LabeledDropdown, LabeledMultiSelect
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Data Visualizer Toolkit")
        self.geometry("1400x900")
        self.df = None
        self.visualizations = {viz.key: viz for viz in list_visualizations()}
        self.current_canvas = None
        self.control_widgets = []


        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open CSV", command=self.load_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)


        # Left panel for visualization list and controls
        left_panel = tk.Frame(main_frame, width=300)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        # Visualization list
        viz_frame = tk.LabelFrame(left_panel, text="Visualizations")
        viz_frame.pack(fill=tk.X, expand=False)

        self.viz_listbox = tk.Listbox(viz_frame, exportselection=False)
        for key, metadata in self.visualizations.items():
            self.viz_listbox.insert(tk.END, f"{metadata.title} ({key})")
        self.viz_listbox.pack(pady=5, padx=5, fill=tk.X)
        self.viz_listbox.bind("<<ListboxSelect>>", self.on_viz_select)

        # Description box
        self.viz_desc = tk.Text(viz_frame, height=6, wrap="word", relief="flat", bg=self.cget('bg'), state="disabled")
        self.viz_desc.pack(pady=5, padx=5, fill=tk.X)

        # Generate button and auto-gen checkbox
        action_frame = tk.Frame(left_panel)
        action_frame.pack(pady=10, fill=tk.X)

        self.generate_button = ttk.Button(action_frame, text="Generate Plot", command=self.generate_plot)
        self.generate_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.auto_generate = tk.BooleanVar(value=True)
        self.auto_gen_checkbox = ttk.Checkbutton(action_frame, text="Auto-Regenerate", variable=self.auto_generate)
        self.auto_gen_checkbox.pack(side=tk.RIGHT, padx=(10,0))


        # Controls Frame
        self.controls_frame = tk.LabelFrame(left_panel, text="Controls")
        self.controls_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        tk.Label(self.controls_frame, text="Select a visualization.").pack(padx=10, pady=10)


        # Plot display
        self.plot_frame = tk.LabelFrame(main_frame, text="Plot")
        self.plot_frame.grid(row=0, column=1, sticky="nsew")

    def on_viz_select(self, event):
        selection_index = self.viz_listbox.curselection()
        if not selection_index:
            return

        selected_key = list(self.visualizations.keys())[selection_index[0]]
        metadata = self.visualizations[selected_key]

        self.viz_desc.config(state="normal")
        self.viz_desc.delete("1.0", tk.END)
        self.viz_desc.insert(tk.END, f"{metadata.description}\n\nTags: {', '.join(metadata.tags)}")
        self.viz_desc.config(state="disabled")

        self.update_controls(selected_key)

    def update_controls(self, viz_key):
        # Clear existing controls
        for widget in self.controls_frame.winfo_children():
            widget.destroy()
        self.control_widgets = []

        config_options = SCHEMA_REQUIREMENTS.get(viz_key, {}).get("config_options", {})
        if not config_options:
            tk.Label(self.controls_frame, text="No configurable options.").pack(padx=10, pady=10)
            return

        for key, details in config_options.items():
            widget_class = None
            widget_args = (self.controls_frame, key, details)

            if details["type"] == "boolean":
                widget_class = LabeledCheckbox
            elif details["type"] in ["integer", "float", "string"]:
                widget_class = LabeledEntry
            elif details["type"] == "dropdown":
                widget_class = LabeledDropdown
            elif details["type"] == "multiselect":
                widget_class = LabeledMultiSelect
                widget_args = (self.controls_frame, key, details, self.df.columns.tolist() if self.df is not None else [])

            if widget_class:
                widget = widget_class(*widget_args)
                widget.pack(fill=tk.X, padx=5, pady=5)
                self.control_widgets.append(widget)
                # Bind event to auto-generate plot
                if hasattr(widget, 'var'): # Check if widget has a variable to trace
                    widget.var.trace("w", lambda *args, **kwargs: self.on_control_change())
                elif hasattr(widget, 'listbox'):
                    widget.listbox.bind("<<ListboxSelect>>", self.on_control_change)


    def on_control_change(self, *args, **kwargs):
        if self.auto_generate.get():
            self.generate_plot()


    def load_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path)
            messagebox.showinfo("Success", f"Loaded {os.path.basename(file_path)} successfully.\n\nShape: {self.df.shape}")
            # Refresh controls if a visualization is already selected
            selection_index = self.viz_listbox.curselection()
            if selection_index:
                selected_key = list(self.visualizations.keys())[selection_index[0]]
                self.update_controls(selected_key)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def get_current_config(self):
        config = {}
        for widget in self.control_widgets:
            config[widget.option_key] = widget.get_value()
        return config

    def generate_plot(self):
        selection_index = self.viz_listbox.curselection()
        if not selection_index:
            messagebox.showwarning("Warning", "Please select a visualization.")
            return

        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first.")
            return

        selected_key = list(self.visualizations.keys())[selection_index[0]]
        config = self.get_current_config()

        try:
            # Clear previous plot
            if self.current_canvas:
                self.current_canvas.get_tk_widget().destroy()

            viz_class = load_visualization(selected_key)

            output_dir = Path("./gui_outputs")
            output_dir.mkdir(exist_ok=True)

            import matplotlib.pyplot as plt

            viz_instance = viz_class(config=config)

            original_render = viz_instance.render
            fig = None
            def gui_render(df, output_path):
                nonlocal fig
                # Ensure a fresh figure for each render
                plt.close('all')
                fig_obj = plt.figure()
                # The original render function uses plt.gca(), so we need a figure to be active
                original_render(df, output_path)
                fig = fig_obj
                return output_path

            viz_instance.render = gui_render

            processed_df = viz_instance.prepare_data(self.df.copy())

            # The run method calls render, which we've patched
            viz_instance.run(processed_df, output_dir)

            # The original render function might have closed the figure, we need to get it before that.
            # A better way is to have render return the figure object.
            # Let's adjust the patch to capture the figure right away.

            plt.close('all') # clean up any open figures from the library
            fig = plt.figure(figsize=(12,6))
            viz_instance = viz_class(config=config)
            processed_df = viz_instance.prepare_data(self.df.copy())
            # We call render directly, not run, to avoid file I/O side effects if possible
            # and to have more control.
            # The base render in the library saves the figure, so we let it do that
            # but we have the 'fig' object to render in Tkinter.
            viz_instance.render(processed_df, output_dir / f"{selected_key}.png")


            if fig.get_axes(): # Check if something was plotted
                self.current_canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                self.current_canvas.draw()
                self.current_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            else:
                plt.close(fig) # close empty figure
                tk.Label(self.plot_frame, text="Plotting failed or produced an empty figure.").pack()


        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate plot: {e}")
            # Also print to console for more details
            import traceback
            traceback.print_exc()


    def show_about(self):
        messagebox.showinfo(
            "About Data Visualizer Toolkit",
            "This application allows you to create and explore various data visualizations."
        )

def main():
    repo_root = Path(__file__).parent.parent.parent.parent
    os.chdir(repo_root)

    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()