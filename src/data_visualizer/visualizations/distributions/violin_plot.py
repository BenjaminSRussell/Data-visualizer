"""Violin plot visualization to surface distribution uniqueness by category.

TODOs:
1. Allow bandwidth and kernel adjustments to suit small or large samples.
2. Provide log-scale option for highly skewed distributions.
3. Overlay quartile/median lines and summary statistics in the legend.
4. Add jittered raw points (swarmplot) for low sample counts.
5. Support secondary facet dimension for contextual comparisons (e.g., region).
6. Include automatic detection of heavy tails or bimodality with textual notes.
7. Offer histogram/boxplot hybrids when stakeholders prefer familiar shapes.
8. Implement density difference highlights to show how one segment deviates from another.
9. Export segment-specific descriptive statistics tables alongside the chart.
10. Warn when category sample size falls below a recommended minimum.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..base import Visualization, VisualizationMetadata


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
        required_cols = self.config.get("columns") or df.columns[:2]
        if len(required_cols) < 2:
            raise ValueError("Violin plot requires at least two columns (category, value).")
        return df[list(required_cols)]

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        try:
            import seaborn as sns
            from matplotlib import pyplot as plt
        except ImportError as exc:
            raise RuntimeError("Install seaborn and matplotlib to use the violin plot visualization.") from exc

        category_col, value_col = df.columns[:2]
        plt.figure(figsize=(8, 4))
        sns.violinplot(data=df, x=category_col, y=value_col, inner="box", palette="muted")
        plt.title(self.metadata.title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path
