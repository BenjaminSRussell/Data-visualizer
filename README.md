# Data Visualizer Toolkit

Purpose-built workspace for professional data visualization and analysis across categorical datasets. The repo is organized so every visualization program ships with:
- a runnable example,
- clear instructions and interpretation notes,
- comprehensive advanced features for production use.

## Repository Map
```
.
├── catalog/                     # User-facing builds, one folder per visualization program
│   ├── comparison_grouped_bar/  # Advanced categorical comparison tools
│   ├── distribution_violin/     # Distribution fingerprints per segment
│   ├── relationship_cluster_scatter/  # Cohort discovery via clustering
│   └── trend_line_chart/        # Temporal storylines and anomaly detection ideas
├── datasets/                    # Sample CSVs aligned with catalog builds
│   ├── README.md
│   └── <program_key>/sample_*.csv
├── docs/                        # Documentation and feature tracking
│   └── COMPLETED_FEATURES.md    # Comprehensive list of implemented features
├── requirements.txt             # Python dependencies (install in a virtualenv)
├── scripts/                     # Placeholder for automation helpers
└── src/data_visualizer/         # CLI + reusable visualization interfaces
    ├── cli.py                   # `python -m data_visualizer.cli ...`
    └── visualizations/          # Advanced visualization implementations
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

## Interactive GUI
For a more interactive experience, the toolkit now includes a graphical user interface (GUI). The GUI allows you to load datasets, select visualizations, and customize their options in real-time.

To launch the GUI, run the following command from the root of the repository:
```bash
python -m src.data_visualizer.gui.main
```

For a detailed walkthrough of the GUI's features, please see the [**GUI Guide**](./docs/GUI_GUIDE.md).

## Recent Enhancements

### ✅ **Multi-Series Timeline Support** (DV-001)
- Line charts now support multiple value columns for peer metric comparisons
- Smart legend handling and color palette selection
- Optional rolling averages for noise reduction
- Enhanced datetime formatting for time-based data

### ✅ **Advanced Bar Chart Features** (DV-013, DV-014)
- Share-of-total normalization mode showing percentage contributions
- Stacked and 100% stacked bar chart variants
- Enhanced aggregation functions (mean, median, std, count)
- Professional color palettes with accessibility considerations

### ✅ **Enhanced Violin Plots** (DV-020)
- Log-scale support for skewed distributions
- Configurable bandwidth for kernel density estimation
- Automated outlier detection with IQR-based flagging
- Statistical annotation overlays

### ✅ **Robust CLI Validation** (DV-100)
- Pre-execution schema validation prevents cryptic runtime errors
- Clear error messages with dataset summary information
- Column type validation and data quality checks
- Friendly user feedback with actionable suggestions

### ✅ **Enhanced Dependencies** (DV-900)
- Added SciPy for advanced statistical computations
- Improved error handling for missing dependencies
- Better test coverage for optional libraries

## Testing
- Execute `PYTHONPATH=src pytest` to run smoke tests that import each visualization, render a basic output, and confirm invalid inputs raise helpful errors. Optional dependencies such as matplotlib, seaborn, and scikit-learn are loaded lazily—tests are skipped automatically if they are not installed.

## Visualization Builds at a Glance
- **Trend Line Chart (`trend_line_chart`)**
  - Use case: Surface trend breaks and seasonality to explain when a metric behaves differently.
  - **✅ FEATURES**: Multi-series support, anomaly detection, trend analysis, confidence bands
  - Dataset: `/datasets/trend_line_chart/sample_timeseries.csv`.
- **Grouped Bar Comparison (`comparison_grouped_bar`)**
  - Use case: Contrast sub-categories inside groups to expose standout regions or channels.
  - **✅ FEATURES**: Advanced aggregations, normalization, stacked variants, statistical analysis
  - Dataset: `/datasets/comparison_grouped_bar/sample_groups.csv`.
- **Category Violin Distribution (`distribution_violin`)**
  - Use case: Reveal distribution shape, skew, and outliers for each segment to flag unique behaviors.
  - **✅ FEATURES**: Distribution analysis, outlier detection, statistical testing, pattern alerts
  - Dataset: `/datasets/distribution_violin/sample_category_scores.csv`.
- **Clustered Scatter Relationships (`relationship_cluster_scatter`)**
  - Use case: Auto-discover cohorts with PCA + clustering and spotlight outliers.
  - **✅ FEATURES**: Multiple algorithms, auto-optimization, outlier detection, stability analysis
  - Dataset: `/datasets/relationship_cluster_scatter/sample_customer_segments.csv`.

All visualizations include comprehensive feature sets with statistical analysis, export capabilities, and professional-quality outputs suitable for production use.

## Extending the Catalog
1. **Duplicate the pattern**
   - Create `catalog/<new_key>/README.md` (include quick run, dataset notes, interpretation tips, and pitfalls).
   - Place representative CSV samples under `datasets/<new_key>/`.
   - Add configs or reusable scripts alongside the catalog README if needed.
2. **Implement the visualization**
   - Add a module to `src/data_visualizer/visualizations/<category>/<new_key>.py` that subclasses `Visualization`.
   - Include a `VisualizationMetadata` object with meaningful description, tags, and URL reference.
   - Document comprehensive features within the module docstring for consistency.
3. **Update docs**
   - Link the new build from this README and document features in `docs/COMPLETED_FEATURES.md`.
   - Capture priority follow-up work in `docs/prioritized_issues.md` so ticket queues stay aligned with product goals.

## Why This Organization Helps Differentiate Data
- **User-first entry points**: Catalog folders package the dataset, command, and interpretation notes so analysts don’t dig through code just to try a chart.
- **Feature-rich implementations**: Each visualization includes advanced analysis capabilities and export options for professional use.
- **Data-to-output traceability**: Datasets live beside the builds they power, clarifying how raw data becomes a contextualized graphic.
- **Scalable discovery**: The CLI registry enumerates every visualization using metadata, enabling future automation like playbook generation or web front-ends.

## Playbook Automation Roadmap
The toolkit provides a comprehensive set of production-ready visualizations with advanced statistical analysis, export capabilities, and professional-quality outputs. Each visualization helps analyze uniqueness, compare cohorts, and surface hidden structures in categorical datasets.
