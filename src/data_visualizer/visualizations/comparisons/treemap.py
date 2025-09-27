"""Hierarchical treemap that displays nested categories with area proportional to values.

Advanced hierarchy analyzer that reveals share-of-parent relationships through
proportional area visualization. Perfect for organizational analysis, budget
allocation, market share studies, and any nested categorical data.

Future vision: Interactive drill-down navigation, color-coded variance indicators,
breadcrumb navigation, and automated hierarchy validation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ..base import Visualization, VisualizationMetadata
from ...globals import CHART_DEFAULTS, get_palette_for_categories, get_timestamped_filename


class HierarchyTreemap(Visualization):
    metadata = VisualizationMetadata(
        key="hierarchy_treemap",
        title="Hierarchy Treemap",
        insight_type="Hierarchy",
        description="Render nested categories with area sized by metric to reveal share-of-parent relationships.",
        example_url="https://plotly.com/python/treemaps/",
        tags=("hierarchy", "categorical", "treemap", "plotly"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Data preparation for hierarchical treemap analysis."""
        if df.empty:
            raise ValueError("Input dataframe is empty; provide hierarchical categorical data.")

        # Get column configuration - expect hierarchical columns plus value
        required_cols: Iterable[str] = self.config.get("columns") or df.columns
        required_cols = tuple(required_cols)

        if len(required_cols) < 2:
            raise ValueError("Treemap requires at least two columns (hierarchy + value).")

        if len(df.columns) < 2:
            raise ValueError("Dataset must have at least 2 columns for hierarchy and value.")

        # Select and validate columns
        processed_df = df[list(required_cols)].copy()

        # The last column should be the value column
        value_col = processed_df.columns[-1]
        hierarchy_cols = processed_df.columns[:-1]

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

        # Validate that we have positive values (treemap areas must be positive)
        if (processed_df[value_col] <= 0).any():
            print("Warning: Treemap requires positive values. Negative/zero values will be filtered out.")
            processed_df = processed_df[processed_df[value_col] > 0]

        if processed_df.empty:
            raise ValueError("No positive values remaining for treemap visualization.")

        return processed_df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Create hierarchical treemap visualization."""
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.offline import plot
        except ImportError as exc:
            raise RuntimeError("Install plotly to use the treemap visualization.") from exc

        # Get column configuration
        value_col = df.columns[-1]
        hierarchy_cols = list(df.columns[:-1])

        # Configuration
        title_override = self.config.get("title", self.metadata.title)
        color_column = self.config.get("color_column", None)  # Optional secondary metric for coloring
        color_scheme = self.config.get("color_scheme", "viridis")
        width = self.config.get("width", 1000)
        height = self.config.get("height", 600)
        show_values = self.config.get("show_values", True)
        threshold_filter = self.config.get("threshold_filter", 0)  # Minimum value to include
        pattern_detection = self.config.get("pattern_detection", False)
        export_hierarchy = self.config.get("export_hierarchy", False)
        variance_coloring = self.config.get("variance_coloring", False)
        target_values = self.config.get("target_values", None)  # Dict of targets per category

        # Validate hierarchy structure
        hierarchy_issues = []
        if len(hierarchy_cols) > 1:
            # Check for orphan nodes
            for i in range(1, len(hierarchy_cols)):
                parent_col = hierarchy_cols[i-1]
                child_col = hierarchy_cols[i]

                # Group by parent and check if children exist in other parents
                parent_child_mapping = df.groupby(parent_col)[child_col].apply(set).to_dict()
                child_parent_mapping = df.groupby(child_col)[parent_col].apply(set).to_dict()

                for child, parents in child_parent_mapping.items():
                    if len(parents) > 1:
                        hierarchy_issues.append(f"Child '{child}' appears under multiple parents: {list(parents)}")

        if hierarchy_issues:
            print("Hierarchy validation warnings:")
            for issue in hierarchy_issues[:5]:  # Show first 5 issues
                print(f"  - {issue}")

        # Apply threshold filtering
        if threshold_filter > 0:
            initial_count = len(df)
            df = df[df[value_col] >= threshold_filter]
            filtered_count = initial_count - len(df)
            if filtered_count > 0:
                print(f"Threshold filtering: Removed {filtered_count} entries below {threshold_filter}")

        # Prepare data for plotly treemap
        # Create path column for treemap hierarchy
        if len(hierarchy_cols) == 1:
            # Single level hierarchy
            df_plot = df.copy()
            path_col = hierarchy_cols[0]
        else:
            # Multi-level hierarchy - create path strings
            df_plot = df.copy()
            df_plot['path'] = df_plot[hierarchy_cols].apply(
                lambda row: ' / '.join(row.astype(str)), axis=1
            )
            path_col = 'path'

        # Enhanced color configuration with variance analysis
        if variance_coloring and target_values:
            # Calculate variance from targets
            color_values = []
            for _, row in df.iterrows():
                if len(hierarchy_cols) == 1:
                    key = row[hierarchy_cols[0]]
                else:
                    key = row[hierarchy_cols[-1]]  # Use leaf level for targets

                if key in target_values:
                    target = target_values[key]
                    actual = row[value_col]
                    variance_pct = ((actual - target) / target * 100) if target != 0 else 0
                    color_values.append(variance_pct)
                else:
                    color_values.append(0)

            color = color_values
            color_title = "Variance from Target (%)"
            color_scheme = "RdBu_r"  # Red for below target, blue for above

        elif color_column and color_column in df.columns:
            color = df[color_column]
            color_title = color_column.replace('_', ' ').title()
        else:
            # Use value column for coloring if no separate color column specified
            color = df[value_col]
            color_title = f"{value_col.replace('_', ' ').title()}"

        # Pattern detection for unusual concentrations
        pattern_alerts = []
        if pattern_detection:
            try:
                import numpy as np

                # Calculate concentration metrics
                total_value = df[value_col].sum()
                value_share = df[value_col] / total_value

                # Detect high concentration (80/20 rule violations)
                sorted_shares = value_share.sort_values(ascending=False)
                cumulative_shares = sorted_shares.cumsum()

                # Find how many entries make up 80% of value
                top_80_count = (cumulative_shares <= 0.8).sum() + 1
                concentration_ratio = top_80_count / len(df)

                if concentration_ratio < 0.2:  # Less than 20% of entries make up 80% of value
                    pattern_alerts.append(f"High concentration: Top {top_80_count} entries ({concentration_ratio:.1%}) account for 80% of total value")

                # Detect unusual gaps in values
                sorted_values = df[value_col].sort_values(ascending=False)
                if len(sorted_values) > 1:
                    value_ratios = sorted_values.iloc[:-1].values / sorted_values.iloc[1:].values
                    large_gaps = value_ratios > 5  # 5x difference

                    if large_gaps.any():
                        gap_count = large_gaps.sum()
                        pattern_alerts.append(f"Large value gaps detected: {gap_count} instances with 5x+ differences")

            except:
                pass

        # Create treemap
        if len(hierarchy_cols) == 1:
            # Simple single-level treemap
            fig = px.treemap(
                df_plot,
                path=[hierarchy_cols[0]],
                values=value_col,
                color=color,
                color_continuous_scale=color_scheme,
                title=title_override,
                width=width,
                height=height
            )
        else:
            # Multi-level hierarchy treemap
            fig = px.treemap(
                df_plot,
                path=hierarchy_cols,
                values=value_col,
                color=color,
                color_continuous_scale=color_scheme,
                title=title_override,
                width=width,
                height=height
            )

        # Customize layout
        fig.update_layout(
            title=dict(
                text=title_override,
                font=dict(size=16, family="Arial, sans-serif"),
                x=0.5
            ),
            font=dict(size=12),
            margin=dict(t=60, l=25, r=25, b=25)
        )

        # Update color bar
        fig.update_coloraxes(
            colorbar=dict(
                title=dict(
                    text=color_title,
                    font=dict(size=12)
                ),
                thickness=15,
                len=0.7
            )
        )

        # Customize treemap appearance
        fig.update_traces(
            textinfo="label+value" if show_values else "label",
            textfont=dict(size=10),
            hovertemplate="<b>%{label}</b><br>" +
                         f"{value_col.replace('_', ' ').title()}: %{{value}}<br>" +
                         f"{color_title}: %{{color}}<br>" +
                         "<extra></extra>"
        )

        # Generate HTML output file
        html_filename = get_timestamped_filename(self.metadata.key).replace('.png', '.html')
        final_output_path = output_path.parent / html_filename

        # Save as interactive HTML
        plot(fig, filename=str(final_output_path), auto_open=False)

        # Also save as static PNG for compatibility
        try:
            png_filename = get_timestamped_filename(self.metadata.key)
            png_output_path = output_path.parent / png_filename
            fig.write_image(str(png_output_path), width=width, height=height, scale=2)
            print(f"Static PNG saved to: {png_output_path}")
        except Exception as e:
            print(f"Could not save PNG (kaleido not installed?): {e}")

        # Export hierarchy analysis if requested
        if export_hierarchy:
            hierarchy_path = final_output_path.with_suffix('.csv')

            # Create hierarchy analysis
            hierarchy_analysis = df.copy()

            # Add calculated metrics
            hierarchy_analysis['value_share_pct'] = (hierarchy_analysis[value_col] / hierarchy_analysis[value_col].sum()) * 100

            # Add level information
            hierarchy_analysis['hierarchy_level'] = len(hierarchy_cols)
            for i, col in enumerate(hierarchy_cols):
                hierarchy_analysis[f'level_{i+1}'] = hierarchy_analysis[col]

            # Add variance information if available
            if variance_coloring and target_values:
                hierarchy_analysis['variance_from_target_pct'] = color

            # Add pattern flags
            if pattern_alerts:
                hierarchy_analysis['pattern_alerts'] = '; '.join(pattern_alerts)

            # Sort by value descending
            hierarchy_analysis = hierarchy_analysis.sort_values(value_col, ascending=False)

            # Save analysis
            hierarchy_analysis.to_csv(hierarchy_path, index=False)
            print(f"Hierarchy analysis exported to: {hierarchy_path}")

        # Display pattern alerts
        if pattern_alerts:
            print("Pattern analysis:")
            for alert in pattern_alerts:
                print(f"  - {alert}")

        return final_output_path