# Line Chart Trend Visualization

## Quick Run
```bash
python -m data_visualizer.cli datasets/trend_line_chart/sample_timeseries.csv trend_line_chart --output-dir outputs/trend_line_chart
```

## What This Visualization Does
The trend line chart tracks how a metric evolves over a sequential dimension (usually time), making it easy to identify directional changes, seasonal patterns, anomalies, and trend breaks. This visualization reveals when the dataset behaves unlike its baseline and helps pinpoint periods of significant change.

## Dataset Requirements
**Expected columns**: `[time/sequence, value]` or `[time/sequence, value, category]`
- **Sequential column**: Time periods, dates, or ordered categories (e.g., months, quarters, steps)
- **Value column**: Continuous numeric variable to track (e.g., sales, performance, counts)
- **Category column** (optional): Multiple series for comparison (e.g., product lines, regions)

**Sample data format**:
```csv
date,sales_amount
2023-01-01,15000
2023-02-01,18500
2023-03-01,22000
2023-04-01,19500
```

## When to Use This Chart
- **Time series analysis**: Track performance metrics over time periods
- **Trend identification**: Identify growth, decline, or cyclical patterns
- **Anomaly detection**: Spot unusual spikes or drops in data
- **Seasonal analysis**: Understand recurring patterns and seasonality
- **Forecasting preparation**: Visualize historical data before prediction modeling

## Interpretation Notes
- **Line slope** = Rate of change (steeper = faster change)
- **Line direction** = Trend direction (up = growth, down = decline)
- **Line smoothness** = Consistency (smooth = stable, jagged = volatile)
- **Peaks and valleys** = Local maxima and minima in the data
- **Trend breaks** = Points where the pattern changes significantly

## Ten Enhancement TODOs

### Data Processing Improvements
1. **Multiple value columns**: Support comparing peer metrics on the same timeline
2. **Time handling**: Accept irregular time intervals and resample to user-defined frequencies
3. **Missing data strategies**: Implement interpolation, forward-fill, or gap indicators
4. **Data transformation**: Support log scale, moving averages, and seasonal decomposition

### Analytical Features
5. **Anomaly detection**: Highlight detected anomalies or regime changes directly on the chart
6. **Trend analysis**: Calculate and display trend slope, CAGR, and breakpoints
7. **Seasonal decomposition**: Add seasonal and trend components as overlays
8. **Forecasting integration**: Include confidence bands for forecasts when model is supplied

### Visual Enhancements
9. **Interactive output**: Enable Plotly/Altair for hover inspection and zooming
10. **Advanced formatting**: Automatic axis formatting for hourly/daily/weekly granularities

## Configuration Options
```json
{
  "columns": ["custom_date", "custom_value"],
  "date_format": "%Y-%m-%d",
  "smoothing": "none",
  "show_markers": true,
  "detect_anomalies": false,
  "seasonal_decomposition": false,
  "moving_average_window": null,
  "y_axis_start_zero": true
}
```

## Related Visualizations
- **Multi-line Chart**: When comparing multiple related time series
- **Area Chart**: When showing cumulative values or emphasizing magnitude
- **Candlestick Chart**: When displaying OHLC financial data
- **Seasonal Plot**: When focusing specifically on seasonal patterns
- **Horizon Chart**: When displaying many time series in compact form
