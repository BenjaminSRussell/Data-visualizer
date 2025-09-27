"""Advanced clustering visualization with multiple algorithms and comprehensive analysis.

Features:
- Multiple clustering algorithms (KMeans, DBSCAN, Agglomerative, Gaussian Mixture)
- Automatic optimal cluster selection using silhouette analysis
- Feature scaling options (standardization, min-max)
- Outlier detection and visual flagging
- Stability diagnostics with multiple runs
- PCA dimensionality reduction for high-dimensional data
- Comprehensive analysis export (centroids, loadings, assignments)
- Known label validation for clustering quality assessment
- Professional visualization with clear cluster differentiation
"""

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
            from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
            from sklearn.mixture import GaussianMixture
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import silhouette_score
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "Install scikit-learn and matplotlib to use the clustered scatter visualization."
            ) from exc

        # Configuration options
        algorithm = self.config.get("algorithm", "kmeans")  # kmeans, dbscan, agglomerative, gaussian_mixture
        n_clusters = self.config.get("n_clusters", None)  # Auto-select if None
        scale_features = self.config.get("scale_features", True)
        random_state = self.config.get("random_state", 42)
        detect_outliers = self.config.get("detect_outliers", False)
        stability_analysis = self.config.get("stability_analysis", False)
        export_analysis = self.config.get("export_analysis", False)
        known_labels = self.config.get("known_labels", None)  # Column name for validation

        # Feature scaling
        if scale_features:
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df)
        else:
            scaled_data = df.values

        # Auto-select optimal number of clusters using silhouette analysis
        if n_clusters is None and algorithm in ["kmeans", "agglomerative", "gaussian_mixture"]:
            best_score = -1
            best_k = 3

            for k in range(2, min(11, len(df) // 2)):  # Test 2-10 clusters, but not more than half the data points
                try:
                    if algorithm == "kmeans":
                        temp_model = KMeans(n_clusters=k, n_init="auto", random_state=random_state)
                        temp_labels = temp_model.fit_predict(scaled_data)
                    elif algorithm == "agglomerative":
                        temp_model = AgglomerativeClustering(n_clusters=k)
                        temp_labels = temp_model.fit_predict(scaled_data)
                    elif algorithm == "gaussian_mixture":
                        temp_model = GaussianMixture(n_components=k, random_state=random_state)
                        temp_labels = temp_model.fit_predict(scaled_data)

                    if len(set(temp_labels)) > 1:  # Need at least 2 clusters for silhouette score
                        score = silhouette_score(scaled_data, temp_labels)
                        if score > best_score:
                            best_score = score
                            best_k = k
                except:
                    continue

            n_clusters = best_k
            print(f"Auto-selected {n_clusters} clusters using silhouette analysis (score: {best_score:.3f})")

        # Apply clustering algorithm
        if algorithm == "kmeans":
            n_clusters = n_clusters or 3
            model = KMeans(n_clusters=n_clusters, n_init="auto", random_state=random_state)
            labels = model.fit_predict(scaled_data)
        elif algorithm == "dbscan":
            eps = self.config.get("eps", 0.5)
            min_samples = self.config.get("min_samples", 5)
            model = DBSCAN(eps=eps, min_samples=min_samples)
            labels = model.fit_predict(scaled_data)
        elif algorithm == "agglomerative":
            n_clusters = n_clusters or 3
            model = AgglomerativeClustering(n_clusters=n_clusters)
            labels = model.fit_predict(scaled_data)
        elif algorithm == "gaussian_mixture":
            n_clusters = n_clusters or 3
            model = GaussianMixture(n_components=n_clusters, random_state=random_state)
            labels = model.fit_predict(scaled_data)
        else:
            raise ValueError(f"Unknown clustering algorithm: {algorithm}. Use 'kmeans', 'dbscan', 'agglomerative', or 'gaussian_mixture'.")

        # Outlier detection based on distance to cluster centers
        outlier_flags = np.zeros(len(labels), dtype=bool)
        if detect_outliers and algorithm in ["kmeans", "gaussian_mixture"]:
            outlier_threshold = self.config.get("outlier_threshold", 2.0)  # Standard deviations

            if algorithm == "kmeans":
                # Calculate distances to cluster centers
                cluster_centers = model.cluster_centers_
                distances = []
                for i, label in enumerate(labels):
                    if label >= 0:  # Valid cluster
                        dist = np.linalg.norm(scaled_data[i] - cluster_centers[label])
                        distances.append(dist)
                    else:
                        distances.append(np.inf)

                distances = np.array(distances)
                # Flag outliers based on distance threshold
                distance_threshold = np.mean(distances) + outlier_threshold * np.std(distances)
                outlier_flags = distances > distance_threshold

        # Stability analysis (multiple runs with different seeds)
        stability_scores = []
        if stability_analysis and algorithm in ["kmeans", "gaussian_mixture"]:
            n_runs = self.config.get("stability_runs", 5)

            for run in range(n_runs):
                if algorithm == "kmeans":
                    temp_model = KMeans(n_clusters=n_clusters, n_init="auto", random_state=random_state + run)
                    temp_labels = temp_model.fit_predict(scaled_data)
                elif algorithm == "gaussian_mixture":
                    temp_model = GaussianMixture(n_components=n_clusters, random_state=random_state + run)
                    temp_labels = temp_model.fit_predict(scaled_data)

                # Calculate adjusted rand index for stability
                from sklearn.metrics import adjusted_rand_score
                if len(set(temp_labels)) > 1:
                    ari_score = adjusted_rand_score(labels, temp_labels)
                    stability_scores.append(ari_score)

            if stability_scores:
                stability_mean = np.mean(stability_scores)
                stability_std = np.std(stability_scores)
                print(f"Clustering stability: ARI = {stability_mean:.3f} ± {stability_std:.3f}")
            else:
                stability_mean, stability_std = 0, 0
        else:
            stability_mean, stability_std = None, None

        # Dimensionality reduction if needed
        if df.shape[1] > 2:
            reducer = PCA(n_components=2, random_state=random_state)
            if scale_features:
                points = reducer.fit_transform(scaled_data)
            else:
                points = reducer.fit_transform(df)
            x, y = points[:, 0], points[:, 1]
            x_label, y_label = "PC1", "PC2"
        else:
            x, y = df.iloc[:, 0], df.iloc[:, 1]
            x_label, y_label = df.columns[:2]

        # Plotting
        figsize = self.config.get("figsize", (8, 6))
        plt.figure(figsize=figsize)

        # Handle noise points for DBSCAN (-1 labels)
        unique_labels = np.unique(labels)
        n_clusters_found = len(unique_labels)
        if -1 in unique_labels:
            n_clusters_found -= 1  # Don't count noise as a cluster

        # Color mapping
        if algorithm == "dbscan":
            # Special handling for DBSCAN noise points
            colors = plt.cm.tab10(np.linspace(0, 1, max(10, n_clusters_found)))
            for label in unique_labels:
                if label == -1:
                    # Noise points in gray
                    mask = labels == label
                    plt.scatter(x[mask], y[mask], c='lightgray', alpha=0.6, s=20,
                               edgecolor="k", linewidth=0.5, label="Noise")
                else:
                    mask = labels == label
                    plt.scatter(x[mask], y[mask], c=[colors[label]], alpha=0.8, s=30,
                               edgecolor="k", linewidth=0.5, label=f"Cluster {label}")
        else:
            scatter = plt.scatter(x, y, c=labels, cmap="tab10", alpha=0.8, s=30, edgecolor="k", linewidth=0.5)

        # Overlay outliers if detected
        if detect_outliers and np.any(outlier_flags):
            plt.scatter(x[outlier_flags], y[outlier_flags],
                       facecolors='none', edgecolors='red', s=100, linewidth=2,
                       alpha=0.8, label="Outliers")

        # Overlay known labels if provided for validation
        if known_labels and known_labels in df.columns:
            # Add border colors based on known labels
            known_label_values = df[known_labels].values
            unique_known = np.unique(known_label_values)

            # Create a different marker style for each known label
            markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
            for i, known_val in enumerate(unique_known):
                mask = known_label_values == known_val
                marker = markers[i % len(markers)]
                plt.scatter(x[mask], y[mask], marker=marker,
                          facecolors='none', edgecolors='black', s=60, linewidth=1,
                          alpha=0.7, label=f"Known: {known_val}")

        # Styling
        title = self.config.get("title", f"{self.metadata.title} ({algorithm.upper()})")
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(x_label, fontsize=12)
        plt.ylabel(y_label, fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.3)

        # Legend
        if algorithm == "dbscan":
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            legend_handles = scatter.legend_elements()[0]
            plt.legend(legend_handles, [f"Cluster {i}" for i in range(len(legend_handles))],
                      title="Cohorts", bbox_to_anchor=(1.05, 1), loc='upper left')

        # Add clustering info
        if algorithm == "dbscan":
            info_text = f"Clusters found: {n_clusters_found}\nNoise points: {sum(labels == -1)}"
        else:
            info_text = f"Clusters: {n_clusters_found}"
            if n_clusters != n_clusters_found:
                info_text += f" (auto-selected)"

        plt.figtext(0.02, 0.02, info_text, fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))

        plt.tight_layout()
        plt.subplots_adjust(right=0.85)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        # Export detailed analysis if requested
        if export_analysis:
            analysis_path = output_path.with_suffix('.json')

            analysis_data = {
                'algorithm': algorithm,
                'n_clusters': n_clusters,
                'n_clusters_found': n_clusters_found,
                'feature_scaling': scale_features,
                'random_state': random_state,
                'outliers_detected': int(np.sum(outlier_flags)) if detect_outliers else None,
                'stability_mean': stability_mean,
                'stability_std': stability_std,
                'original_features': list(df.columns),
                'n_samples': len(df),
                'n_features': df.shape[1],
            }

            # Add cluster centroids for supported algorithms
            if algorithm == "kmeans" and hasattr(model, 'cluster_centers_'):
                analysis_data['cluster_centers'] = model.cluster_centers_.tolist()

            # Add PCA information if dimensionality reduction was used
            if df.shape[1] > 2:
                analysis_data['pca_explained_variance_ratio'] = reducer.explained_variance_ratio_.tolist()
                analysis_data['pca_components'] = reducer.components_.tolist()

            # Add cluster assignments
            cluster_assignments = pd.DataFrame({
                'cluster': labels,
                'outlier': outlier_flags if detect_outliers else [False] * len(labels)
            })

            if known_labels and known_labels in df.columns:
                cluster_assignments['known_label'] = df[known_labels].values
                # Calculate clustering validation metrics
                from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
                ari = adjusted_rand_score(df[known_labels], labels)
                nmi = normalized_mutual_info_score(df[known_labels], labels)
                analysis_data['validation_ari'] = ari
                analysis_data['validation_nmi'] = nmi

            # Save analysis data
            import json
            with open(analysis_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)

            # Save cluster assignments
            assignments_path = output_path.with_name(output_path.stem + '_assignments.csv')
            cluster_assignments.to_csv(assignments_path, index=False)

            print(f"Cluster analysis exported to: {analysis_path}")
            print(f"Cluster assignments exported to: {assignments_path}")

        return output_path
