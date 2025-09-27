# Sample Datasets

Reference datasets are stored alongside their matching visualization build so users always know which data to try first.

## Layout
- `trend_line_chart/` — Monthly metric history for trend spotting.
- `comparison_grouped_bar/` — Regional revenue split by channel.
- `distribution_violin/` — Segment scores showcasing varied distribution shapes.
- `relationship_cluster_scatter/` — Customer metrics for clustering demonstrations.

When adding a new visualization:
1. Create a subdirectory named after the visualization key.
2. Include one or more representative CSV files (small enough for version control).
3. Document schema + purpose in the corresponding catalog README.
4. Note any preprocessing requirements or quirks in the dataset README.
