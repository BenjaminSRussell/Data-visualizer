# Data Visualizer Overview Plan

## Repository Layout
```
.
├── data
│   ├── sample_customer_segments.csv  # Numeric features for cohort discovery
│   ├── sample_groups.csv             # Example dataset for grouped comparisons
│   └── sample_timeseries.csv         # Example dataset for temporal trends
├── requirements.txt                  # Python dependencies for the CLI + samples
├── src
│   └── data_visualizer
│       ├── __init__.py
│       ├── cli.py                    # Command line entry-point for running visuals
│       └── visualizations
│           ├── __init__.py           # Visualization discovery helpers
│           ├── base.py               # Shared interface + metadata contract
│           ├── comparisons
│           │   ├── __init__.py
│           │   └── grouped_bar.py    # Seaborn grouped bar example
│           ├── distributions
│           │   ├── __init__.py
│           │   └── violin_plot.py    # Segment-specific distribution fingerprinting
│           ├── relationships
│           │   ├── __init__.py
│           │   └── cluster_scatter.py# PCA + KMeans to expose unique cohorts
│           └── trends
│               ├── __init__.py
│               └── line_chart.py     # Matplotlib line chart example
└── scripts
    └── README.md                     # Reserve space for future automation scripts
```

## Quick Start
- Create and activate a virtual environment, then install dependencies: `pip install -r requirements.txt`.
- Export the source directory to `PYTHONPATH` (or install the package in editable mode): `export PYTHONPATH=src`.
- List available visualizations: `python -m data_visualizer.cli --list`.
- Run a visualization on a dataset: `python -m data_visualizer.cli data/sample_timeseries.csv trend_line_chart`.
  - Adjust `--output-dir`, `--separator`, `--encoding`, and `--config` (JSON file) as needed.
- Generated charts are saved under `outputs/` by default; add this directory to version control only when the artifacts are intentionally curated.

## Differentiating Data Through Visualization
- **Trend Line Chart (`trend_line_chart`)** reveals directional change so you can pinpoint periods where the dataset behaves unlike its baseline.
- **Grouped Bar Chart (`comparison_grouped_bar`)** surfaces relative gaps between peer categories, quickly separating outliers from the pack.
- **Category Violin Plot (`distribution_violin`)** traces the full distribution shape for each segment; unique long tails or multimodal patterns flag differentiated customer groups.
- **Clustered Scatter (`relationship_cluster_scatter`)** uses PCA + KMeans to auto-discover cohorts and color-codes them so emergent clusters or borderline records stand out immediately.

Together these examples form a template for layering more specialized visuals. Each module’s metadata describes *why* a chart is useful, ensuring future additions articulate the unique insight they unlock.

## Adding a New Visualization
1. Create a new module under `src/data_visualizer/visualizations/<category>/<slug>.py`.
2. Subclass `Visualization` from `visualizations.base` and attach a `VisualizationMetadata` describing the chart.
3. Implement `prepare_data` (optional data wrangling) and `render` (produce the graphic and return the saved file path).
4. Reference authoritative documentation in `metadata.example_url` so the playbook can link to working examples.
5. Add or update sample datasets in `data/` if the visualization requires representative input.

Keeping metadata rich allows the CLI, documentation generators, or future dashboards to discover and explain each option automatically.

## Automation Roadmap for the Playbook

### Project Vision
Create a reusable workflow that ingests an arbitrary dataset, profiles it for contextual groupings, and surfaces 20–30 distinct visualization concepts—each paired with a URL that demonstrates how the view teaches something meaningful about the data. The final deliverable is a curated document (e.g., `visualization-playbook.md`) that stakeholders can browse to select the best visualization strategy for their scenario.

### Key Deliverable
- **Visualization Playbook**: A document with 20–30 entries. Every entry must include
  - Short description of the insight the visualization highlights.
  - Dataset characteristics or use-cases where the visualization shines.
  - URL to an example, tutorial, or reference implementation.

### Execution Plan
1. **Dataset Intake & Goals**
   - Collect metadata: data types, volume, temporal coverage, geographic scope, categorical hierarchies.
   - Interview or document stakeholder questions so every recommended chart answers a real business or research need.
2. **Contextual Grouping Discovery**
   - Use clustering, dimensionality reduction, or similarity metrics to locate natural groupings.
   - Catalog categorical hierarchies, time-based segments, or geographic clusters that merit their own views.
3. **Insight Mapping**
   - Map each stakeholder question or grouping to visualization families (trend, comparison, composition, relationship, distribution, flow, spatial, text analytics, network).
   - Prioritize visualizations that reveal actionable differences or trends as opposed to decorative charts.
4. **Visualization Research & Curation**
   - For each candidate visualization:
     - Document when to use it, how to interpret it, and pitfalls to avoid.
     - Gather authoritative URLs (e.g., Observable notebooks, Vega-Lite specs, D3 examples, industry case studies).
   - Ensure coverage across multiple difficulty levels: quick wins, intermediate techniques, advanced/interactive visuals.
5. **Playbook Assembly**
   - Organize entries by insight category with consistent formatting.
   - Provide tooling suggestions (Python/Altair, R/ggplot2, JS/D3, BI platforms, GIS tools) when relevant.
   - Add cross-links between complementary visuals (e.g., pair Sankey diagrams with flow heatmaps).
6. **Validation & Iteration**
   - Share the draft with stakeholders for feedback on clarity and relevance.
   - Refine descriptions, replace weak URLs, and add notes about data preparation requirements.
   - Capture lessons learned for future datasets.

### Suggested Visualization Coverage
Aim for representation from each block below to reach 20–30 strong entries:
- **Trends & Temporal**: line charts, horizon charts, cycle plots, ridgeline plots.
- **Comparisons & Rankings**: bar charts, slope graphs, bump charts, lollipop charts, dot plots.
- **Distributions**: histograms, violin plots, boxen plots, Joy plots, empirical CDFs.
- **Relationships & Correlations**: scatterplots, pair plots, correlograms, hexbin maps, contour plots.
- **Multivariate & Dimensionality Reduction**: parallel coordinates, radar charts, t-SNE/UMAP projections, decision trees.
- **Part-to-Whole**: treemaps, sunbursts, Marimekko charts, stacked bars, waterfall charts.
- **Flow & Process**: Sankey diagrams, alluvial diagrams, chord diagrams, funnel charts.
- **Network & Graphs**: force-directed graphs, adjacency matrices, hive plots.
- **Spatial & Geospatial**: choropleth maps, dot-density maps, isochrone maps, 3D terrain overlays.
- **Text & Semantics**: topic modeling heatmaps, word embeddings plots, co-occurrence networks.
- **Anomaly & Change Detection**: control charts, cumulative sum (CUSUM) charts, change point visualizations.
- **Interactive & Narrative**: scrollytelling pages, dashboards with drill-downs, storyboards, animation timelines.

### Visual Entry Template
```
## <Visualization Name>
- Insight Type: Trend / Comparison / …
- Best For: <Data scenarios>
- Why It Teaches Something: <Key takeaway users learn>
- Example URL: <https://…>
- Tooling: <Libraries or platforms>
- Prep Notes: <Data wrangling or grouping requirements>
```

### Next Steps
- Stand up a lightweight notebook or script to automate metadata profiling and grouping discovery.
- Start populating the playbook with 3–5 entries per category, validating each with the dataset at hand.
- Iterate with stakeholders until the document hits 20–30 high-quality, insight-driven visualization URLs.
