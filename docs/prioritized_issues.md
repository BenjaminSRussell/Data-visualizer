# Prioritized Issue Backlog

These entries translate the highest-impact TODOs into trackable issues. Prefix `DV-` IDs can be used when opening tickets in your preferred tracker.

## Trend Line Chart (`trend_line_chart`)
- [ ] **DV-001 – Multi-series timeline support (High)**
  - *Why*: Comparing peer metrics side-by-side is the most common request from stakeholders and unlocks richer discussions about divergence.
  - *Scope*: Extend configuration to accept multiple value columns, update legend handling, and ensure axis scaling remains readable with overlapping series.
  - *Acceptance*: Users can specify several metrics in config; chart renders each with distinct styling and legend entries without errors.
- [ ] **DV-002 – Automated anomaly callouts (High)**
  - *Why*: Highlighting breakpoints or regime changes makes trend charts immediately insightful for anomaly detection use cases.
  - *Scope*: Integrate a simple anomaly detector (e.g., rolling z-score) and annotate flagged points directly on the plot.
  - *Acceptance*: Running the sample dataset with anomalies enabled produces callouts and optional textual summary.
- [ ] **DV-003 – Rolling-average overlay (Medium)**
  - *Why*: Smoothing volatile data reduces noise; it is often requested during early exploratory analyses.
  - *Scope*: Add optional moving average window support controlled via config, including legend entry and axis alignment.
  - *Acceptance*: Users can toggle smoothing on/off; chart displays both raw and smoothed lines.

## Grouped Bar Comparison (`comparison_grouped_bar`)
- [ ] **DV-010 – Configurable aggregation functions (High)**
  - *Why*: Teams frequently compare averages or medians; being locked to sums limits applicability.
  - *Scope*: Allow users to choose `sum`, `mean`, `median`, etc., and ensure tooltips/legends reflect the choice.
  - *Acceptance*: Configuration selecting an estimator updates the chart output accordingly.
- [ ] **DV-011 – Confidence interval/error bars (High)**
  - *Why*: Visualizing variability clarifies whether differences are statistically meaningful.
  - *Scope*: Surface CI options from seaborn, expose through config, and document required data columns.
  - *Acceptance*: Running with CI enabled shows error bars sized to resampled or bootstrap estimates.
- [ ] **DV-012 – Group sorting by key metric (Medium)**
  - *Why*: Sorting highlights the most important categories, guiding attention to high/low performers.
  - *Scope*: Implement sorting controls (ascending/descending by total or selected subcategory).
  - *Acceptance*: Configured sort order is reflected in the rendered chart.

## Category Violin Distribution (`distribution_violin`)
- [ ] **DV-020 – Log-scale + bandwidth configuration (High)**
  - *Why*: Without control over bandwidth or log scaling, skewed data becomes unreadable, limiting adoption.
  - *Scope*: Expose seaborn bandwidth parameters and y-axis scaling options through config.
  - *Acceptance*: Users can switch to log scale and adjust bandwidth, verifying changes in sample output.
- [ ] **DV-021 – Summary statistic overlays (High)**
  - *Why*: Decision-makers need medians/quartiles to interpret violins quickly without consulting raw numbers.
  - *Scope*: Overlay box or point summaries and add legend notes for clarity.
  - *Acceptance*: Chart shows median/quartile markers matching computed statistics.
- [ ] **DV-022 – Swarmplot jitter for raw points (Medium)**
  - *Why*: With small samples, seeing actual observations builds trust in the distribution depiction.
  - *Scope*: Add optional jittered dots layered over each violin, controlled via config.
  - *Acceptance*: Enabling the option renders individual points without excessive overlap.

## Clustered Scatter Relationships (`relationship_cluster_scatter`)
- [ ] **DV-030 – Alternate clustering algorithms (High)**
  - *Why*: KMeans struggles with non-spherical clusters; providing DBSCAN/Agglomerative makes the tool useful across more datasets.
  - *Scope*: Support algorithm selection via config, including parameter validation and fallbacks.
  - *Acceptance*: Users can switch algorithms and regenerate charts with distinct cluster assignments.
- [ ] **DV-031 – Automatic cluster count selection (High)**
  - *Why*: Analysts may not know how many clusters to request; automation accelerates exploration.
  - *Scope*: Implement silhouette or elbow heuristics when `n_clusters` is omitted; document behavior.
  - *Acceptance*: Running without `n_clusters` picks an optimal value and records the decision in output logs.
- [ ] **DV-032 – Outlier flagging & labeling (Medium)**
  - *Why*: Identifying points distant from any cluster highlights emerging behaviors or data issues.
  - *Scope*: Compute distance-to-centroid scores, mark outliers visually, and provide descriptive text.
  - *Acceptance*: Sample run highlights at least one outlier with annotation.

## CLI Orchestration (`data_visualizer.cli`)
- [ ] **DV-100 – Schema validation before execution (High)**
  - *Why*: Early detection of missing columns prevents confusing runtime failures for analysts.
  - *Scope*: Validate dataset headers against visualization requirements, emitting clear messages.
  - *Acceptance*: Running with a malformed CSV yields a helpful validation error instead of a stack trace.
- [ ] **DV-101 – Playbook entry generator (High)**
  - *Why*: Automating markdown snippets accelerates compilation of the 20–30 visualization playbook.
  - *Scope*: Add a CLI subcommand that prints a formatted entry from `VisualizationMetadata`.
  - *Acceptance*: Command outputs markdown aligning with the template in the README.
- [ ] **DV-102 – Preset configuration loader (Medium)**
  - *Why*: Analysts often repeat the same combinations; presets minimize typing and errors.
  - *Scope*: Support JSON/YAML presets referenced by name; document the search path.
  - *Acceptance*: Users run a preset by name, and the CLI loads dataset + key + config automatically.
