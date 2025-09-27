"""Grouped bar chart visualization using seaborn.

TODOs:
1. Accept custom aggregation functions (mean, median) via configuration.
2. Add confidence interval/error bars to convey variability within groups.
3. Enable sorting of groups by total value or max subcategory.
4. Provide optional data normalization to show share of group total.
5. Offer stacked/100% stacked variants for dense categorical sets.
6. Introduce drill-down capability that filters on a selected group.
7. Support color palette overrides and accessibility-safe defaults.
8. Auto-truncate long category labels and expose tooltips in interactive mode.
9. Export summary tables comparing highest and lowest performers per group.
10. Warn users when group/category cardinality exceeds readability thresholds.
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
        required_cols: Iterable[str] = self.config.get("columns") or df.columns[:3]
        required_cols = tuple(required_cols)
        if len(required_cols) < 3:
            raise ValueError("Grouped bar chart requires three columns (group, category, value).")
        return df[list(required_cols)]

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        try:
            import seaborn as sns
            from matplotlib import pyplot as plt
        except ImportError as exc:
            raise RuntimeError("Install seaborn and matplotlib to use the grouped bar visualization.") from exc

        group_col, category_col, value_col = df.columns[:3]
        plt.figure(figsize=(8, 4))
        sns.barplot(
            data=df,
            x=group_col,
            y=value_col,
            hue=category_col,
            estimator=sum,
            palette="colorblind",
        )
        plt.title(self.metadata.title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path
