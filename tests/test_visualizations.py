from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data_visualizer.visualizations.comparisons.grouped_bar import GroupedBarChart
from data_visualizer.visualizations.comparisons.heatmap import ComparisonHeatmap
from data_visualizer.visualizations.comparisons.treemap import HierarchyTreemap
from data_visualizer.visualizations.distributions.violin_plot import ViolinPlot
from data_visualizer.visualizations.relationships.cluster_scatter import ClusterScatter
from data_visualizer.visualizations.relationships.parallel_sets import SegmentationParallelSets
from data_visualizer.visualizations.trends.line_chart import LineChart

REPO_ROOT = Path(__file__).resolve().parents[1]
WORDS_CSV = REPO_ROOT / "datasets" / "sample_words.csv"


def test_line_chart_runs(tmp_path):
    pytest.importorskip("matplotlib")
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=6, freq="MS"),
            "value": [120, 135, 128, 142, 150, 160],
        }
    )
    output_path = LineChart().run(df, tmp_path)
    assert output_path.exists()


def test_grouped_bar_runs(tmp_path):
    pytest.importorskip("seaborn")
    df = pd.DataFrame(
        {
            "region": ["North", "North", "South", "South"],
            "channel": ["Online", "Retail", "Online", "Retail"],
            "revenue": [120000, 95000, 102000, 88000],
        }
    )
    output_path = GroupedBarChart().run(df, tmp_path)
    assert output_path.exists()


def test_violin_plot_runs(tmp_path):
    pytest.importorskip("seaborn")
    df = pd.DataFrame(
        {
            "segment": ["North", "North", "South", "South", "East", "East"],
            "score": [65, 72, 55, 58, 45, 52],
        }
    )
    output_path = ViolinPlot().run(df, tmp_path)
    assert output_path.exists()


def test_cluster_scatter_runs(tmp_path):
    pytest.importorskip("sklearn")
    pytest.importorskip("matplotlib")
    df = pd.DataFrame(
        {
            "avg_order_value": [45.3, 120.5, 78.1, 30.2, 210.7, 66.4],
            "visits_per_month": [12, 4, 9, 15, 2, 8],
            "tenure_months": [6, 24, 14, 3, 36, 12],
        }
    )
    output_path = ClusterScatter().run(df, tmp_path)
    assert output_path.exists()


def test_comparison_heatmap_runs(tmp_path):
    pytest.importorskip("seaborn")
    df = pd.DataFrame(
        {
            "region": ["North", "North", "South", "South", "East", "East"],
            "product": ["A", "B", "A", "B", "A", "B"],
            "sales": [1250, 850, 980, 1100, 1400, 700],
        }
    )
    output_path = ComparisonHeatmap().run(df, tmp_path)
    assert output_path.exists()


def test_hierarchy_treemap_runs(tmp_path):
    pytest.importorskip("plotly")
    df = pd.DataFrame(
        {
            "region": ["North", "North", "South", "South"],
            "country": ["USA", "Canada", "USA", "Mexico"],
            "population": [8400000, 2700000, 4000000, 9200000],
        }
    )
    output_path = HierarchyTreemap().run(df, tmp_path)
    assert output_path.exists()


def test_parallel_sets_runs(tmp_path):
    pytest.importorskip("plotly")
    df = pd.DataFrame(
        {
            "channel": ["Organic", "Organic", "Paid", "Paid"],
            "plan": ["Free", "Premium", "Free", "Premium"],
            "status": ["Active", "Active", "Churned", "Active"],
            "count": [800, 350, 400, 180],
        }
    )
    output_path = SegmentationParallelSets().run(df, tmp_path)
    assert output_path.exists()


def test_word_dataset_triggers_validation(tmp_path):
    data = pd.read_csv(WORDS_CSV)

    with pytest.raises(ValueError):
        LineChart().run(data, tmp_path)

    with pytest.raises(ValueError):
        ClusterScatter().prepare_data(data)
