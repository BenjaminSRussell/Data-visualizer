import unittest
from unittest.mock import patch
import tkinter as tk
import pandas as pd
import sys
import os
from pathlib import Path

# Add src to python path to allow for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from data_visualizer.gui.main import App

class TestGui(unittest.TestCase):

    def setUp(self):
        """Set up the test environment for each test."""
        # The App class is the root window. We create it and withdraw it
        # to prevent it from appearing during tests.
        self.app = App()
        self.app.withdraw()

    def tearDown(self):
        """Tear down the test environment."""
        self.app.destroy()

    def test_app_initialization(self):
        """Test that the application initializes correctly."""
        self.assertIsInstance(self.app, App)
        self.assertEqual(self.app.title(), "Data Visualizer Toolkit")
        self.assertIsNone(self.app.df)
        self.assertGreater(len(self.app.visualizations), 0)

    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.messagebox.showinfo')
    def test_load_csv_success(self, mock_showinfo, mock_askopenfilename):
        """Test successful CSV loading and data preview update."""
        # Create a dummy CSV file for the test
        dummy_csv_path = "tests/dummy_data.csv"
        dummy_df = pd.DataFrame({'col1': [1, 3], 'col2': [2, 4]})
        dummy_df.to_csv(dummy_csv_path, index=False)

        mock_askopenfilename.return_value = dummy_csv_path

        self.app.load_csv()

        # Check that the dataframe was loaded
        self.assertIsNotNone(self.app.df)
        pd.testing.assert_frame_equal(self.app.df, dummy_df)

        # Check that the success message was called
        mock_showinfo.assert_called_once()

        # Check that the data preview table was updated
        self.assertEqual(len(self.app.data_tree.get_children()), 2)
        self.assertEqual(self.app.data_tree.item(self.app.data_tree.get_children()[0])['values'], [1, 2])

        # Clean up dummy file
        os.remove(dummy_csv_path)

    @patch('tkinter.filedialog.askopenfilename')
    def test_load_csv_cancel(self, mock_askopenfilename):
        """Test cancelling the file dialog."""
        mock_askopenfilename.return_value = "" # Simulate user cancelling

        initial_df = self.app.df
        self.app.load_csv()

        self.assertIs(self.app.df, initial_df)

    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.messagebox.showerror')
    def test_load_csv_error(self, mock_showerror, mock_askopenfilename):
        """Test loading a malformed CSV file."""
        dummy_csv_path = "tests/bad_data.csv"
        with open(dummy_csv_path, "w") as f:
            f.write("col1,col2\n1,2,3\n4,5") # Malformed row

        mock_askopenfilename.return_value = dummy_csv_path

        self.app.load_csv()

        self.assertIsNone(self.app.df)
        mock_showerror.assert_called_once()

        os.remove(dummy_csv_path)

    def test_control_panel_generation(self):
        """Test that the control panel is generated correctly when a viz is selected."""
        # Load some data first
        self.app.df = pd.DataFrame({'date': ['2023-01-01'], 'value': [10]})

        # Select the "Line Chart" visualization (assuming it's the first one)
        self.app.viz_listbox.selection_set(0)
        self.app.on_viz_select(None) # Manually trigger the event handler

        # Check that control widgets were created
        self.assertGreater(len(self.app.control_widgets), 0)
        # Check for a specific control from the line chart schema
        labels = [w.label for w in self.app.control_widgets]
        self.assertIn("Rolling Average Window", labels)

if __name__ == '__main__':
    unittest.main()