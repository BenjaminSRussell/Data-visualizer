"""Distribution detective - reveals hidden patterns in categorical data through violin shapes.

Advanced distribution analyzer that exposes multimodal patterns, outliers, and variance
differences invisible to summary statistics. Perfect for quality control, A/B testing,
and customer behavior analysis.

Future vision: Automated anomaly detection, real-time distribution monitoring, and
AI-powered pattern interpretation with business context."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..base import Visualization, VisualizationMetadata
from ...globals import CHART_DEFAULTS, get_palette_for_categories, get_timestamped_filename


class ViolinPlot(Visualization):
    metadata = VisualizationMetadata(
        key="distribution_violin",
        title="Category Violin Plot",
        insight_type="Distribution",
        description="Reveal distribution shape and outliers across categories to spot unique segment behavior.",
        example_url="https://seaborn.pydata.org/examples/violinplots.html",
        tags=("distribution", "category", "seaborn"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Statistical preprocessing - ensures robust distribution analysis across categories.

        Future: Auto-detect optimal transformations, handle mixed data types, smart binning."""
        if df.empty:
            raise ValueError("Input dataframe is empty; provide categorical distribution data.")

        # Get column configuration
        required_cols = self.config.get("columns") or df.columns[:2]
        if len(required_cols) < 2:
            raise ValueError("Violin plot requires at least two columns (category, value).")

        if len(df.columns) < 2:
            raise ValueError("Dataset must have at least 2 columns for category and value.")

        # Select and validate columns
        processed_df = df[list(required_cols)].copy()
        category_col, value_col = processed_df.columns[:2]

        # Data quality checks
        if processed_df[value_col].isnull().all():
            raise ValueError(f"Value column '{value_col}' contains no valid data.")

        # Handle missing values
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

        # Check sample sizes per category
        min_samples = self.config.get("min_samples_per_category", 10)
        category_counts = processed_df[category_col].value_counts()

        small_categories = category_counts[category_counts < min_samples]
        if len(small_categories) > 0:
            print(f"Warning: Categories with fewer than {min_samples} samples: {small_categories.to_dict()}")

        # Check for reasonable number of categories
        max_categories = self.config.get("max_categories", 8)
        n_categories = processed_df[category_col].nunique()

        if n_categories > max_categories:
            print(f"Warning: {n_categories} categories detected. Violin plot may be cluttered.")

        # Data transformation if requested
        transform = self.config.get("transform", "none")
        if transform == "log":
            if (processed_df[value_col] <= 0).any():
                print("Warning: Cannot log-transform data with non-positive values.")
            else:
                import numpy as np
                processed_df[value_col] = np.log(processed_df[value_col])
                print("Applied log transformation to value column.")

        return processed_df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Advanced statistical visualization - creates violin plots with deep analytical insights.

        Future: Interactive distribution exploration, real-time statistical testing, automated insights."""
        try:
            import seaborn as sns
            from matplotlib import pyplot as plt
            import numpy as np
            from scipy import stats
        except ImportError as exc:
            raise RuntimeError("Install seaborn, matplotlib, and scipy to use the violin plot visualization.") from exc

        category_col, value_col = df.columns[:2]

        # Intelligent configuration with global styling
        defaults = CHART_DEFAULTS["violin_plot"]
        figsize = self.config.get("figsize", (10, 6))

        # Smart color selection for statistical visualization
        n_categories = df[category_col].nunique()
        palette_style = self.config.get("palette_style", "vibrant_accessible")
        colors = get_palette_for_categories(n_categories, palette_style)

        inner = self.config.get("inner", "box")
        split = self.config.get("split", False)
        scale = self.config.get("scale", "area")  # area, count, width
        bandwidth = self.config.get("bandwidth", "auto")
        show_stats = self.config.get("show_statistics", True)
        show_sample_sizes = self.config.get("show_sample_sizes", True)
        title_override = self.config.get("title", self.metadata.title)
        log_scale = self.config.get("log_scale", False)
        outlier_detection = self.config.get("outlier_detection", False)

        # Data transformation for log scale
        if log_scale:
            # Check for positive values required for log transformation
            if (df[value_col] <= 0).any():
                min_positive = df[df[value_col] > 0][value_col].min()
                # Add small offset to non-positive values
                df[value_col] = df[value_col].where(df[value_col] > 0, min_positive / 10)
                print(f"Warning: Non-positive values found. Adjusted to minimum positive value / 10: {min_positive / 10:.6f}")

        # Outlier detection and flagging
        outliers_info = {}
        if outlier_detection:
            for cat in df[category_col].unique():
                cat_data = df[df[category_col] == cat][value_col]
                Q1 = cat_data.quantile(0.25)
                Q3 = cat_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = cat_data[(cat_data < lower_bound) | (cat_data > upper_bound)]
                outliers_info[cat] = {
                    'count': len(outliers),
                    'values': outliers.tolist()[:5]  # Show first 5 outliers
                }

        # Create the plot
        plt.figure(figsize=figsize)

        # Main violin plot with intelligent color application
        ax = sns.violinplot(
            data=df,
            x=category_col,
            y=value_col,
            inner=inner,
            palette=colors,
            split=split,
            scale=scale,
            bw_method=bandwidth if bandwidth != "auto" else None
        )

        # Apply statistical annotation colors
        ax.set_facecolor(defaults["background"])

        # Calculate and display statistics
        if show_stats:
            categories = df[category_col].unique()
            stats_text = []

            for cat in categories:
                cat_data = df[df[category_col] == cat][value_col]

                # Basic statistics
                mean_val = cat_data.mean()
                median_val = cat_data.median()
                std_val = cat_data.std()
                n_samples = len(cat_data)

                # Statistical tests
                if len(cat_data) >= 3:  # Minimum for normality test
                    _, p_normal = stats.shapiro(cat_data)
                    is_normal = p_normal > 0.05
                else:
                    is_normal = "N/A"

                stats_text.append(f"{cat}: μ={mean_val:.2f}, σ={std_val:.2f}, n={n_samples}")

            # Add statistics as text box
            stats_str = "\n".join(stats_text)
            plt.figtext(0.02, 0.02, stats_str, fontsize=8,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))

        # Add sample sizes to x-axis labels if requested
        if show_sample_sizes:
            categories = df[category_col].unique()
            sample_sizes = [len(df[df[category_col] == cat]) for cat in categories]

            # Update x-axis labels with sample sizes
            ax.set_xticklabels([f"{cat}\n(n={n})" for cat, n in zip(categories, sample_sizes)])

        # Perform ANOVA test if multiple categories
        categories = df[category_col].unique()
        if len(categories) > 1:
            try:
                category_groups = [df[df[category_col] == cat][value_col] for cat in categories]
                f_stat, p_anova = stats.f_oneway(*category_groups)

                if p_anova < 0.001:
                    p_text = "p < 0.001"
                else:
                    p_text = f"p = {p_anova:.3f}"

                plt.figtext(0.98, 0.98, f"ANOVA: F={f_stat:.2f}, {p_text}",
                           fontsize=10, ha='right', va='top',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            except:
                pass  # Skip if ANOVA fails

        # Customize the plot
        plt.title(title_override, fontsize=14, fontweight='bold', pad=20)
        plt.xlabel(category_col.replace('_', ' ').title(), fontsize=12)

        # Create appropriate y-label based on transformation
        if log_scale:
            ylabel = f"Log({value_col.replace('_', ' ').title()})"
            plt.yscale('log')
        elif self.config.get("transform") == "log":
            ylabel = f"Log({value_col.replace('_', ' ').title()})"
        else:
            ylabel = value_col.replace('_', ' ').title()
        plt.ylabel(ylabel, fontsize=12)

        # Display outlier information if detection was enabled
        if outlier_detection and any(info['count'] > 0 for info in outliers_info.values()):
            outlier_text = "Outliers detected:\n"
            for cat, info in outliers_info.items():
                if info['count'] > 0:
                    outlier_text += f"{cat}: {info['count']} outliers\n"

            plt.figtext(0.98, 0.02, outlier_text.strip(), fontsize=8, ha='right', va='bottom',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="orange", alpha=0.7))

        # Rotate x-axis labels if needed
        if len(categories) > 5 or any(len(str(cat)) > 8 for cat in categories):
            plt.xticks(rotation=45, ha='right')

        # Add grid for better readability
        plt.grid(axis='y', alpha=0.3, linestyle='--')

        # Tight layout with space for annotations
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15, top=0.9, left=0.1, right=0.95)

        # Save with high DPI for quality
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        return output_path
