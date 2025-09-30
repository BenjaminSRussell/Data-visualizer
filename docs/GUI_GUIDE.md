# GUI Guide for the Data Visualizer Toolkit

This guide provides a comprehensive overview of the new graphical user interface (GUI) for the Data Visualizer Toolkit. The GUI provides an interactive way to explore your data and generate visualizations without writing any code.

## Getting Started

To launch the GUI, run the following command from the root of the repository:

```bash
python -m src.data_visualizer.gui.main
```

This will open the main application window.

## Using the GUI

The GUI is designed to be intuitive and easy to use. Here's a step-by-step guide to generating your first visualization.

### 1. Loading Data

The first step is to load a dataset. The GUI currently supports CSV files.

1.  Click on the **File** menu in the top-left corner of the application.
2.  Select **Open CSV**.
3.  In the file dialog, navigate to and select your desired CSV file.

Once the file is loaded, a confirmation message will appear with the dimensions of the dataset.

### 2. Selecting a Visualization

After loading a dataset, you can choose a visualization from the list on the left-hand side of the application.

1.  The **Visualizations** panel displays all the available plot types.
2.  Click on a visualization to select it.
3.  A description of the selected visualization and its tags will appear below the list.

### 3. Using Interactive Controls

When you select a visualization, the **Controls** panel will dynamically update with a set of options that are specific to that plot. These controls allow you to customize the appearance and behavior of the visualization.

The available controls include:

*   **Checkboxes**: For toggling boolean options (e.g., "Detect Anomalies").
*   **Text Fields**: for entering numerical or text values (e.g., "Rolling Average Window").
*   **Dropdown Menus**: For selecting from a list of predefined options (e.g., "Chart Type").
*   **Multi-Select Lists**: For choosing one or more columns from your dataset.

### 4. Generating Plots

Once you have selected a visualization and configured its options, you can generate the plot.

*   **Manual Generation**: Click the **Generate Plot** button to render the visualization with the current settings.
*   **Automatic Regeneration**: For a more interactive experience, ensure the **Auto-Regenerate** checkbox is ticked. With this option enabled, the plot will automatically update whenever you change a control.

The generated plot will be displayed in the main area of the window.

## Project Structure

The GUI code is organized in a new directory: `src/data_visualizer/gui`. This directory contains the following files:

*   `main.py`: The main entry point for the GUI application. It contains the main window, layout, and logic for interacting with the visualization library.
*   `widgets.py`: A collection of custom `tkinter` widgets used to build the dynamic controls panel.

This structure separates the GUI code from the core visualization logic, making the project easier to maintain and extend in the future.