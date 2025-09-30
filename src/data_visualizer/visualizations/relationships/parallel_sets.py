"""Parallel sets visualization for displaying categorical flows and funnel analysis.

Advanced flow analyzer that reveals how cohorts transition across categorical
stages through proportional ribbon visualization. Perfect for customer journey
analysis, conversion funnels, and lifecycle progression studies.

Future vision: Interactive path highlighting, conversion rate annotations,
drop-off analysis, and AI-powered journey optimization recommendations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ..base import Visualization, VisualizationMetadata
from ...globals import CHART_DEFAULTS, get_palette_for_categories, get_timestamped_filename


class SegmentationParallelSets(Visualization):
    metadata = VisualizationMetadata(
        key="segmentation_parallel_sets",
        title="Parallel Sets",
        insight_type="Flow",
        description="Display how cohorts flow across categorical stages to reveal funnel patterns and transitions.",
        example_url="https://plotly.com/python/parallel-categories-diagram/",
        tags=("flow", "categorical", "funnel", "plotly"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Data preparation for parallel sets flow analysis."""
        if df.empty:
            raise ValueError("Input dataframe is empty; provide categorical flow data.")

        # Get column configuration
        required_cols: Iterable[str] = self.config.get("columns") or df.columns
        required_cols = tuple(required_cols)

        if len(required_cols) < 2:
            raise ValueError("Parallel sets requires at least two categorical columns.")

        if len(df.columns) < 2:
            raise ValueError("Dataset must have at least 2 columns for flow analysis.")

        # Check if the last column is numeric (count/weight)
        if pd.api.types.is_numeric_dtype(df[df.columns[-1]]):
            # Last column is numeric - use as weights
            flow_cols = list(required_cols[:-1])
            weight_col = required_cols[-1]
        else:
            # All columns are categorical - will count occurrences
            flow_cols = list(required_cols)
            weight_col = None

        # Select relevant columns
        if weight_col:
            processed_df = df[flow_cols + [weight_col]].copy()
        else:
            processed_df = df[flow_cols].copy()

        # Drop rows with missing values in flow columns
        initial_rows = len(processed_df)
        processed_df = processed_df.dropna(subset=flow_cols)
        dropped_rows = initial_rows - len(processed_df)

        if dropped_rows > 0:
            print(f"Warning: Dropped {dropped_rows} rows with missing values in flow columns.")

        if processed_df.empty:
            raise ValueError("No valid data remaining after removing missing values.")

        # If no weight column, create one by counting combinations
        if weight_col is None:
            # Group by all flow columns and count occurrences
            processed_df = processed_df.groupby(flow_cols).size().reset_index(name='count')
            weight_col = 'count'

        # Validate that we have meaningful flows
        if len(flow_cols) < 2:
            raise ValueError("Need at least 2 stages for flow analysis.")

        # Store configuration for rendering
        self._flow_cols = flow_cols
        self._weight_col = weight_col

        return processed_df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Create parallel sets flow visualization."""
        try:
            import plotly.graph_objects as go
            from plotly.offline import plot
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install plotly to use the parallel sets visualization.") from exc

        flow_cols = self._flow_cols
        weight_col = self._weight_col

        # Configuration
        title_override = self.config.get("title", self.metadata.title)
        color_scheme = self.config.get("color_scheme", "plotly3")
        width = self.config.get("width", 1000)
        height = self.config.get("height", 600)
        show_counts = self.config.get("show_counts", True)
        conversion_analysis = self.config.get("conversion_analysis", False)
        drop_off_analysis = self.config.get("drop_off_analysis", False)
        export_funnel = self.config.get("export_funnel", False)
        highlight_path = self.config.get("highlight_path", None)  # Specific path to highlight

        # Prepare data for plotly parallel categories
        # Create dimensions for each stage
        dimensions = []

        for i, col in enumerate(flow_cols):
            # Get unique values and their positions
            unique_vals = df[col].unique()

            dimension = dict(
                label=col.replace('_', ' ').title(),
                values=df[col],
                categoryorder='category ascending'
            )
            dimensions.append(dimension)

        # Create the parallel categories diagram
        fig = go.Figure(data=[go.Parcats(
            dimensions=dimensions,
            counts=df[weight_col] if weight_col in df.columns else None,
            hoveron='color',
            hoverinfo='count+probability',
            line=dict(
                colorscale=color_scheme,
                showscale=True,
                colorbar=dict(
                    title="Flow Volume",
                    thickness=15,
                    len=0.7
                )
            ),
            arrangement='freeform'
        )])

        # Enhanced flow analysis
        total_flow = df[weight_col].sum()
        n_stages = len(flow_cols)

        # Detailed conversion analysis
        conversion_data = []
        drop_off_data = []

        if conversion_analysis or drop_off_analysis:
            for i in range(len(flow_cols) - 1):
                stage_from = flow_cols[i]
                stage_to = flow_cols[i + 1]

                # Calculate conversion rates by source
                stage_totals = df.groupby(stage_from)[weight_col].sum()
                stage_flows = df.groupby([stage_from, stage_to])[weight_col].sum().unstack(fill_value=0)

                for source in stage_totals.index:
                    total_from_source = stage_totals[source]

                    for destination in stage_flows.columns:
                        flow_volume = stage_flows.loc[source, destination] if source in stage_flows.index else 0
                        conversion_rate = (flow_volume / total_from_source * 100) if total_from_source > 0 else 0

                        conversion_data.append({
                            'stage_from': stage_from,
                            'stage_to': stage_to,
                            'source_value': source,
                            'destination_value': destination,
                            'flow_volume': flow_volume,
                            'source_total': total_from_source,
                            'conversion_rate': conversion_rate
                        })

                    # Calculate drop-off rate (1 - sum of all conversion rates from this source)
                    total_converted = stage_flows.loc[source].sum() if source in stage_flows.index else 0
                    drop_off_rate = ((total_from_source - total_converted) / total_from_source * 100) if total_from_source > 0 else 0

                    if drop_off_rate > 0:
                        drop_off_data.append({
                            'stage': stage_from,
                            'source_value': source,
                            'total_volume': total_from_source,
                            'converted_volume': total_converted,
                            'drop_off_volume': total_from_source - total_converted,
                            'drop_off_rate': drop_off_rate
                        })

        # Calculate summary conversion stats for display
        conversion_stats = []
        for i in range(len(flow_cols) - 1):
            stage_from = flow_cols[i]
            stage_to = flow_cols[i + 1]

            # Overall conversion rate between stages
            stage_from_total = df.groupby(stage_from)[weight_col].sum().sum()
            stage_to_total = df.groupby(stage_to)[weight_col].sum().sum()

            if stage_from_total > 0:
                avg_conversion = (stage_to_total / stage_from_total) * 100
                conversion_stats.append(f"{stage_from} → {stage_to}: {avg_conversion:.1f}%")

        # Identify critical drop-off points
        critical_dropoffs = []
        if drop_off_data:
            drop_off_df = pd.DataFrame(drop_off_data)
            # Find stages with >20% drop-off rate
            high_dropoff = drop_off_df[drop_off_df['drop_off_rate'] > 20]
            if not high_dropoff.empty:
                for _, row in high_dropoff.iterrows():
                    critical_dropoffs.append(f"{row['stage']} '{row['source_value']}': {row['drop_off_rate']:.1f}% drop-off")

        # Customize layout
        fig.update_layout(
            title=dict(
                text=title_override,
                font=dict(size=16, family="Arial, sans-serif"),
                x=0.5
            ),
            font=dict(size=12),
            margin=dict(t=80, l=50, r=50, b=50),
            width=width,
            height=height,
            plot_bgcolor='white'
        )

        # Enhanced statistics annotation
        stats_text = f"Total Flow Volume: {total_flow:,.0f}<br>"
        stats_text += f"Stages: {n_stages}<br>"
        if conversion_stats:
            stats_text += "Conversion Rates:<br>"
            stats_text += "<br>".join(conversion_stats)

        # Add critical drop-off alerts
        if critical_dropoffs:
            stats_text += "<br><br>⚠️ High Drop-off Points:<br>"
            stats_text += "<br>".join(critical_dropoffs[:3])  # Show top 3

        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=stats_text,
            showarrow=False,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
            align="left",
            valign="top"
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

        # Export funnel analysis if requested
        if export_funnel:
            funnel_path = final_output_path.with_suffix('.csv')

            if conversion_data:
                # Export detailed conversion analysis
                conversion_df = pd.DataFrame(conversion_data)
                conversion_df = conversion_df.sort_values(['stage_from', 'conversion_rate'], ascending=[True, False])
                conversion_df.to_csv(funnel_path, index=False)
                print(f"Funnel analysis exported to: {funnel_path}")

                # Also export drop-off analysis if available
                if drop_off_data:
                    dropoff_path = final_output_path.with_name(final_output_path.stem + '_dropoffs.csv')
                    dropoff_df = pd.DataFrame(drop_off_data)
                    dropoff_df = dropoff_df.sort_values('drop_off_rate', ascending=False)
                    dropoff_df.to_csv(dropoff_path, index=False)
                    print(f"Drop-off analysis exported to: {dropoff_path}")

        # Display critical insights
        if critical_dropoffs:
            print("Critical drop-off points identified:")
            for dropoff in critical_dropoffs:
                print(f"  - {dropoff}")

        return final_output_path