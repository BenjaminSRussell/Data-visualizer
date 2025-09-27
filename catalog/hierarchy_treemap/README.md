# Hierarchy Treemap

**Use case**: Visualize nested categories with area proportional to values to reveal hierarchical relationships and share-of-parent contributions.

**Perfect for**: Organizational charts, budget allocation, market share analysis, geographic data, file system visualization, and any nested categorical data structure.

## Quick Run

```bash
python -m data_visualizer.cli datasets/hierarchy_treemap/sample_hierarchy.csv hierarchy_treemap --output-dir outputs/hierarchy_treemap
```

## Dataset Structure

The sample dataset (`sample_hierarchy.csv`) demonstrates global city data in a hierarchical structure:

- **region**: Top-level geographic grouping (North America, Europe, Asia)
- **country**: Second-level grouping within regions
- **city**: Individual cities within countries
- **population**: Primary metric for area sizing (numeric)
- **gdp_per_capita**: Secondary metric for color coding (numeric)

## Interpretation Guidelines

**What to look for:**
- **Area size**: Larger rectangles represent higher values in the primary metric
- **Color intensity**: Darker/lighter colors indicate secondary metric values
- **Hierarchy levels**: Nested rectangles show parent-child relationships
- **Proportional relationships**: Visual comparison of relative sizes within groups

**Common insights:**
- Resource allocation across organizational units
- Market share distribution within segments
- Geographic concentration patterns
- Budget utilization across departments

## Configuration Options

Key parameters for customization:

- `color_column`: Secondary metric for color coding (uses value column if not specified)
- `color_scheme`: "viridis", "plasma", "blues", "reds", "greens"
- `width`/`height`: Output dimensions (default: 1000x600)
- `show_values`: Display numeric values in rectangles (true/false)
- `title`: Override default title

## Ten Forward-Looking TODOs

1. **Interactive drill-down**: Click to zoom into hierarchy levels with breadcrumb navigation
2. **Variance indicators**: Color-code by performance vs. target or deviation from mean
3. **Comparative mode**: Side-by-side treemaps for different time periods
4. **Export capabilities**: Generate hierarchy tables and summary statistics
5. **Threshold filtering**: Hide small segments below configurable size limits
6. **Pattern detection**: Automatically identify unusual concentrations or gaps
7. **Multi-metric support**: Overlay additional metrics via patterns or borders
8. **Accessibility features**: High contrast modes and screen reader compatibility
9. **Animation support**: Transitions between different hierarchy cuts or time periods
10. **Smart layout**: Optimize rectangle arrangement for better readability

## Potential Pitfalls

- **Hierarchy validation**: Ensure data forms proper tree structure with no orphan nodes
- **Scale differences**: Large value ranges may make small segments invisible
- **Color confusion**: Choose colorblind-safe palettes for secondary metrics
- **Label overcrowding**: Too many small segments create unreadable text
- **Missing data**: Handle incomplete hierarchies gracefully
- **Performance**: Large datasets may require aggregation for responsive interaction