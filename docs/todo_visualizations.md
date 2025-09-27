# Visualization Program TODOs

Refocused backlog centered on grouping, segmentation, and categorical comparisons. Time-series work has been archived so upcoming efforts highlight how cohorts differ, how categories stack up, and how clusters behave.

## Archived — `trend_line_chart`
- Preserve the existing implementation as-is; future work is paused while the catalog pivots toward grouping-first visuals.
- Move any new timeline ideas into a separate roadmap doc if time-based analysis returns to scope.

## comparison_grouped_bar — Grouped Bar Chart
- Ship share-of-total mode that normalizes each group to 100% while updating axis labels and legends.
- Introduce stacked and 100% stacked variants that reuse the existing palette logic and respect legend order.
- Add per-group drill-down hooks (CLI flag + API method) to regenerate the chart for a single cohort on demand.
- Provide automatic small-multiple layout when `facet_column` is supplied, reducing clutter for high-cardinality categories.
- Expose accessibility presets (color palettes + hatch patterns) to assist viewers with color-vision deficiencies.
- Offer export of top/bottom performers as a CSV summary with the chart metadata embedded for traceability.
- Allow optional sorting by statistical lift (e.g., difference from group mean) instead of raw totals.
- Generate optional tooltips/interactivity via Plotly so analysts can inspect precise values in-browser.
- Add threshold warnings that trigger when a group has too many categories for legibility and suggest filters.
- Document best-practice guidance for binning sparse categories before charting.

## distribution_violin — Category Violin Plot
- Layer an optional swarm/strip overlay that jitter-plots raw observations without obscuring the violin shape.
- Accept a facet column to produce small-multiple grids with shared y-axis scaling for apples-to-apples comparisons.
- Detect heavy tails or bimodality automatically and print interpretive notes alongside the figure.
- Provide configurable bandwidth/kernel selection surfaced through presets for common sample sizes.
- Support log and power transformations with guardrails that prevent invalid conversions.
- Emit a descriptive statistics CSV (mean, median, quartiles, sample size) for each category and facet.
- Allow shading of confidence intervals or percentile bands to highlight central mass vs. tails.
- Integrate optional reference distributions so teams can compare segments against a benchmark cohort.
- Surface accessibility-friendly color palettes and monochrome styling for print usage.
- Add CLI flag that toggles statistical test summaries (ANOVA, Kruskal-Wallis) with clear interpretation guidance.

## relationship_cluster_scatter — Clustered Scatter
- Add alternate clustering backends (DBSCAN, Agglomerative, Gaussian Mixture) selectable via config.
- Implement automatic `n_clusters` selection using silhouette scores when `n_clusters` is omitted.
- Surface outlier detection that labels points far from any cluster center with contextual annotations.
- Provide feature scaling options (standardization/min-max) with sensible defaults based on data distribution.
- Export cluster centroids, feature importances, and PCA loadings to a companion JSON/CSV for follow-up analysis.
- Enable 3D scatter and linked pair plots for datasets where two components are insufficient.
- Add interactive hover tooltips listing original feature values and record identifiers.
- Introduce stability diagnostics (multiple random seeds, variation reports) so analysts can judge segmentation robustness.
- Log model parameters, random seeds, and preprocessing steps directly into the output directory for reproducibility.
- Overlay known labels (if provided) to evaluate clustering quality against business-defined segments.

## Planned Visualizations (Grouping Focus)

### `comparison_heatmap`
- Visualize intersection of two categorical dimensions with custom aggregation functions.
- Provide hierarchical clustering of rows/columns to reveal latent structure.
- Offer divergence-from-total coloring (percentage point differences) for quick anomaly spotting.
- Support interactive drill-down by clicking on a cell to regenerate a filtered grouped bar chart.
- Emit a ranking table listing the strongest intersections for executive summaries.
- Include accessibility-friendly sequential/diverging palettes with automatic contrast checks.
- Add option to hide low-sample intersections and annotate the omission.
- Document guidance on pre-aggregating wide datasets into a cross-tab suitable for heatmap rendering.

### `hierarchy_treemap`
- Render nested categories (e.g., region → country → store) with area sized by metric of interest.
- Provide color-coding for variance from target or share-of-parent.
- Allow drill-down clicks to re-center the treemap on a child node while exporting the filtered dataset.
- Surface breadcrumb navigation and summary statistics for the currently selected hierarchy level.
- Support optional overlay of secondary metrics (e.g., profit margin) via color saturation or annotations.
- Produce printable PDF/PNG outputs alongside interactive HTML versions.
- Validate that hierarchy columns form a proper tree (no orphan nodes) before rendering.
- Offer presets for rectangular vs. squarified layouts depending on storytelling needs.

### `segmentation_parallel_sets`
- Display how cohorts flow across categorical stages (e.g., signup channel → plan type → retention status).
- Allow users to highlight a single path to trace how a cohort progresses.
- Export the underlying path counts as a CSV for reporting.
- Provide filtering on any stage to simplify dense diagrams.
- Add accessibility options (colorblind-safe palettes, line width scaling) for clarity in presentations.
- Integrate tooltips that list exact counts/percentages when hovering over ribbons.
- Support ordering heuristics that minimize ribbon crossings for readability.
- Include CLI shortcuts for loading preset funnels stored in YAML/JSON configs.

## CLI Orchestration — `data_visualizer.cli`
- Introduce `describe` and `plan` subcommands to list required columns, sample configs, and recommended grouping charts.
- Validate dataset schemas before execution, surfacing helpful messages when grouping/category columns are missing.
- Support named presets (JSON/YAML) pointing to grouping-focused visualizations with inline overrides.
- Add dry-run mode that prints planned aggregation/grouping operations without rendering.
- Emit a run manifest summarizing charts generated, filters applied, and output paths for audit trails.
- Provide integration hooks for exporting results to dashboards/shared drives used by analytics teams.
- Package the CLI as a console-script entry point for smoother installation.
- Log dependency versions and environment details to ensure reproducibility of grouping analyses.
- Offer optional profiling (load/prepare/render timing) to pinpoint bottlenecks in large categorical datasets.
- Wire up interactive backends (Plotly/Altair) as selectable render targets for grouping visuals that support it.

Revisit these lists with stakeholders to keep the grouping-first catalog aligned with storytelling goals around separation, organization, and categorical comparison.
