# Clustered Scatter Relationship Build

Workflow wrapper for the `relationship_cluster_scatter` program to surface unique cohorts.

## Quick Run
- Install dependencies: `pip install -r requirements.txt`.
- Set `PYTHONPATH=src`.
- Execute: `python -m data_visualizer.cli datasets/relationship_cluster_scatter/sample_customer_segments.csv relationship_cluster_scatter --output-dir outputs/relationship_cluster_scatter`.
- Optional: pass `--config catalog/relationship_cluster_scatter/kmeans_config.json` for consistent clustering.
- Output: PNG chart at `outputs/relationship_cluster_scatter/relationship_cluster_scatter.png`.

## Dataset
- File: `datasets/relationship_cluster_scatter/sample_customer_segments.csv`
- Schema: `customer_id`, `avg_order_value`, `visits_per_month`, `tenure_months`
- Purpose: Highlights how purchasing behavior and engagement define distinct cohorts.

## Interpretation Tips
- Color grouping indicates cluster membership; inspect centroids to describe each persona.
- Points far from any cluster may signal data quality issues or emerging behaviors.

## TODOs (10)
1. Add support for alternative clustering algorithms (DBSCAN, Agglomerative, Gaussian Mixture).
2. Provide feature scaling options (standardization, min-max) controlled via config.
3. Auto-select optimal `n_clusters` using silhouette or elbow heuristics when not specified.
4. Export cluster centroids and PCA component loadings for deeper analysis.
5. Enable interactive tooltips listing customer IDs and feature values.
6. Allow 3D scatter or pair plot outputs when two components are insufficient.
7. Flag outliers beyond a configurable distance threshold and label them on the chart.
8. Offer cluster stability diagnostics (e.g., repeated runs) to build trust in segmentation.
9. Log model parameters and random seeds for reproducibility.
10. Integrate optional supervised overlay (e.g., color by known label) to validate clustering quality.

## Potential Pitfalls
- High-dimensional datasets may lose nuance after PCA; consider domain-driven feature selection.
- KMeans assumes spherical clusters—if shapes are irregular, pivot to DBSCAN-style density methods.
