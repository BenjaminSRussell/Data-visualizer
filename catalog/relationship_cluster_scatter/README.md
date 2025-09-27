# Clustered Scatter Plot Visualization

## Quick Run
```bash
python -m data_visualizer.cli datasets/relationship_cluster_scatter/sample_customer_segments.csv relationship_cluster_scatter --output-dir outputs/relationship_cluster_scatter
```

## What This Visualization Does
The clustered scatter plot auto-discovers cohorts using PCA + clustering algorithms and color-codes them to reveal emergent clusters or borderline records. This visualization combines dimensionality reduction with unsupervised learning to identify natural groupings in multi-dimensional data that aren't obvious from individual variables.

## Dataset Requirements
**Expected columns**: Multiple numeric columns (3+ recommended)
- **Numeric features**: Continuous variables for analysis (e.g., age, income, engagement_score, purchase_amount)
- **Optional ID column**: Customer ID or record identifier for tracking
- **Optional label column**: Known categories for validation (will be compared against discovered clusters)

**Sample data format**:
```csv
customer_id,age,income,spending_score,loyalty_years
1,25,50000,75,2.5
2,45,80000,45,5.2
3,35,60000,85,3.1
```

## When to Use This Chart
- **Customer segmentation**: Discover natural customer groups based on behavior/demographics
- **Market research**: Identify distinct consumer segments in survey data
- **Anomaly detection**: Spot outliers or unusual patterns in multi-dimensional data
- **Product clustering**: Group products by similar characteristics or performance
- **Quality control**: Identify process variations or defect patterns

## Interpretation Notes
- **Point colors** = Discovered clusters (each color represents a distinct group)
- **Point positions** = Reduced 2D representation of multi-dimensional relationships
- **Cluster boundaries** = Natural groupings discovered by the algorithm
- **Outlier points** = Records that don't fit well into any cluster
- **Cluster centers** = Representative points for each discovered group

## Ten Enhancement TODOs

### Algorithm Improvements
1. **Multiple clustering algorithms**: Support KMeans, HDBSCAN, DBSCAN, Gaussian Mixture Models
2. **Optimal cluster detection**: Implement elbow method, silhouette analysis, gap statistic
3. **Feature selection**: Automatic feature importance and selection for better clustering
4. **Dimensionality reduction options**: Support t-SNE, UMAP alongside PCA

### Statistical Enhancements
5. **Cluster validation metrics**: Calculate and display silhouette scores, Calinski-Harabasz index
6. **Stability analysis**: Bootstrap clustering to assess cluster stability
7. **Feature contribution analysis**: Show which original features most influence each cluster
8. **Distance metrics**: Support different distance measures (euclidean, manhattan, cosine)

### Interactive Features
9. **Interactive exploration**: Click points to see original feature values, hover for details
10. **Cluster refinement**: Allow manual adjustment of cluster assignments and parameters

## Configuration Options
```json
{
  "clustering_algorithm": "kmeans",
  "n_clusters": "auto",
  "dimensionality_reduction": "pca",
  "scaling_method": "standard",
  "remove_outliers": true,
  "outlier_threshold": 0.05,
  "cluster_validation": true,
  "show_cluster_centers": true
}
```

## Related Visualizations
- **Parallel Coordinates**: When you want to see all dimensions simultaneously
- **Correlation Heatmap**: When focusing on feature relationships
- **3D Scatter Plot**: When three dimensions provide better separation
- **Hierarchical Clustering Dendrogram**: When exploring cluster hierarchies
