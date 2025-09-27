# Violin Plot Distribution Visualization

## Quick Run
```bash
python -m data_visualizer.cli datasets/distribution_violin/sample_category_scores.csv distribution_violin --output-dir outputs/distribution_violin
```

## What This Visualization Does
The violin plot reveals the full distribution shape, skew, and outliers for each segment or category. Unlike box plots that only show summary statistics, violin plots display the entire probability density, making it easy to identify unique behaviors like multimodal distributions, long tails, or unusual clustering patterns within each group.

## Dataset Requirements
**Expected columns**: `[category, value]` or `[category, value, group]`
- **category**: Discrete grouping variable for which to show distributions (e.g., customer segments, product types, regions)
- **value**: Continuous numeric variable to analyze (e.g., scores, amounts, measurements)
- **group** (optional): Additional grouping for side-by-side comparison within categories

**Sample data format**:
```csv
customer_segment,satisfaction_score
Premium,8.5
Premium,9.2
Basic,6.1
Basic,5.8
Enterprise,9.8
Enterprise,8.9
```

## When to Use This Chart
- **Distribution comparison**: When you need to compare the shape of distributions across categories
- **Outlier detection**: When identifying unusual values or patterns within groups
- **Multimodal analysis**: When checking if groups have multiple peaks or clusters
- **Variance assessment**: When understanding the spread and consistency within categories
- **Quality control**: When monitoring process variation across different conditions

## Interpretation Notes
- **Width of violin** = Density of data points at that value (wider = more common)
- **Shape symmetry** = Skewness of the distribution (symmetric vs. left/right skewed)
- **Multiple peaks** = Multimodal distributions (subgroups within categories)
- **Tail length** = Presence of outliers or extreme values
- **Center line** = Median or mean of the distribution

## Common Pitfalls to Avoid
1. **Too few data points**: Violins need sufficient data to show meaningful shapes
2. **Scale differences**: Ensure all categories use the same value scale for comparison
3. **Bandwidth choice**: Automatic smoothing may over or under-smooth the distribution
4. **Overlapping categories**: Too many categories make individual shapes hard to distinguish
5. **Missing context**: Without sample sizes, wide violins might just reflect more data

## Ten Enhancement TODOs

### Data Processing Improvements
1. **Automated outlier detection**: Flag and optionally exclude extreme values using IQR or z-score methods
2. **Distribution normality tests**: Perform and report Shapiro-Wilk, Anderson-Darling tests per category
3. **Missing data strategies**: Handle missing values with imputation or explicit missing category
4. **Data transformation options**: Support log, square root, or Box-Cox transformations for skewed data

### Statistical Enhancements
5. **Statistical annotations**: Add p-values from ANOVA or Kruskal-Wallis tests comparing categories
6. **Confidence intervals**: Show bootstrap confidence intervals around median or mean lines
7. **Sample size display**: Annotate each violin with sample size for context
8. **Effect size calculations**: Compute and display Cohen's d or other effect size measures

### Visual Improvements
9. **Interactive exploration**: Enable hover tooltips showing exact statistics and sample details
10. **Density customization**: Allow manual bandwidth adjustment and kernel selection for distribution smoothing

## Configuration Options
```json
{
  "columns": ["custom_category", "custom_value"],
  "split": false,
  "inner": "box",
  "bandwidth": "auto",
  "cut": 2,
  "gridsize": 100,
  "show_outliers": true,
  "transform": "none",
  "statistical_test": "anova"
}
```

## Related Visualizations
- **Box Plot**: When you need simpler distribution summaries
- **Histogram**: When focusing on a single distribution's shape
- **Ridge Plot**: When comparing many distributions stacked vertically
- **Density Plot**: When overlaying multiple distributions on the same axes
- **Swarm Plot**: When you want to see individual data points
