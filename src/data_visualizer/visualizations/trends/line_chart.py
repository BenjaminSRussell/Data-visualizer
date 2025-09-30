"""Advanced line chart visualization with multi-series support, anomaly detection, and trend analysis.

Features:
- Multi-series overlays with intelligent color palettes
- Rolling averages and smoothing controls
- Automated anomaly detection using rolling z-score
- Trend analysis with slope, R², and CAGR calculations
- Confidence bands for statistical analysis
- Comprehensive trend statistics export
- Professional-quality outputs with adaptive formatting
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
        anomaly_detection = self.config.get("anomaly_detection", False)
        export_trends = self.config.get("export_trends", False)
        seasonal_decomposition = self.config.get("seasonal_decomposition", False)
        confidence_bands = self.config.get("confidence_bands", False)

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
        if self.config.get("colors"):
            colors = self.config.get("colors")
        else:
            palette = self.config.get("palette", "corporate_safe")
            colors = get_palette_for_categories(len(y_cols), palette)

        # Store trend analysis data
        trend_analysis = []

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

            # Anomaly detection using rolling z-score
            anomalies_x, anomalies_y = [], []
            if anomaly_detection:
                try:
                    import numpy as np
                    rolling_mean = y_data.rolling(window=max(5, len(y_data)//10), center=True).mean()
                    rolling_std = y_data.rolling(window=max(5, len(y_data)//10), center=True).std()
                    z_scores = np.abs((y_data - rolling_mean) / rolling_std)

                    anomaly_threshold = self.config.get("anomaly_threshold", 2.5)
                    anomaly_mask = z_scores > anomaly_threshold

                    if anomaly_mask.any():
                        anomalies_x = df[x_col][anomaly_mask].values
                        anomalies_y = y_data[anomaly_mask].values
                except:
                    pass  # Skip if anomaly detection fails

            # Calculate trend statistics
            if export_trends:
                try:
                    import numpy as np
                    from scipy import stats

                    # Convert x to numeric for trend calculation
                    if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                        x_numeric = pd.to_numeric(df[x_col])
                    else:
                        x_numeric = pd.to_numeric(df[x_col], errors='coerce')

                    # Remove NaN values for trend calculation
                    valid_mask = ~(x_numeric.isna() | y_data.isna())
                    if valid_mask.sum() > 1:
                        x_clean = x_numeric[valid_mask]
                        y_clean = y_data[valid_mask]

                        slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)

                        # Calculate CAGR if possible (for positive values)
                        cagr = None
                        if len(y_clean) > 1 and y_clean.iloc[0] > 0 and y_clean.iloc[-1] > 0:
                            periods = len(y_clean) - 1
                            cagr = (y_clean.iloc[-1] / y_clean.iloc[0]) ** (1/periods) - 1

                        trend_analysis.append({
                            'metric': y_col,
                            'slope': slope,
                            'r_squared': r_value**2,
                            'p_value': p_value,
                            'cagr': cagr,
                            'start_value': y_clean.iloc[0],
                            'end_value': y_clean.iloc[-1],
                            'mean_value': y_clean.mean(),
                            'std_value': y_clean.std(),
                            'anomalies_detected': len(anomalies_x)
                        })
                except:
                    pass  # Skip if trend analysis fails

            # Plot the line
            marker = "o" if show_markers else None
            plt.plot(df[x_col], y_data,
                    marker=marker, linewidth=line_width,
                    color=color, label=label, alpha=0.8)

            # Plot anomalies if detected
            if anomalies_x and anomalies_y:
                plt.scatter(anomalies_x, anomalies_y, color='red', s=50,
                           alpha=0.8, zorder=5, label=f"{y_col} Anomalies")

            # Add confidence bands if requested and data supports it
            if confidence_bands and rolling_window and rolling_window > 1:
                try:
                    rolling_std = df[y_col].rolling(window=rolling_window, center=True).std()
                    upper_band = y_data + 1.96 * rolling_std
                    lower_band = y_data - 1.96 * rolling_std
                    plt.fill_between(df[x_col], upper_band, lower_band,
                                   color=color, alpha=0.2, label=f"{y_col} 95% CI")
                except:
                    pass

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

        # Export trend analysis if requested
        if export_trends and trend_analysis:
            trends_path = final_output_path.with_suffix('.csv')
            trends_df = pd.DataFrame(trend_analysis)
            trends_df.to_csv(trends_path, index=False)
            print(f"Trend analysis exported to: {trends_path}")

        return final_output_path
