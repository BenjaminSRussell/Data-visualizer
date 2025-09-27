"""Violin plot visualization to surface distribution uniqueness by category."""

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
