# Visualization Program TODOs

Source of truth for program-specific enhancements. Each section mirrors the ten-item backlog captured in the catalog README and module docstring so contributors can pick up work quickly.

## trend_line_chart — Line Chart
- Support multiple value columns to compare peer metrics on the same timeline.
- Add rolling-average and seasonal decomposition overlays for noisy series.
- Highlight detected anomalies or regime changes directly on the chart.
- Accept irregular time intervals and resample to user-defined frequencies.
- Provide automatic axis formatting for hourly/daily/weekly granularities.
- Enable interactive output (Plotly/Altair) for hover inspection of points.
- Offer export of aggregated statistics (trend slope, CAGR, breakpoints).
- Integrate confidence bands for forecasts when a model is supplied.
- Allow faceting by category to split unique trend profiles side-by-side.
- Document best practices for handling missing periods and time zone normalization.

## comparison_grouped_bar — Grouped Bar Chart
- Accept custom aggregation functions (mean, median) via configuration.
- Add confidence interval/error bars to convey variability within groups.
- Enable sorting of groups by total value or max subcategory.
- Provide optional data normalization to show share of group total.
- Offer stacked/100% stacked variants for dense categorical sets.
- Introduce drill-down capability that filters on a selected group.
- Support color palette overrides and accessibility-safe defaults.
- Auto-truncate long category labels and expose tooltips in interactive mode.
- Export summary tables comparing highest and lowest performers per group.
- Warn users when group/category cardinality exceeds readability thresholds.

## distribution_violin — Category Violin Plot
- Allow bandwidth and kernel adjustments to suit small or large samples.
- Provide log-scale option for highly skewed distributions.
- Overlay quartile/median lines and summary statistics in the legend.
- Add jittered raw points (swarmplot) for low sample counts.
- Support secondary facet dimension for contextual comparisons (e.g., region).
- Include automatic detection of heavy tails or bimodality with textual notes.
- Offer histogram/boxplot hybrids when stakeholders prefer familiar shapes.
- Implement density difference highlights to show how one segment deviates from another.
- Export segment-specific descriptive statistics tables alongside the chart.
- Warn when category sample size falls below a recommended minimum.

## relationship_cluster_scatter — Clustered Scatter
- Add support for alternative clustering algorithms (DBSCAN, Agglomerative, Gaussian Mixture).
- Provide feature scaling options (standardization, min-max) controlled via config.
- Auto-select optimal `n_clusters` using silhouette or elbow heuristics when not specified.
- Export cluster centroids and PCA component loadings for deeper analysis.
- Enable interactive tooltips listing record identifiers and feature values.
- Allow 3D scatter or pair plot outputs when two components are insufficient.
- Flag outliers beyond a configurable distance threshold and label them on the chart.
- Offer cluster stability diagnostics (e.g., repeated runs) to build trust in segmentation.
- Log model parameters and random seeds for reproducibility.
- Integrate optional supervised overlay (e.g., color by known label) to validate clustering quality.

## CLI Orchestration — `data_visualizer.cli`
- Add subcommands for `run`, `describe`, and `generate-playbook` to streamline workflows.
- Surface visualization metadata (required columns, description, example URL) before execution.
- Validate dataset schemas against visualization expectations with friendly error messages.
- Support configuration files in JSON/YAML plus inline overrides via CLI flags.
- Introduce presets that bundle dataset + visualization + config into one shortcut command.
- Offer dry-run mode to print planned operations without generating charts.
- Track execution logs and output paths for auditability.
- Allow optional profiling of runtime (dataset load, prepare, render) to spot bottlenecks.
- Provide hooks for publishing generated charts to dashboards or shared drives.
- Package CLI as console script entry point for easier installation.

Revisit these lists alongside stakeholder feedback to keep the catalog aligned with the overarching goal: exposing what makes each dataset unique.
