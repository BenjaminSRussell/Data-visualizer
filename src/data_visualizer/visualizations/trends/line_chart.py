"""Simple line chart visualization using matplotlib.

TODOs (audit notes):
1. Multi-series overlays — current implementation only looks at the first two columns,
   so we cannot compare peer metrics. Accept a list of value columns and render each with
   legend support to unlock competitive analysis.
2. Smoothing controls — noisy datasets read poorly. Add optional rolling averages and
   seasonal decomposition so users can toggle de-noised trend views without leaving the tool.
3. Automated anomaly callouts — nothing flags spikes or regime shifts today; integrate
   a lightweight detector (e.g., rolling z-score) and annotate flagged points directly.
4. Irregular interval handling — the chart assumes evenly spaced data. Support resampling
   and explicit formatting of gaps to prevent misleading slopes when periods are missing.
5. Adaptive axis formatting — axis labels default to raw `matplotlib` formatting. Inject
   smart formatting for hourly/daily/weekly cadences to keep dense series legible.
6. Interactive exports — static PNGs limit exploration. Provide an optional Plotly/Altair
   backend so users can hover, zoom, and download data quickly.
7. Trend summary export — analysts must compute slope/CAGR elsewhere. Generate summary
   statistics with the chart and persist them alongside the PNG for reporting.
8. Forecast overlays — confidence intervals are unsupported. Accept forecast arrays or
   models and render bands to illustrate projected uncertainty.
9. Faceting by category — when multiple cohorts exist, a single panel gets cluttered.
   Enable faceted layouts or small multiples so unique trend profiles remain readable.
10. Data hygiene guidance — missing periods and timezone mismatches cause false spikes.
    Document preprocessing expectations and optionally warn when gaps are detected.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..base import Visualization, VisualizationMetadata
from ...globals import CHART_DEFAULTS, get_palette_for_categories, get_timestamped_filename


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
        """Prepare and validate data for line chart visualization.

        Supports both single-series (x, y) and multi-series (x, y1, y2, ...) formats.
        Configuration can specify value_columns to select specific metrics.
        """
        if df.empty:
            raise ValueError("Input dataframe is empty; provide time series data.")
        if df.shape[1] < 2:
            raise ValueError("Expected dataframe with at least two columns (x, y).")

        # Handle datetime conversion for x-axis if needed
        x_col = df.columns[0]
        if df[x_col].dtype == 'object':
            try:
                df[x_col] = pd.to_datetime(df[x_col])
            except (ValueError, pd.errors.ParserError):
                pass  # Keep as-is if not datetime-convertible

        return df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Render line chart with multi-series support and enhanced styling."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError as exc:
            raise RuntimeError("Install matplotlib to use the line chart visualization.") from exc

        # Configuration options
        defaults = CHART_DEFAULTS["line_chart"]
        figsize = self.config.get("figsize", (12, 6))
        value_columns = self.config.get("value_columns", None)
        show_markers = self.config.get("show_markers", True)
        line_width = self.config.get("line_width", 2)
        title_override = self.config.get("title", self.metadata.title)
        rolling_window = self.config.get("rolling_window", None)

        # Determine columns to plot
        x_col = df.columns[0]
        if value_columns:
            # Use specified value columns
            y_cols = [col for col in value_columns if col in df.columns]
            if not y_cols:
                raise ValueError(f"None of the specified value_columns {value_columns} found in data")
        else:
            # Use all numeric columns after the first
            y_cols = [col for col in df.columns[1:] if pd.api.types.is_numeric_dtype(df[col])]
            if not y_cols:
                raise ValueError("No numeric columns found for plotting")

        # Set up the plot
        plt.figure(figsize=figsize)
        ax = plt.gca()

        # Get colors for multiple series
        colors = get_palette_for_categories(len(y_cols), "corporate_safe")

        # Plot each series
        for i, y_col in enumerate(y_cols):
            color = colors[i] if i < len(colors) else defaults["primary_color"]

            # Optional rolling average
            if rolling_window and rolling_window > 1:
                y_data = df[y_col].rolling(window=rolling_window, center=True).mean()
                label = f"{y_col} (MA{rolling_window})"
            else:
                y_data = df[y_col]
                label = y_col

            # Plot the line
            marker = "o" if show_markers else None
            plt.plot(df[x_col], y_data,
                    marker=marker, linewidth=line_width,
                    color=color, label=label, alpha=0.8)

        # Formatting
        plt.title(title_override, fontsize=14, fontweight='bold')
        plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)

        # Y-axis label - use generic term for multi-series
        if len(y_cols) == 1:
            plt.ylabel(y_cols[0].replace('_', ' ').title(), fontsize=12)
        else:
            plt.ylabel("Value", fontsize=12)

        # Format x-axis for datetime data
        if pd.api.types.is_datetime64_any_dtype(df[x_col]):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(df) // 6)))
            plt.xticks(rotation=45)

        # Grid and legend
        plt.grid(True, linestyle="--", alpha=0.4, color='#E5E5E5')

        if len(y_cols) > 1:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()

        # Generate timestamped filename for unique outputs
        timestamped_filename = get_timestamped_filename(self.metadata.key)
        final_output_path = output_path.parent / timestamped_filename

        plt.savefig(final_output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        return final_output_path
