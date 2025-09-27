"""Simple line chart visualization using matplotlib."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..base import Visualization, VisualizationMetadata


class LineChart(Visualization):
    metadata = VisualizationMetadata(
        key="trend_line_chart",
        title="Line Chart",
        insight_type="Trend",
        description="Track how a metric evolves over a sequential dimension.",
        example_url="https://observablehq.com/@d3/line-chart",
        tags=("trends", "time-series", "matplotlib"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Input dataframe is empty; provide time series data.")
        if df.shape[1] < 2:
            raise ValueError("Expected dataframe with at least two columns (x, y).")
        return df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise RuntimeError("Install matplotlib to use the line chart visualization.") from exc

        x_col, y_col = df.columns[:2]
        plt.figure(figsize=(8, 4))
        plt.plot(df[x_col], df[y_col], marker="o", linewidth=2)
        plt.title(self.metadata.title)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path
