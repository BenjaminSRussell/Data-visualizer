"""Comparative grouping through clustered bars - reveals performance gaps across categories.

Smart comparison engine that transforms grouped data into visual stories about relative
performance. Perfect for spotting winners/losers across regions, time periods, or segments.

Future thinking: Interactive drill-downs, statistical significance testing, automatic
insight generation, and dynamic grouping based on similarity patterns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ..base import Visualization, VisualizationMetadata
from ...globals import CHART_DEFAULTS, get_palette_for_categories, get_timestamped_filename


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
        """Data wrangling and validation - ensures clean categorical groupings for comparison.

        Future: Auto-detect optimal groupings, handle temporal data, smart category merging."""
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
        """Visual rendering engine - transforms data into compelling comparison stories.

        Future: Real-time interactivity, animated transitions, AI-generated insights."""
        try:
            import seaborn as sns
            from matplotlib import pyplot as plt
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install seaborn and matplotlib to use the grouped bar visualization.") from exc

        group_col, category_col, value_col = df.columns[:3]

        # Configuration with global color intelligence
        defaults = CHART_DEFAULTS["grouped_bar"]
        figsize = self.config.get("figsize", (10, 6))

        # Smart palette selection based on data complexity
        n_categories = df[df.columns[1]].nunique()
        palette_style = self.config.get("palette_style", "corporate_safe")
        colors = get_palette_for_categories(n_categories, palette_style)

        aggregation = self.config.get("aggregation", "sum")
        sort_by = self.config.get("sort_by", None)
        title_override = self.config.get("title", self.metadata.title)
        show_values = self.config.get("show_values", False)
        normalize = self.config.get("normalize", False)
        chart_type = self.config.get("chart_type", "grouped")  # "grouped", "stacked", "percent_stacked"

        # Aggregation function mapping
        agg_funcs = {
            "sum": sum,
            "mean": np.mean,
            "median": np.median,
            "count": len,
            "std": np.std
        }

        estimator = agg_funcs.get(aggregation, sum)

        # Apply normalization if requested
        if normalize or chart_type == "percent_stacked":
            # Group data and calculate group totals for normalization
            grouped_data = df.groupby([group_col, category_col])[value_col].apply(estimator).reset_index()
            group_totals = grouped_data.groupby(group_col)[value_col].sum()

            # Normalize to percentages within each group
            for group in group_totals.index:
                mask = grouped_data[group_col] == group
                if group_totals[group] > 0:  # Avoid division by zero
                    grouped_data.loc[mask, value_col] = (
                        grouped_data.loc[mask, value_col] / group_totals[group] * 100
                    )

            # Use the normalized data for plotting
            df = grouped_data

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

        # Choose plotting method based on chart type
        if chart_type in ["stacked", "percent_stacked"]:
            # Create stacked bar chart
            pivot_data = df.pivot_table(
                values=value_col,
                index=group_col,
                columns=category_col,
                aggfunc=estimator,
                fill_value=0
            )

            # Reorder based on group_order
            pivot_data = pivot_data.reindex(group_order)

            ax = pivot_data.plot(
                kind='bar',
                stacked=True,
                color=colors[:len(pivot_data.columns)],
                figsize=figsize,
                width=0.8
            )
        else:
            # Main bar plot with intelligent color application
            ax = sns.barplot(
                data=df,
                x=group_col,
                y=value_col,
                hue=category_col,
                estimator=estimator if not normalize else 'mean',  # Use mean for pre-aggregated normalized data
                palette=colors,
                order=group_order,
                errorbar=self.config.get("error_bars", None)
            )

        # Apply global styling preferences
        ax.set_facecolor(defaults["background"])

        # Customize the plot
        plt.title(title_override, fontsize=14, fontweight='bold')
        plt.xlabel(group_col.replace('_', ' ').title(), fontsize=12)

        # Update y-axis label based on normalization and chart type
        if normalize or chart_type == "percent_stacked":
            plt.ylabel("Percentage (%)", fontsize=12)
        else:
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

        # Generate timestamped filename for unique outputs
        timestamped_filename = get_timestamped_filename(self.metadata.key)
        final_output_path = output_path.parent / timestamped_filename

        # Save with professional quality settings
        plt.savefig(final_output_path, dpi=300, bbox_inches='tight',
                   facecolor=defaults["background"], edgecolor='none')
        plt.close()

        return final_output_path
