"""Scatter plot that highlights discovered clusters to differentiate cohorts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..base import Visualization, VisualizationMetadata


class ClusterScatter(Visualization):
    metadata = VisualizationMetadata(
        key="relationship_cluster_scatter",
        title="Clustered Scatter",
        insight_type="Relationship",
        description="Project observations into two dimensions and color-code discovered clusters to expose unique groupings.",
        example_url="https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_digits.html",
        tags=("relationship", "clustering", "sklearn"),
    )

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Input dataframe is empty; provide numerical features for clustering.")
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.shape[1] < 2:
            raise ValueError("Cluster scatter requires at least two numeric columns.")
        return numeric_df

    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        try:
            from matplotlib import pyplot as plt
            from sklearn.cluster import KMeans
            from sklearn.decomposition import PCA
        except ImportError as exc:
            raise RuntimeError(
                "Install scikit-learn and matplotlib to use the clustered scatter visualization."
            ) from exc

        n_clusters = self.config.get("n_clusters", 3)
        model = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
        labels = model.fit_predict(df)

        if df.shape[1] > 2:
            reducer = PCA(n_components=2, random_state=42)
            points = reducer.fit_transform(df)
            x, y = points[:, 0], points[:, 1]
            x_label, y_label = "PC1", "PC2"
        else:
            x, y = df.iloc[:, 0], df.iloc[:, 1]
            x_label, y_label = df.columns[:2]

        plt.figure(figsize=(6, 6))
        scatter = plt.scatter(x, y, c=labels, cmap="tab10", alpha=0.8, edgecolor="k")
        plt.title(self.metadata.title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.grid(True, linestyle="--", alpha=0.3)
        plt.tight_layout()
        legend_handles = scatter.legend_elements()[0]
        plt.legend(legend_handles, [f"Cluster {i}" for i in range(len(legend_handles))], title="Cohorts")
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path
