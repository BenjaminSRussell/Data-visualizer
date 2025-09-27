# Visualization Catalog Builds

Each subfolder packages a user-friendly workflow for a specific visualization program. The pattern keeps datasets, configs, run instructions, and enhancement roadmap in one place so analysts can explore unique data stories without reading code.

## Folder Structure
- `<program_slug>/README.md` — Run instructions, dataset description, interpretation tips, and ten TODOs.
- `<program_slug>/` optional config files — e.g., preset model parameters.
- Outputs default to `outputs/<program_slug>/` when the CLI is executed.

### Available Builds
- `trend_line_chart/` — Time-series narrative with anomaly considerations.
- `comparison_grouped_bar/` — Category comparisons spotlighting outliers.
- `distribution_violin/` — Segment fingerprinting via distribution shape.
- `relationship_cluster_scatter/` — Automated cohort discovery with clustering.

Add new visualization builds by mirroring this layout: create a dataset in `../datasets/<slug>/`, author a README with quick-start + TODOs, and commit any recommended configs.
