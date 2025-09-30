# GUI Guide: The Data Visualizer Toolkit

Welcome to the official guide for the Data Visualizer Toolkit's graphical user interface (GUI). This document provides a complete walkthrough of the application, designed to help you get the most out of its interactive features.

The GUI provides a professional, intuitive, and cross-platform compatible environment for data exploration and visualization.

## 1. Launching the Application

To get started, launch the GUI by running the following command from the root directory of the project:

```bash
python -m src.data_visualizer.gui.main
```

This will open the main application window, which is divided into three main sections: the **Sidebar** on the left, the **Canvas** in the center, and the **Control Panel** on the right.

---

## 2. The Workflow: From Data to Plot

The application is designed around a simple, linear workflow:

1.  **Load Your Data**: Start by loading a CSV file.
2.  **Explore Your Data**: Use the Data Preview tab to inspect the raw data and summary statistics.
3.  **Select a Visualization**: Choose the type of plot you want to create.
4.  **Customize Your Plot**: Use the interactive controls to fine-tune the visualization.
5.  **Generate and Explore**: View the plot and continue to adjust it in real-time.

### Step 1: Load a Dataset

In the top-left corner of the sidebar, click the **"Load Dataset"** button. This will open your system's native file dialog. The application is configured to accept **`.csv`** files.

Once a file is loaded successfully, a confirmation message will appear, and the application will be ready for the next step.

### Step 2: Select a Visualization

The list in the left sidebar displays all the visualizations available in the toolkit. Simply click on a visualization from the list to select it. When you do, the **Control Panel** on the right will automatically populate with the options available for that specific plot.

### Step 3: Use the Interactive Controls

The **Control Panel** on the right is the heart of the interactive experience. It dynamically displays a set of styled widgets that allow you to customize the selected visualization.

#### The Custom Color Picker
For visualizations that support color palettes, a **"Set Custom Colors"** button will appear at the bottom of the control panel. Clicking this button will open a color picker dialog.

You can select multiple colors, one by one, to create a custom palette for your plot. These custom colors will override the default palette selection.

### Step 4: Explore Your Data

The central part of the application is a tabbed canvas that lets you switch between viewing your plot and inspecting your data.

*   **The Data Preview Tab**: When you load a dataset, this tab is automatically populated with the raw data and summary statistics, allowing you to inspect and validate your data before visualizing it.
*   **The Plot Tab**: This is where your visualizations come to life. Click the **"Generate Plot"** button to render the visualization. For a more interactive experience, ensure the **"Auto-Regenerate"** checkbox is ticked, and the plot will update automatically whenever you change a control.

---

## 5. Error Handling and Logging

The application includes a robust logging system to help with debugging. All significant actions, warnings, and errors are logged to a file named `app.log` in the root directory. If you encounter an issue, this file will contain detailed information that can help diagnose the problem.

We hope you enjoy the new interactive experience of the Data Visualizer Toolkit!