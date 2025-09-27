# Grouped Bar Comparison Build

Curated entry point for the `comparison_grouped_bar` program to evaluate segmented comparisons.

## Quick Run
- Install dependencies: `pip install -r requirements.txt`.
- Set `PYTHONPATH=src`.
- Execute: `python -m data_visualizer.cli datasets/comparison_grouped_bar/sample_groups.csv comparison_grouped_bar --output-dir outputs/comparison_grouped_bar`.
- Output: PNG chart at `outputs/comparison_grouped_bar/comparison_grouped_bar.png`.

## Dataset
- File: `datasets/comparison_grouped_bar/sample_groups.csv`
- Schema: `region`, `channel`, `revenue`
- Purpose: Illustrates how revenue splits between channels differ per region.

## Interpretation Tips
- Focus on the spread between grouped bars to identify standout categories.
- Use consistent ordering across charts when comparing multiple time periods.

## TODOs (10)
1. Accept custom aggregation functions (mean, median) via configuration.
2. Add confidence interval/error bars to convey variability within groups.
3. Enable sorting of groups by total value or max subcategory.
4. Provide optional data normalization to show share of group total.
5. Offer stacked/100% stacked variants for dense categorical sets.
6. Introduce drill-down capability that filters on a selected group.
7. Support color palette overrides and accessibility-safe defaults.
8. Auto-truncate long category labels and expose tooltips in interactive mode.
9. Export summary tables comparing highest and lowest performers per group.
10. Warn users when group/category cardinality exceeds readability thresholds.

## Potential Pitfalls
- Bars can look similar if scales are not adjusted; annotate key differences to reinforce insights.
- Too many hues overwhelm; consider grouping low-frequency categories into "Other".
