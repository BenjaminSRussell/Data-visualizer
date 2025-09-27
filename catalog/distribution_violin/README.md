# Category Violin Distribution Build

Guide for the `distribution_violin` program aimed at uncovering segment-specific distribution shapes.

## Quick Run
- Install dependencies: `pip install -r requirements.txt`.
- Set `PYTHONPATH=src`.
- Execute: `python -m data_visualizer.cli datasets/distribution_violin/sample_category_scores.csv distribution_violin --output-dir outputs/distribution_violin`.
- Output: PNG chart at `outputs/distribution_violin/distribution_violin.png`.

## Dataset
- File: `datasets/distribution_violin/sample_category_scores.csv`
- Schema: `segment`, `score`
- Purpose: Demonstrates varied spread and skew for category scores.

## Interpretation Tips
- Thick areas reveal where most observations cluster; use them to compare segment consistency.
- Long tails or multiple peaks highlight subgroups worth deeper investigation.

## TODOs (10)
1. Allow bandwidth and kernel adjustments to suit small or large samples.
2. Provide log-scale option for highly skewed distributions.
3. Overlay quartile/median lines and summary statistics in the legend.
4. Add jittered raw points (swarmplot) for low sample counts.
5. Support secondary facet dimension for contextual comparisons (e.g., region).
6. Include automatic detection of heavy tails or bimodality with textual notes.
7. Offer histogram/boxplot hybrids when stakeholders prefer familiar shapes.
8. Implement density difference highlights to show how one segment deviates from another.
9. Export segment-specific descriptive statistics tables alongside the chart.
10. Warn when category sample size falls below a recommended minimum.

## Potential Pitfalls
- Unequal sample sizes can make violins look deceptively similar; annotate counts.
- Overlapping violins in interactive mode can obstruct selection—consider side-by-side layout.
