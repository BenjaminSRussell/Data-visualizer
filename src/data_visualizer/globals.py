"""Global configuration and color theory for consistent visual design.

This module centralizes color palettes and visual constants to ensure
coherent aesthetics across all visualization types while supporting
accessibility and psychological impact of color choices.
"""

from typing import Dict, List, Tuple
import datetime

# Output Configuration
OUTPUT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
OUTPUT_BASE_DIR = "outputs"

def get_timestamped_filename(base_name: str, extension: str = "png") -> str:
    """Generate unique filenames to prevent overwrites and track creation time."""
    timestamp = datetime.datetime.now().strftime(OUTPUT_TIMESTAMP_FORMAT)
    return f"{base_name}_{timestamp}.{extension}"

# Color Theory & Psychology
"""
Color theory considerations for data visualization:

PRIMARY PALETTES:
- Qualitative: Distinct hues for categorical data (max 8-10 colors before confusion)
- Sequential: Single hue progression for ordered data (light to dark intensity)
- Diverging: Two-hue spectrum for data with meaningful center point (e.g., +/- values)

PSYCHOLOGICAL IMPACT:
- Blue: Trust, stability, professionalism (safe choice for business data)
- Green: Growth, positive trends, success metrics
- Red: Urgency, decline, errors (use sparingly, accessibility concerns)
- Orange: Energy, attention-grabbing (good for highlights)
- Purple: Creativity, premium segments
- Gray: Neutral, supporting information

ACCESSIBILITY PRINCIPLES:
- ColorBrewer schemes tested for colorblind accessibility
- Minimum 3:1 contrast ratio for text/background
- Never rely solely on color to convey information
- Provide texture/pattern alternatives when possible
"""

# Core Color Palettes
QUALITATIVE_PALETTES = {
    "corporate_safe": [
        "#2E86AB",  # Professional blue - trustworthy, calming
        "#A23B72",  # Confident magenta - attention without aggression
        "#F18F01",  # Warm orange - energetic, optimistic
        "#C73E1D",  # Strategic red - urgency, importance
        "#7209B7",  # Creative purple - innovation, premium
        "#588157",  # Growth green - success, stability
        "#F4A261",  # Friendly amber - approachable, warm
        "#264653"   # Grounded teal - reliability, depth
    ],

    "vibrant_accessible": [
        "#FF6B6B",  # Coral red - warm, engaging
        "#4ECDC4",  # Mint teal - fresh, modern
        "#45B7D1",  # Sky blue - open, trustworthy
        "#96CEB4",  # Sage green - calm, natural
        "#FECA57",  # Sunny yellow - optimistic, energetic
        "#FF9FF3",  # Soft pink - approachable, creative
        "#54A0FF",  # Electric blue - dynamic, tech-forward
        "#5F27CD"   # Rich purple - sophisticated, unique
    ],

    "earth_tones": [
        "#8D5524",  # Rich brown - grounded, traditional
        "#C4A484",  # Warm beige - neutral, sophisticated
        "#A4AC86",  # Olive green - natural, organic
        "#656D4A",  # Forest green - stable, enduring
        "#414833",  # Deep sage - calm, meditative
        "#333D29",  # Dark moss - mysterious, depth
        "#FEFAE0",  # Cream - clean, spacious
        "#DDA15E"   # Golden ochre - warm, inviting
    ]
}

SEQUENTIAL_PALETTES = {
    "blue_progression": [
        "#F7FBFF", "#DEEBF7", "#C6DBEF", "#9ECAE1",
        "#6BAED6", "#4292C6", "#2171B5", "#08519C", "#08306B"
    ],
    "warm_gradient": [
        "#FFF5F0", "#FEE0D2", "#FCBBA1", "#FC9272",
        "#FB6A4A", "#EF3B2C", "#CB181D", "#A50F15", "#67000D"
    ],
    "green_growth": [
        "#F7FCF5", "#E5F5E0", "#C7E9C0", "#A1D99B",
        "#74C476", "#41AB5D", "#238B45", "#006D2C", "#00441B"
    ]
}

DIVERGING_PALETTES = {
    "red_blue_classic": [
        "#67001F", "#B2182B", "#D6604D", "#F4A582", "#FDDBC7",
        "#F7F7F7", "#D1E5F0", "#92C5DE", "#4393C3", "#2166AC", "#053061"
    ],
    "purple_orange": [
        "#7F3B08", "#B35806", "#E08214", "#FDB863", "#FEE0B6",
        "#F7F7F7", "#D8DAEB", "#B2ABD2", "#8073AC", "#542788", "#2D004B"
    ]
}

# Specialized Color Functions
def get_palette_for_categories(n_categories: int, style: str = "corporate_safe") -> List[str]:
    """Smart palette selection based on category count and visualization context.

    Future: Could integrate with brand guidelines, user preferences, or
    automatic accessibility testing for optimal color selection.
    """
    if n_categories <= 2:
        return QUALITATIVE_PALETTES[style][:2]
    elif n_categories <= 8:
        return QUALITATIVE_PALETTES[style][:n_categories]
    else:
        # For many categories, cycle through palette with alpha variations
        base_colors = QUALITATIVE_PALETTES[style]
        extended = []
        for i in range(n_categories):
            color_idx = i % len(base_colors)
            alpha_level = 1.0 - (i // len(base_colors)) * 0.3
            extended.append(base_colors[color_idx])
        return extended

def get_sequential_colors(n_steps: int, palette: str = "blue_progression") -> List[str]:
    """Generate sequential color progression for ordered data visualization.

    Useful for heatmaps, choropleth maps, or any data with natural ordering.
    Future: Dynamic palette generation based on data distribution characteristics.
    """
    colors = SEQUENTIAL_PALETTES[palette]
    if n_steps <= len(colors):
        # Evenly distribute colors across the available range
        step_size = len(colors) // n_steps
        return [colors[i * step_size] for i in range(n_steps)]
    else:
        # Interpolate additional colors if needed
        return colors  # Simplified for now

# Chart-Specific Defaults
CHART_DEFAULTS = {
    "grouped_bar": {
        "palette": "corporate_safe",
        "background": "#FFFFFF",
        "grid_color": "#E5E5E5",
        "text_color": "#333333",
        "accent_color": "#2E86AB"
    },
    "violin_plot": {
        "palette": "vibrant_accessible",
        "background": "#FAFAFA",
        "statistical_color": "#FF6B6B",  # For statistical annotations
        "confidence_color": "#45B7D1"   # For confidence intervals
    },
    "scatter_plot": {
        "palette": "earth_tones",
        "background": "#FFFFFF",
        "cluster_alpha": 0.7,
        "outlier_color": "#C73E1D"
    },
    "line_chart": {
        "primary_color": "#2E86AB",
        "secondary_color": "#A23B72",
        "anomaly_color": "#C73E1D",
        "confidence_fill": "#E3F2FD"
    }
}

# Accessibility Helpers
COLORBLIND_SAFE_PAIRS = [
    ("#1f77b4", "#ff7f0e"),  # Blue-Orange (most accessible)
    ("#2ca02c", "#d62728"),  # Green-Red (avoid unless necessary)
    ("#9467bd", "#8c564b"),  # Purple-Brown
    ("#e377c2", "#7f7f7f")   # Pink-Gray
]

def validate_accessibility(colors: List[str]) -> Dict[str, bool]:
    """Basic accessibility validation for color combinations.

    Future: Integration with full WCAG compliance testing, automated
    contrast ratio calculations, and colorblind simulation.
    """
    return {
        "sufficient_contrast": len(colors) <= 8,  # Simplified check
        "colorblind_safe": True,  # Would implement actual checking
        "distinct_hues": len(set(colors)) == len(colors)
    }


# Centralized schema and configuration options for each visualization
SCHEMA_REQUIREMENTS = {
    "trend_line_chart": {
        "min_columns": 2,
        "description": "Requires at least 2 columns (x-axis, y-axis)",
        "example_columns": ["date", "value"],
        "column_types": {"numeric_columns": 1},
        "config_options": {
            "value_columns": {"type": "multiselect", "label": "Value Columns", "options": "data_columns"},
            "rolling_window": {"type": "integer", "label": "Rolling Average Window", "default": 1},
            "anomaly_detection": {"type": "boolean", "label": "Detect Anomalies", "default": False},
            "export_trends": {"type": "boolean", "label": "Export Trend Data", "default": False},
            "palette": {"type": "dropdown", "label": "Color Palette", "options": list(QUALITATIVE_PALETTES.keys()), "default": "corporate_safe"}
        }
    },
    "comparison_grouped_bar": {
        "min_columns": 3,
        "description": "Requires exactly 3 columns (group, category, value)",
        "example_columns": ["region", "product", "sales"],
        "column_types": {"numeric_columns": 1},
        "config_options": {
            "aggregation": {"type": "dropdown", "label": "Aggregation", "options": ["mean", "sum", "median", "count"], "default": "sum"},
            "chart_type": {"type": "dropdown", "label": "Chart Type", "options": ["grouped", "stacked", "100% stacked"], "default": "grouped"},
            "normalize": {"type": "boolean", "label": "Normalize Data", "default": False},
            "show_error_bars": {"type": "boolean", "label": "Show Error Bars", "default": False},
            "palette": {"type": "dropdown", "label": "Color Palette", "options": list(QUALITATIVE_PALETTES.keys()), "default": "corporate_safe"}
        }
    },
    "distribution_violin": {
        "min_columns": 2,
        "description": "Requires at least 2 columns (category, numeric_value)",
        "example_columns": ["segment", "score"],
        "column_types": {"numeric_columns": 1},
        "config_options": {
            "swarm_overlay": {"type": "boolean", "label": "Overlay Swarm Plot", "default": True},
            "log_scale": {"type": "boolean", "label": "Use Log Scale", "default": False},
            "outlier_detection": {"type": "boolean", "label": "Detect Outliers", "default": True},
            "palette": {"type": "dropdown", "label": "Color Palette", "options": list(QUALITATIVE_PALETTES.keys()), "default": "vibrant_accessible"}
        }
    },
    "relationship_cluster_scatter": {
        "min_columns": 2,
        "description": "Requires at least 2 numeric columns for clustering",
        "example_columns": ["feature1", "feature2", "feature3"],
        "column_types": {"numeric_columns": 2},
        "config_options": {
            "algorithm": {"type": "dropdown", "label": "Clustering Algorithm", "options": ["KMeans", "DBSCAN", "AgglomerativeClustering"], "default": "KMeans"},
            "n_clusters": {"type": "integer", "label": "Number of Clusters", "default": 3},
            "detect_outliers": {"type": "boolean", "label": "Detect Outliers", "default": True},
            "palette": {"type": "dropdown", "label": "Color Palette", "options": list(QUALITATIVE_PALETTES.keys()), "default": "earth_tones"}
        }
    },
    "comparison_heatmap": {
        "min_columns": 3,
        "description": "Requires 3 columns (row_category, column_category, value)",
        "example_columns": ["region", "product", "sales"],
        "column_types": {"numeric_columns": 1},
        "config_options": {
            "aggregation": {"type": "dropdown", "label": "Aggregation", "options": ["mean", "sum"], "default": "mean"},
            "cluster_rows": {"type": "boolean", "label": "Cluster Rows", "default": False},
            "palette": {"type": "dropdown", "label": "Color Palette", "options": list(SEQUENTIAL_PALETTES.keys()), "default": "blue_progression"}
        }
    },
    "hierarchy_treemap": {
        "min_columns": 2,
        "description": "Requires at least 2 columns (hierarchy + value)",
        "example_columns": ["region", "country", "city", "population"],
        "column_types": {"numeric_columns": 1},
        "config_options": {
            "threshold_filter": {"type": "float", "label": "Value Threshold", "default": 0.0},
            "palette": {"type": "dropdown", "label": "Color Palette", "options": list(SEQUENTIAL_PALETTES.keys()), "default": "green_growth"}
        }
    },
    "segmentation_parallel_sets": {
        "min_columns": 2,
        "description": "Requires at least 2 categorical columns for flow analysis",
        "example_columns": ["channel", "plan", "status", "count"],
        "column_types": {},
        "config_options": {
            "conversion_analysis": {"type": "boolean", "label": "Analyze Conversion", "default": False},
            "color_scheme": {"type": "dropdown", "label": "Color Scheme", "options": ["plotly3", "viridis", "cividis", "plasma"], "default": "plotly3"}
        }
    }
}