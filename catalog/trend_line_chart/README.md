# Trend Line Chart Build

User-friendly wrapper around the `trend_line_chart` program for exploring temporal behavior.

## Quick Run
- Ensure dependencies are installed: `pip install -r requirements.txt`.
- Set `PYTHONPATH=src` (or install the package).
- Execute: `python -m data_visualizer.cli datasets/trend_line_chart/sample_timeseries.csv trend_line_chart --output-dir outputs/trend_line_chart`.
- Output: PNG chart saved at `outputs/trend_line_chart/trend_line_chart.png`.

## Dataset
- File: `datasets/trend_line_chart/sample_timeseries.csv`
- Schema: `date`, `value`
- Purpose: Demonstrates a single metric over consecutive months so sudden shifts stand out.

## Interpretation Tips
- Watch for inflection points where slope changes direction.
- Overlay annotations for product launches or events to explain spikes when possible.

## TODOs (10)
1. Support multiple value columns to compare peer metrics on the same timeline.
2. Add rolling-average and seasonal decomposition overlays for noisy series.
3. Highlight detected anomalies or regime changes directly on the chart.
4. Accept irregular time intervals and resample to user-defined frequencies.
5. Provide automatic axis formatting for hourly/daily/weekly granularities.
6. Enable interactive output (Plotly/Altair) for hover inspection of points.
7. Offer export of aggregated statistics (trend slope, CAGR, breakpoints).
8. Integrate confidence bands for forecasts when a model is supplied.
9. Allow faceting by category to split unique trend profiles side-by-side.
10. Document best practices for handling missing periods and time zone normalization.

## Potential Pitfalls
- Sparse data may exaggerate line jumps; consider interpolating or switching to markers only.
- Multiple metrics with vastly different scales can obscure trends—normalize or split panels.
