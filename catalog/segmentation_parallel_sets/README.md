# Parallel Sets (Segmentation Flow)

**Use case**: Visualize how cohorts flow across categorical stages to reveal conversion patterns, funnel behavior, and customer journey insights.

**Perfect for**: Customer acquisition analysis, conversion funnel optimization, user journey mapping, A/B test flow comparison, and lifecycle progression studies.

## Quick Run

```bash
python -m data_visualizer.cli datasets/segmentation_parallel_sets/sample_funnel.csv segmentation_parallel_sets --output-dir outputs/segmentation_parallel_sets
```

## Dataset Structure

The sample dataset (`sample_funnel.csv`) demonstrates user flow through acquisition to retention:

- **acquisition_channel**: How users were acquired (Organic, Paid Social, Email, etc.)
- **plan_type**: Plan tier they selected (Free, Premium, Enterprise)
- **retention_status**: Final retention outcome (Active, Churned)
- **user_count**: Number of users following this path (numeric weight)

## Interpretation Guidelines

**What to look for:**
- **Ribbon thickness**: Proportional to flow volume between stages
- **Flow splits**: How cohorts divide at each decision point
- **Conversion patterns**: Which paths lead to desired outcomes
- **Drop-off points**: Where significant user loss occurs

**Common insights:**
- Channel effectiveness across different user segments
- Plan conversion rates by acquisition source
- Retention patterns by customer type
- Bottlenecks in conversion funnels

## Configuration Options

Key parameters for customization:

- `color_scheme`: "plotly", "viridis", "plasma", "rainbow"
- `width`/`height`: Output dimensions (default: 1000x600)
- `show_counts`: Display flow volumes in hover information
- `title`: Override default title

## Ten Forward-Looking TODOs

1. **Path highlighting**: Click to trace specific customer journey paths
2. **Conversion rate overlays**: Display percentages at each transition point
3. **Comparative analysis**: Side-by-side flows for different time periods or segments
4. **Drop-off analysis**: Automated identification of critical loss points
5. **Cohort filtering**: Interactive filtering by specific attributes or outcomes
6. **Statistical significance**: Highlight flows with significant conversion differences
7. **Journey optimization**: AI-powered recommendations for improving conversion rates
8. **Time dimension**: Animate flows showing progression over time periods
9. **Custom metrics**: Support for revenue, LTV, or other business metrics as weights
10. **Export capabilities**: Generate funnel reports and conversion tables

## Potential Pitfalls

- **Stage ordering**: Ensure stages represent logical progression in time or process
- **Data completeness**: Missing stages in customer journeys may skew analysis
- **Scale differences**: Large volume differences may make small flows invisible
- **Interpretation complexity**: Too many stages or categories create cluttered diagrams
- **Causation assumptions**: Flow patterns don't necessarily indicate causal relationships
- **Temporal considerations**: Ensure data represents consistent time periods for fair comparison