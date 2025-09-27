# This Needs To Be Fixed

## Critical
- **Missing SciPy dependency**: `ViolinPlot` pulls in `scipy.stats` at runtime (`src/data_visualizer/visualizations/distributions/violin_plot.py:103-199`), yet `requirements.txt` does not list SciPy. Fresh installs fail during rendering, so the dependency must be declared and documented.

## High Priority
- **CLI lacks upfront schema validation**: The CLI loads CSVs and invokes visualizations without checking required columns or types (`src/data_visualizer/cli.py:53-75`). Users hit visualization-specific tracebacks instead of actionable errors.
- **Line chart is limited to a single metric**: `LineChart.render` only plots the first value column and ignores any additional metrics (`src/data_visualizer/visualizations/trends/line_chart.py:59-65`). Multi-series support and smoothing remain unmet roadmap items.
- **Grouped bar backlog is out of sync with code**: Aggregation, error bars, and sorting already exist (`src/data_visualizer/visualizations/comparisons/grouped_bar.py:112-150`), but the published TODOs still list them as pending, obscuring the real gaps (normalization, stacked variants, drill-down).

## Medium Priority
- **Violin plot needs raw-point overlays and advanced diagnostics**: Current output cannot highlight small-sample distributions or report modality/tail findings (`src/data_visualizer/visualizations/distributions/violin_plot.py:130-198`).
- **Documentation drift**: `docs/todo_visualizations.md` continues to advertise features that now exist for grouped bars and violin plots, making it harder for contributors to spot the remaining work (`docs/todo_visualizations.md`).
