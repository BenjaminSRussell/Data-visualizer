# Grouped Bar Chart Visualization

## Quick Run
```bash
python -m data_visualizer.cli datasets/comparison_grouped_bar/sample_groups.csv comparison_grouped_bar --output-dir outputs/comparison_grouped_bar
```

## What This Visualization Does
The grouped bar chart compares sub-categories within discrete groups, making it easy to spot relative performance differences between peer categories. Each group becomes a cluster of bars, where each bar represents a sub-category's value, enabling quick visual comparison both within groups and across groups.

## Dataset Requirements
**Expected columns**: `[group, category, value]`
- **group**: Discrete grouping variable (e.g., regions, departments, time periods)
- **category**: Sub-categories within each group (e.g., product types, metrics, channels)
- **value**: Numeric measure to compare (e.g., sales, counts, percentages)

**Sample data format**:
```csv
region,product_type,sales
North,Laptops,150000
North,Tablets,75000
South,Laptops,120000
South,Tablets,90000
```

## When to Use This Chart
- **Cross-group comparisons**: When you need to compare the same categories across different groups
- **Sub-category analysis**: When each group contains multiple related sub-categories
- **Performance benchmarking**: When identifying which categories perform best/worst in each group
- **Market share analysis**: When showing product mix or channel distribution by region/segment

## Interpretation Notes
- **Bar height** = Category value within that group
- **Color grouping** = Same category across all groups uses the same color
- **Cluster spacing** = Groups are visually separated for clarity
- **Cross-group trends** = Look for categories that consistently perform well/poorly across groups

## Common Pitfalls to Avoid
1. **Too many categories**: More than 5-6 categories per group becomes cluttered
2. **Uneven group sizes**: Groups with different numbers of categories can mislead
3. **Scale misinterpretation**: Ensure value scales are meaningful for comparison
4. **Missing data**: Gaps in category-group combinations create visual confusion
5. **Poor color choices**: Similar colors for different categories reduce clarity

## Ten Enhancement TODOs

### Data Processing Improvements
1. **Custom aggregation functions**: Support mean, median, percentiles via config instead of just sum
2. **Data normalization options**: Add percentage-of-group-total and z-score normalization modes
3. **Missing data handling**: Implement strategies for incomplete category-group combinations
4. **Outlier detection**: Flag and optionally exclude extreme values that skew comparisons

### Visual Enhancements
5. **Advanced sorting**: Sort groups by total value, max category, or custom criteria
6. **Error bars and confidence intervals**: Show variability when data represents samples
7. **Color palette management**: Support custom palettes, accessibility modes, and brand colors
8. **Label optimization**: Auto-truncate long labels, rotate for space, add tooltips

### Interaction and Export
9. **Interactive drill-down**: Click groups to filter detailed views, hover for exact values
10. **Summary table export**: Generate comparison matrices showing top/bottom performers per group

## Configuration Options
```json
{
  "columns": ["custom_group", "custom_category", "custom_value"],
  "aggregation": "mean",
  "sort_by": "total_value",
  "normalize": "group_percentage",
  "color_palette": "Set2",
  "max_categories": 6
}
```

## Related Visualizations
- **Stacked Bar Chart**: When showing part-to-whole within groups
- **Heatmap**: When you have many groups and categories
- **Violin Plot**: When distribution shape matters more than totals
- **Line Chart**: When groups represent time periods
