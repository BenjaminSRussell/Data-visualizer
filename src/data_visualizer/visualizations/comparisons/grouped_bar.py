"""Grouped bar chart visualization using seaborn.

This visualization compares sub-categories within discrete groups, making it easy to spot
relative performance differences between peer categories. Each group becomes a cluster of
bars, where each bar represents a sub-category's value.

TODOs:
1. **Custom aggregation functions**: Support mean, median, percentiles via config instead of just sum
2. **Data normalization options**: Add percentage-of-group-total and z-score normalization modes
3. **Missing data handling**: Implement strategies for incomplete category-group combinations
4. **Outlier detection**: Flag and optionally exclude extreme values that skew comparisons
5. **Advanced sorting**: Sort groups by total value, max category, or custom criteria
6. **Error bars and confidence intervals**: Show variability when data represents samples
7. **Color palette management**: Support custom palettes, accessibility modes, and brand colors
8. **Label optimization**: Auto-truncate long labels, rotate for space, add tooltips
9. **Interactive drill-down**: Click groups to filter detailed views, hover for exact values
10. **Summary table export**: Generate comparison matrices showing top/bottom performers per group
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ..base import Visualization, VisualizationMetadata


class GroupedBarChart(Visualization):
    metadata = VisualizationMetadata(
        key="comparison_grouped_bar",
        title="Grouped Bar Chart",
        insight_type="Comparison",
        description="Compare sub-categories within discrete groups.",
        example_url="https://seaborn.pydata.org/examples/grouped_barplot.html",
        tags=("comparison", "categorical", "seaborn"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for grouped bar chart visualization."""
        if df.empty:
            raise ValueError("Input dataframe is empty; provide grouped categorical data.")

        # Get column configuration
        required_cols: Iterable[str] = self.config.get("columns") or df.columns[:3]
        required_cols = tuple(required_cols)

        if len(required_cols) < 3:
            raise ValueError("Grouped bar chart requires three columns (group, category, value).")

        if len(df.columns) < 3:
            raise ValueError("Dataset must have at least 3 columns for group, category, and value.")

        # Select and validate columns
        processed_df = df[list(required_cols)].copy()
        group_col, category_col, value_col = processed_df.columns[:3]

        # Data quality checks
        if processed_df[value_col].isnull().all():
            raise ValueError(f"Value column '{value_col}' contains no valid data.")

        # Drop rows with missing values
        initial_rows = len(processed_df)
        processed_df = processed_df.dropna()
        dropped_rows = initial_rows - len(processed_df)

        if dropped_rows > 0:
            print(f"Warning: Dropped {dropped_rows} rows with missing values.")

        if processed_df.empty:
            raise ValueError("No valid data remaining after removing missing values.")

        # Validate numeric column
        if not pd.api.types.is_numeric_dtype(processed_df[value_col]):
            try:
                processed_df[value_col] = pd.to_numeric(processed_df[value_col], errors='coerce')
                processed_df = processed_df.dropna()
            except:
                raise ValueError(f"Value column '{value_col}' must be numeric.")

        # Check for reasonable cardinality
        max_groups = self.config.get("max_groups", 10)
        max_categories = self.config.get("max_categories", 6)

        n_groups = processed_df[group_col].nunique()
        n_categories = processed_df[category_col].nunique()

        if n_groups > max_groups:
            print(f"Warning: {n_groups} groups detected. Consider filtering or grouping for readability.")

        if n_categories > max_categories:
            print(f"Warning: {n_categories} categories detected. Chart may be cluttered.")

        return processed_df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Render the grouped bar chart with enhanced customization options."""
        try:
            import seaborn as sns
            from matplotlib import pyplot as plt
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install seaborn and matplotlib to use the grouped bar visualization.") from exc

        group_col, category_col, value_col = df.columns[:3]

        # Configuration options
        figsize = self.config.get("figsize", (10, 6))
        palette = self.config.get("color_palette", "colorblind")
        aggregation = self.config.get("aggregation", "sum")
        sort_by = self.config.get("sort_by", None)
        title_override = self.config.get("title", self.metadata.title)
        show_values = self.config.get("show_values", False)

        # Aggregation function mapping
        agg_funcs = {
            "sum": sum,
            "mean": np.mean,
            "median": np.median,
            "count": len,
            "std": np.std
        }

        estimator = agg_funcs.get(aggregation, sum)

        # Sort groups if requested
        if sort_by == "total_value":
            group_totals = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
            group_order = group_totals.index.tolist()
        elif sort_by == "alphabetical":
            group_order = sorted(df[group_col].unique())
        else:
            group_order = df[group_col].unique()

        # Create the plot
        plt.figure(figsize=figsize)

        # Main bar plot
        ax = sns.barplot(
            data=df,
            x=group_col,
            y=value_col,
            hue=category_col,
            estimator=estimator,
            palette=palette,
            order=group_order,
            errorbar=self.config.get("error_bars", None)
        )

        # Customize the plot
        plt.title(title_override, fontsize=14, fontweight='bold')
        plt.xlabel(group_col.replace('_', ' ').title(), fontsize=12)
        plt.ylabel(f"{value_col.replace('_', ' ').title()} ({aggregation})", fontsize=12)

        # Rotate x-axis labels if needed
        if len(group_order) > 5 or any(len(str(g)) > 8 for g in group_order):
            plt.xticks(rotation=45, ha='right')

        # Add value labels on bars if requested
        if show_values:
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', fontsize=9)

        # Customize legend
        legend = plt.legend(title=category_col.replace('_', ' ').title(),
                          bbox_to_anchor=(1.05, 1), loc='upper left')
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_alpha(0.9)

        # Add grid for better readability
        plt.grid(axis='y', alpha=0.3, linestyle='--')

        # Tight layout with extra space for legend
        plt.tight_layout()
        plt.subplots_adjust(right=0.85)

        # Save with high DPI for quality
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        return output_path
