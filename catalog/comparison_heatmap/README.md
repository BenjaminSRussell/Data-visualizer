# Comparison Heatmap

**Use case**: Visualize intersection patterns between two categorical dimensions to reveal hidden relationships and performance gaps across segments.

**Perfect for**: Market segmentation analysis, regional performance comparison, demographic cross-tabulation, and identifying high/low performing category intersections.

## Quick Run

```bash
python -m data_visualizer.cli datasets/comparison_heatmap/sample_intersections.csv comparison_heatmap --output-dir outputs/comparison_heatmap
```

## Dataset Structure

The sample dataset (`sample_intersections.csv`) demonstrates regional sales performance across product categories:

- **region**: Geographic regions (North, South, East, West, Central)
- **product_category**: Product types (Electronics, Clothing, Home, Sports, Books)
- **sales_volume**: Numeric values for aggregation

## Interpretation Guidelines

**What to look for:**
- **Hot spots**: Dark colored cells indicate high-performing intersections
- **Cold spots**: Light colored cells reveal underperforming combinations
- **Patterns**: Row/column clustering exposes similar behavior across segments
- **Anomalies**: Unexpected high or low values that warrant investigation

**Common insights:**
- Regional preferences for specific product categories
- Market penetration gaps requiring strategic attention
- Cross-segment performance benchmarks for goal setting

## Configuration Options

Key parameters for customization:

- `aggregation`: "sum", "mean", "median", "count", "std", "min", "max"
- `color_palette`: "viridis", "plasma", "coolwarm", "RdYlBu_r"
- `show_values`: Display numeric values in cells (true/false)
- `diverging_colormap`: Use centered colormap for deviation analysis
- `cluster_rows`/`cluster_cols`: Hierarchical clustering for pattern discovery

## Ten Forward-Looking TODOs

1. **Interactive drill-down**: Click cells to generate filtered detail charts
2. **Statistical significance testing**: Highlight cells with significant deviations
3. **Hierarchical clustering**: Auto-group similar rows/columns for pattern discovery
4. **Anomaly detection**: Automatically flag unusual intersections with annotations
5. **Export functionality**: Generate ranking tables of top/bottom performers
6. **Multi-metric overlay**: Support secondary metrics via color saturation
7. **Comparative mode**: Side-by-side heatmaps for time period comparison
8. **Accessibility enhancements**: Colorblind-safe palettes with pattern overlays
9. **Smart aggregation**: Auto-recommend aggregation methods based on data distribution
10. **Contextual insights**: AI-generated explanations of notable patterns and outliers

## Potential Pitfalls

- **Scale sensitivity**: Values with different magnitudes may need normalization
- **Missing combinations**: Empty intersections appear as zero - distinguish from actual zeros
- **Color interpretation**: Ensure legend clearly communicates the value scale
- **Overcrowding**: Too many categories create unreadable charts - consider filtering
- **Correlation confusion**: Strong patterns don't necessarily imply causation