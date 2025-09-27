"""Cross-tabulation heatmap that reveals intersection patterns between two categorical dimensions.

Advanced intersection analyzer that exposes hidden relationships between categorical
segments through color-coded cross-tabulation. Perfect for market segmentation,
demographic analysis, and performance evaluation across multiple dimensions.

Future vision: Hierarchical clustering of rows/columns, interactive drill-down,
automated anomaly detection, and AI-powered pattern interpretation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ..base import Visualization, VisualizationMetadata
from ...globals import CHART_DEFAULTS, get_palette_for_categories, get_timestamped_filename


class ComparisonHeatmap(Visualization):
    metadata = VisualizationMetadata(
        key="comparison_heatmap",
        title="Comparison Heatmap",
        insight_type="Comparison",
        description="Visualize intersection of two categorical dimensions with custom aggregation functions.",
        example_url="https://seaborn.pydata.org/examples/heatmap_annotation.html",
        tags=("comparison", "categorical", "heatmap", "seaborn"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Data preparation for cross-tabulation analysis."""
        if df.empty:
            raise ValueError("Input dataframe is empty; provide categorical intersection data.")

        # Get column configuration
        required_cols: Iterable[str] = self.config.get("columns") or df.columns[:3]
        required_cols = tuple(required_cols)

        if len(required_cols) < 3:
            raise ValueError("Heatmap requires three columns (row_category, column_category, value).")

        if len(df.columns) < 3:
            raise ValueError("Dataset must have at least 3 columns for row, column, and value.")

        # Select and validate columns
        processed_df = df[list(required_cols)].copy()
        row_col, col_col, value_col = processed_df.columns[:3]

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

        return processed_df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Create cross-tabulation heatmap with intelligent styling."""
        try:
            import seaborn as sns
            from matplotlib import pyplot as plt
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install seaborn and matplotlib to use the heatmap visualization.") from exc

        row_col, col_col, value_col = df.columns[:3]

        # Configuration
        defaults = CHART_DEFAULTS.get("heatmap", {"background": "white"})
        figsize = self.config.get("figsize", (10, 8))
        aggregation = self.config.get("aggregation", "sum")
        color_palette = self.config.get("color_palette", "viridis")
        show_values = self.config.get("show_values", True)
        title_override = self.config.get("title", self.metadata.title)
        cluster_rows = self.config.get("cluster_rows", False)
        cluster_cols = self.config.get("cluster_cols", False)
        diverging_colormap = self.config.get("diverging_colormap", False)
        statistical_testing = self.config.get("statistical_testing", False)
        export_rankings = self.config.get("export_rankings", False)
        anomaly_detection = self.config.get("anomaly_detection", False)
        hide_low_samples = self.config.get("hide_low_samples", False)
        min_sample_threshold = self.config.get("min_sample_threshold", 5)

        # Aggregation function mapping
        agg_funcs = {
            "sum": "sum",
            "mean": "mean",
            "median": "median",
            "count": "count",
            "std": "std",
            "min": "min",
            "max": "max"
        }

        agg_func = agg_funcs.get(aggregation, "sum")

        # Create pivot table with sample counting for filtering
        if aggregation == "count":
            pivot_table = df.pivot_table(
                values=value_col,
                index=row_col,
                columns=col_col,
                aggfunc="count",
                fill_value=0
            )
            sample_counts = pivot_table.copy()
        else:
            pivot_table = df.pivot_table(
                values=value_col,
                index=row_col,
                columns=col_col,
                aggfunc=agg_func,
                fill_value=0
            )
            # Create sample count table for filtering
            sample_counts = df.pivot_table(
                values=value_col,
                index=row_col,
                columns=col_col,
                aggfunc="count",
                fill_value=0
            )

        # Filter out low-sample intersections if requested
        if hide_low_samples:
            low_sample_mask = sample_counts < min_sample_threshold
            pivot_table = pivot_table.mask(low_sample_mask)

        # Statistical testing for significant deviations
        statistical_annotations = {}
        if statistical_testing:
            try:
                from scipy import stats
                import numpy as np

                # Test each cell against the grand mean (one-sample t-test approximation)
                grand_mean = pivot_table.mean().mean()
                grand_std = pivot_table.std().std()

                for row_idx in pivot_table.index:
                    for col_idx in pivot_table.columns:
                        cell_value = pivot_table.loc[row_idx, col_idx]
                        if not pd.isna(cell_value) and grand_std > 0:
                            # Calculate z-score
                            z_score = (cell_value - grand_mean) / grand_std
                            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed

                            if p_value < 0.05:  # Significant deviation
                                statistical_annotations[(row_idx, col_idx)] = f"*"
                            if p_value < 0.01:  # Highly significant
                                statistical_annotations[(row_idx, col_idx)] = f"**"
            except:
                pass  # Skip if statistical testing fails

        # Anomaly detection using IQR method
        anomaly_annotations = {}
        if anomaly_detection:
            flat_values = pivot_table.values.flatten()
            flat_values = flat_values[~np.isnan(flat_values)]

            if len(flat_values) > 0:
                Q1 = np.percentile(flat_values, 25)
                Q3 = np.percentile(flat_values, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                for row_idx in pivot_table.index:
                    for col_idx in pivot_table.columns:
                        cell_value = pivot_table.loc[row_idx, col_idx]
                        if not pd.isna(cell_value):
                            if cell_value < lower_bound or cell_value > upper_bound:
                                anomaly_annotations[(row_idx, col_idx)] = "!"

        # Sort by row and column totals for better readability
        row_totals = pivot_table.sum(axis=1).sort_values(ascending=False)
        col_totals = pivot_table.sum(axis=0).sort_values(ascending=False)

        pivot_table = pivot_table.reindex(row_totals.index)
        pivot_table = pivot_table.reindex(col_totals.index, axis=1)

        # Set up the plot
        plt.figure(figsize=figsize)

        # Choose colormap
        if diverging_colormap:
            # Center around zero or median
            center_value = 0 if (pivot_table < 0).any().any() else pivot_table.median().median()
            cmap = "RdBu_r"
        else:
            center_value = None
            cmap = color_palette

        # Apply hierarchical clustering if requested
        if cluster_rows or cluster_cols:
            try:
                from scipy.cluster.hierarchy import linkage, dendrogram, leaves_list
                from scipy.spatial.distance import pdist

                if cluster_rows:
                    # Cluster rows
                    row_distances = pdist(pivot_table.fillna(0), metric='euclidean')
                    row_linkage = linkage(row_distances, method='ward')
                    row_order = leaves_list(row_linkage)
                    pivot_table = pivot_table.iloc[row_order]

                if cluster_cols:
                    # Cluster columns
                    col_distances = pdist(pivot_table.fillna(0).T, metric='euclidean')
                    col_linkage = linkage(col_distances, method='ward')
                    col_order = leaves_list(col_linkage)
                    pivot_table = pivot_table.iloc[:, col_order]

            except:
                print("Warning: Clustering failed, using original order")

        # Create custom annotations combining values with significance markers
        annotations = None
        if show_values or statistical_annotations or anomaly_annotations:
            annotations = []
            for i, row_idx in enumerate(pivot_table.index):
                row_annotations = []
                for j, col_idx in enumerate(pivot_table.columns):
                    cell_value = pivot_table.loc[row_idx, col_idx]

                    # Start with the value
                    if pd.isna(cell_value):
                        text = ""
                    elif aggregation in ["sum", "count"]:
                        text = f"{cell_value:.0f}"
                    else:
                        text = f"{cell_value:.2f}"

                    # Add statistical significance markers
                    if (row_idx, col_idx) in statistical_annotations:
                        text += statistical_annotations[(row_idx, col_idx)]

                    # Add anomaly markers
                    if (row_idx, col_idx) in anomaly_annotations:
                        text += anomaly_annotations[(row_idx, col_idx)]

                    row_annotations.append(text)
                annotations.append(row_annotations)

        # Create heatmap
        ax = sns.heatmap(
            pivot_table,
            annot=annotations if annotations else show_values,
            fmt='' if annotations else ('.0f' if aggregation in ["sum", "count"] else '.2f'),
            cmap=cmap,
            center=center_value,
            square=False,
            linewidths=0.5,
            cbar_kws={
                'label': f'{value_col.replace("_", " ").title()} ({aggregation.title()})'
            },
            robust=True
        )

        # Styling
        ax.set_facecolor(defaults["background"])
        plt.title(title_override, fontsize=14, fontweight='bold', pad=20)
        plt.xlabel(col_col.replace('_', ' ').title(), fontsize=12)
        plt.ylabel(row_col.replace('_', ' ').title(), fontsize=12)

        # Rotate labels if needed
        if len(pivot_table.columns) > 8:
            plt.xticks(rotation=45, ha='right')
        if len(pivot_table.index) > 10:
            plt.yticks(rotation=0)

        # Add summary statistics
        total_sum = pivot_table.sum().sum()
        max_intersection = pivot_table.max().max()
        max_row, max_col = np.unravel_index(pivot_table.values.argmax(), pivot_table.shape)
        max_row_name = pivot_table.index[max_row]
        max_col_name = pivot_table.columns[max_col]

        stats_text = f"Total: {total_sum:.0f}\nHighest: {max_intersection:.1f}\n({max_row_name} × {max_col_name})"
        plt.figtext(0.02, 0.98, stats_text, fontsize=9, va='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))

        plt.tight_layout()

        # Generate timestamped filename
        timestamped_filename = get_timestamped_filename(self.metadata.key)
        final_output_path = output_path.parent / timestamped_filename

        # Save with high DPI
        plt.savefig(final_output_path, dpi=300, bbox_inches='tight',
                   facecolor=defaults["background"], edgecolor='none')
        plt.close()

        # Export ranking tables if requested
        if export_rankings:
            rankings_path = final_output_path.with_suffix('.csv')

            # Create ranking data
            ranking_data = []
            for row_idx in pivot_table.index:
                for col_idx in pivot_table.columns:
                    cell_value = pivot_table.loc[row_idx, col_idx]
                    if not pd.isna(cell_value):
                        ranking_data.append({
                            row_col: row_idx,
                            col_col: col_idx,
                            value_col: cell_value,
                            'sample_count': sample_counts.loc[row_idx, col_idx] if not hide_low_samples else None,
                            'is_significant': (row_idx, col_idx) in statistical_annotations,
                            'is_anomaly': (row_idx, col_idx) in anomaly_annotations,
                            'percentile_rank': None  # Will be calculated
                        })

            # Convert to DataFrame and calculate percentile ranks
            rankings_df = pd.DataFrame(ranking_data)
            if not rankings_df.empty:
                rankings_df['percentile_rank'] = rankings_df[value_col].rank(pct=True) * 100
                rankings_df = rankings_df.sort_values(value_col, ascending=False)

                # Save rankings
                rankings_df.to_csv(rankings_path, index=False)
                print(f"Rankings exported to: {rankings_path}")

        return final_output_path