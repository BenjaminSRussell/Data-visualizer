# Data Visualizer Toolkit

Purpose-built workspace for experimenting with contextual groupings and differentiated storytelling across datasets. The repo is organized so every visualization program ships with:
- a runnable example,
- clear instructions and interpretation notes,
- a list of ten forward-looking TODOs to keep enhancements user-focused.

## Repository Map
```
.
├── catalog/                     # User-facing builds, one folder per visualization program
│   ├── comparison_grouped_bar/  # Instructions + TODOs for categorical comparisons
│   ├── distribution_violin/     # Distribution fingerprints per segment
│   ├── relationship_cluster_scatter/  # Cohort discovery via clustering
│   └── trend_line_chart/        # Temporal storylines and anomaly detection ideas
├── datasets/                    # Sample CSVs aligned with catalog builds
│   ├── README.md
│   └── <program_key>/sample_*.csv
├── docs/                        # Additional planning notes and backlog references
│   ├── prioritized_issues.md    # High-impact backlog distilled into ticket-ready items
│   └── todo_visualizations.md   # Full TODO inventory per visualization
├── requirements.txt             # Python dependencies (install in a virtualenv)
├── scripts/                     # Placeholder for automation helpers
└── src/data_visualizer/         # CLI + reusable visualization interfaces
    ├── cli.py                   # `python -m data_visualizer.cli ...`
    └── visualizations/          # Program implementations with embedded TODO lists
```

Tip: generated charts land in `outputs/<program_key>/` (ignored by git). Keep only curated artifacts.

## Quick Start
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Make the source importable: `export PYTHONPATH=src` (or `pip install -e .` once packaging exists).
4. Discover available visualizations: `python -m data_visualizer.cli --list`.
5. Run any catalog build, e.g.:
   - `python -m data_visualizer.cli datasets/trend_line_chart/sample_timeseries.csv trend_line_chart --output-dir outputs/trend_line_chart`
   - `python -m data_visualizer.cli datasets/comparison_grouped_bar/sample_groups.csv comparison_grouped_bar --output-dir outputs/comparison_grouped_bar`

Each catalog README restates the command, explains the dataset, and highlights potential interpretation pitfalls so new users can explore confidently.

## Visualization Builds at a Glance
- **Trend Line Chart (`trend_line_chart`)**
  - Use case: Surface trend breaks and seasonality to explain when a metric behaves differently.
  - Catalog notes: `/catalog/trend_line_chart/README.md` with ten TODOs covering multi-series overlays, anomaly callouts, interactive output, and more.
  - Dataset: `/datasets/trend_line_chart/sample_timeseries.csv`.
- **Grouped Bar Comparison (`comparison_grouped_bar`)**
  - Use case: Contrast sub-categories inside groups to expose standout regions or channels.
  - Catalog notes enumerate enhancements like custom aggregations, normalization, and drill-down.
  - Dataset: `/datasets/comparison_grouped_bar/sample_groups.csv`.
- **Category Violin Distribution (`distribution_violin`)**
  - Use case: Reveal distribution shape, skew, and outliers for each segment to flag unique behaviors.
  - Catalog TODOs target log-scaling options, heavy-tail detection, and descriptive table exports.
  - Dataset: `/datasets/distribution_violin/sample_category_scores.csv`.
- **Clustered Scatter Relationships (`relationship_cluster_scatter`)**
  - Use case: Auto-discover cohorts with PCA + clustering and spotlight outliers.
  - Catalog TODOs outline algorithm swaps, optimal cluster discovery, and interaction upgrades.
  - Dataset: `/datasets/relationship_cluster_scatter/sample_customer_segments.csv` (with optional `kmeans_config.json`).

Every corresponding implementation under `src/data_visualizer/visualizations/...` starts with the same ten-item TODO list in the module docstring, keeping engineers and analysts aligned on how to push differentiation further.

## Extending the Catalog
1. **Duplicate the pattern**
   - Create `catalog/<new_key>/README.md` (include quick run, dataset notes, interpretation tips, ten TODOs, and pitfalls).
   - Place representative CSV samples under `datasets/<new_key>/`.
   - Add configs or reusable scripts alongside the catalog README if needed.
2. **Implement the visualization**
   - Add a module to `src/data_visualizer/visualizations/<category>/<new_key>.py` that subclasses `Visualization`.
   - Include a `VisualizationMetadata` object with meaningful description, tags, and URL reference.
   - Document ten TODOs within the module docstring (mirror the catalog README for consistency).
3. **Update docs**
   - Link the new build from this README and, if needed, expand `docs/todo_visualizations.md`.
   - Capture priority follow-up work in `docs/prioritized_issues.md` so ticket queues stay aligned with product goals.

## Why This Organization Helps Differentiate Data
- **User-first entry points**: Catalog folders package the dataset, command, and interpretation notes so analysts don’t dig through code just to try a chart.
- **Embedded roadmaps**: Ten TODOs per program (catalog README + module docstring) make it obvious how each visualization can evolve to uncover more unique signals.
- **Data-to-output traceability**: Datasets live beside the builds they power, clarifying how raw data becomes a contextualized graphic.
- **Scalable discovery**: The CLI registry enumerates every visualization using metadata, enabling future automation like playbook generation or web front-ends.

## Playbook Automation Roadmap
Longer-term, the goal remains to compile a 20–30 entry visualization playbook with authoritative URLs and applicability notes. The steps outlined in `docs/todo_visualizations.md` and the catalog TODO lists feed directly into that deliverable—each improvement sharpens how we explain uniqueness, compare cohorts, and surface hidden structures in new datasets.
