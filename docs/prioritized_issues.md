# Prioritized Issue Backlog

Grouping-first roadmap distilled into execution-ready tickets. Time-series enhancements are archived until further notice so the team can double down on categorical separation, segmentation, and comparison stories.

## Cross-Cutting
- [ ] **DV-900 – Add SciPy runtime dependency (Critical)**
  - *Why*: `distribution_violin` imports `scipy.stats`, yet `requirements.txt` omits SciPy. Fresh installs fail before charts render.
  - *Scope*: Add SciPy to `requirements.txt`, mention it in install docs, and smoke-test `ViolinPlot` after a clean install.
  - *Acceptance*: `pip install -r requirements.txt` succeeds locally and on CI; running the violin plot no longer raises a missing dependency error.

## Grouped Bar Comparison (`comparison_grouped_bar`)
- [ ] **DV-013 – Share-of-total normalization (High)**
  - *Why*: Stakeholders want proportional stories; raw sums hide relative performance.
  - *Scope*: Provide a config switch that normalizes each group to 100%, updates axis labels, and documents caveats.
  - *Acceptance*: Enabling normalization renders percent-based bars whose totals per group equal 100%.
- [ ] **DV-014 – Stacked variants (Medium)**
  - *Why*: Side-by-side bars become unreadable with many categories.
  - *Scope*: Offer stacked and 100% stacked renderers, reusing palette logic and ensuring legend accuracy.
  - *Acceptance*: Switching to stacked mode produces a valid chart without overlapping bars or legend errors.
- [ ] **DV-015 – Drill-down workflow (Medium)**
  - *Why*: Analysts need to isolate a single group without munging data manually.
  - *Scope*: Add CLI flag/API hook to filter to one group and regenerate the chart plus a CSV export.
  - *Acceptance*: Providing a group identifier yields a filtered chart and summary file without code changes.

## Category Violin Distribution (`distribution_violin`)
- [ ] **DV-023 – Swarm overlay toggle (High)**
  - *Why*: Small samples look empty; raw points build trust in the distribution view.
  - *Scope*: Layer an optional swarm/strip plot with jitter, balancing overlap and legend clarity.
  - *Acceptance*: Enabling the option displays individual observations without obscuring the violin shape.
- [ ] **DV-024 – Facet support (Medium)**
  - *Why*: Teams often compare distributions across a secondary segment (e.g., region).
  - *Scope*: Accept a facet column and render small-multiple grids with synchronized axes.
  - *Acceptance*: Supplying a facet column yields a tidy grid whose panels share axis scales and titles.
- [ ] **DV-025 – Tail/modality alerts (Medium)**
  - *Why*: Hidden structure goes unnoticed without textual guidance.
  - *Scope*: Detect heavy tails or bimodality (e.g., Hartigan’s dip test) and surface explanatory notes alongside the plot.
  - *Acceptance*: Running on a crafted dataset triggers an alert describing the detected pattern.

## Clustered Scatter Relationships (`relationship_cluster_scatter`)
- [ ] **DV-030 – Alternate clustering algorithms (High)**
  - *Why*: KMeans struggles with non-spherical clusters, limiting adoption.
  - *Scope*: Support DBSCAN, Agglomerative, and Gaussian Mixture selection via config plus parameter validation.
  - *Acceptance*: Switching algorithms updates cluster assignments and chart legends without errors.
- [ ] **DV-031 – Automatic cluster count selection (High)**
  - *Why*: Analysts often do not know the ideal `n_clusters` ahead of time.
  - *Scope*: Implement silhouette-based heuristics when `n_clusters` is absent, logging the decision.
  - *Acceptance*: Omitting `n_clusters` still produces a chart and records the auto-selected value.
- [ ] **DV-032 – Outlier flagging & labeling (Medium)**
  - *Why*: Distant points signal data quality issues or emerging cohorts.
  - *Scope*: Compute distance-to-centroid scores, mark outliers visually, and emit a textual summary.
  - *Acceptance*: Running on the sample dataset highlights at least one synthetic outlier with annotations.

## Planned Visualizations (Grouping Expansion)
- [ ] **DV-110 – Launch `comparison_heatmap` baseline (High)**
  - *Why*: Cross-tab heatmaps surface intersections between categories and reveal structural pockets quickly.
  - *Scope*: Build the visualization class, metadata, sample dataset, and catalog README focused on grouping intersections.
  - *Acceptance*: CLI command renders a heatmap from the sample dataset; README documents usage and TODOs.
- [ ] **DV-120 – Launch `hierarchy_treemap` baseline (Medium)**
  - *Why*: Hierarchical segments need a dedicated view that communicates share-of-parent stories.
  - *Scope*: Implement treemap visualization, add hierarchy dataset, and capture documentation/playbook entry.
  - *Acceptance*: Running the CLI on the sample hierarchy dataset outputs a treemap PNG/HTML with breadcrumb notes.
- [ ] **DV-130 – Launch `segmentation_parallel_sets` baseline (Medium)**
  - *Why*: Funnel and lifecycle analyses require visualizing how cohorts flow across categorical stages.
  - *Scope*: Implement parallel sets renderer with sample data, CLI wiring, and catalog README.
  - *Acceptance*: Sample run generates a parallel sets visualization with hover tooltips and stage filtering options.

## CLI Orchestration (`data_visualizer.cli`)
- [ ] **DV-100 – Schema validation before execution (High)**
  - *Why*: Users currently hit cryptic errors inside individual visualizations.
  - *Scope*: Validate required columns/data types pre-run and surface actionable error messages.
  - *Acceptance*: Running with a malformed CSV prints a friendly validation error instead of a stack trace.
- [ ] **DV-101 – Playbook entry generator (Medium)**
  - *Why*: Product teams want markdown snippets summarizing grouping visuals.
  - *Scope*: Add a subcommand that outputs README-ready blocks sourced from `VisualizationMetadata` and config hints.
  - *Acceptance*: Command prints formatted markdown matching the catalog template.
- [ ] **DV-102 – Preset loader for grouping scenarios (Medium)**
  - *Why*: Analysts repeat the same dataset + visualization combos.
  - *Scope*: Support named presets (JSON/YAML) and allow inline overrides with grouping-focused defaults.
  - *Acceptance*: Invoking a preset by name loads dataset, key, and config automatically, with optional overrides.
