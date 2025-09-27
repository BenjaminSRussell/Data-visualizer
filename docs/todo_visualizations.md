# Visualization Program TODOs

These notes outline the next steps, goals, and potential pitfalls for each visualization program so new contributors see where differentiation work is headed.

## trend_line_chart — Line Chart
- **Goals**
  - Highlight temporal shifts that make a metric feel unique compared with its historical baseline.
  - Support multi-series comparisons to spot diverging trajectories.
- **TODOs**
  - Allow optional grouping/overlay to plot multiple series with legend support.
  - Add smoothing or rolling-mean option to reduce noise when data is volatile.
  - Provide automatic detection of breakpoints or anomalies to call out unusual periods.
- **Approach Ideas**
  - Extend `prepare_data` to accept a config describing `time_column`, `value_columns`, and aggregation windows.
  - Integrate `pandas` resampling for datasets that arrive in irregular intervals.
- **Considerations & Risks**
  - Trend charts can mislead if time zones or missing periods are not handled; document preprocessing expectations clearly.
  - Over-plotting many series can reduce readability—consider fallback to facetting.

## comparison_grouped_bar — Grouped Bar Chart
- **Goals**
  - Compare sub-categories inside each group to expose which combinations are exceptional.
  - Offer insight into relative share differences across segments.
- **TODOs**
  - Accept custom aggregation functions (mean, median) instead of hard-coded sums.
  - Add support for confidence intervals/error bars to show variability.
  - Enable sorting of groups by a key metric so the most important differences surface first.
- **Approach Ideas**
  - Use `seaborn.barplot` parameters for estimator and `ci`; expose those via config.
  - Consider stacked or normalized variants when group counts grow large.
- **Considerations & Risks**
  - Performance may degrade with very wide categorical data; warn about trimming categories.
  - Colors must stay colorblind-friendly if more hues are added—define a central palette.

## distribution_violin — Category Violin Plot
- **Goals**
  - Reveal distribution shapes and tails that indicate unique behaviors inside each category.
  - Quantify how much variance or skew differentiates segments.
- **TODOs**
  - Offer toggles for log scaling and bandwidth tweaks for small samples.
  - Add overlay of summary statistics (median, quartiles) in the legend for quick interpretation.
  - Provide optional facet-by-secondary-dimension to compare distributions across contexts (e.g., region).
- **Approach Ideas**
  - Leverage `seaborn.violinplot` parameters (`scale`, `bw`) driven by config.
  - Use `sns.swarmplot` overlay for showing individual observations when sample sizes are modest.
- **Considerations & Risks**
  - Violin plots can mislead with very small datasets; add guidance on minimum sample sizes.
  - Faceting multiplies charts quickly—ensure output size handles multiple panels without cramming.

## relationship_cluster_scatter — Clustered Scatter
- **Goals**
  - Automatically differentiate cohorts through clustering and dimensionality reduction.
  - Help analysts explain which feature combinations drive uniqueness.
- **TODOs**
  - Expose multiple clustering algorithms (DBSCAN, Agglomerative) and distance metrics.
  - Provide optional tooltips/labels for top outliers to explain why they are distant.
  - Persist model artifacts (centroids, PCA loadings) for reproducibility and storytelling.
- **Approach Ideas**
  - Wrap clustering choice in config; use `sklearn` pipelines to standardize features before modeling.
  - Offer auto-tuning for `n_clusters` using silhouette scores when the user does not supply a value.
- **Considerations & Risks**
  - PCA obscures original feature meaning; document loadings or offer biplot overlays.
  - High-dimensional datasets may need normalization—warn when data includes non-scaled features.

## CLI Orchestration — `data_visualizer.cli`
- **Goals**
  - Provide a seamless experience for selecting, configuring, and running visualizations.
  - Make it simple to catalog new programs as they are created.
- **TODOs**
  - Add subcommand for generating a markdown playbook entry from visualization metadata automatically.
  - Implement validation that checks required columns exist before execution.
  - Offer presets (YAML/JSON templates) so recurring analyses can be launched with a single command.
- **Approach Ideas**
  - Integrate `argparse` subparsers for commands like `run`, `generate-playbook`, `describe`.
  - Use schema validation (`pydantic` or `cerberus`) on configuration files to catch mistakes early.
- **Considerations & Risks**
  - Error messages need to stay human-readable—wrap stack traces with clear tips.
  - Supporting many optional dependencies may complicate installation; consider optional extras in `setup.cfg` later.

Keeping these todos visible should help prioritize the unique storytelling power of each visualization and ensure future additions slot cleanly into the workflow.
