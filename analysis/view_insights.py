"""
View Analysis Insights - Interactive Report Viewer
"""

import json
import sys
from pathlib import Path
from typing import Dict


def load_results(results_dir: str = 'analysis/results'):
    results_path = Path(results_dir)

    try:
        with open(results_path / 'analysis_results.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Results not found in {results_dir}")
        print("Run the master pipeline first:")
        print("  python3 analysis/pipeline/master_pipeline.py Site.jsonl analysis/results")
        sys.exit(1)


def view_overview(results: Dict):
    meta = results.get('metadata', {})
    insights = results.get('insights', {})

    print("Analysis overview")
    print(f"Dataset: {meta.get('input_file', 'N/A')}")
    print(f"Total URLs: {meta.get('total_urls', 0):,}")
    print(f"Analysis Time: {meta.get('total_execution_time', 0):.2f}s")

    if 'scores' in insights:
        print("Scores:")
        for score_name, score_value in insights['scores'].items():
            print(f"{score_name.replace('_', ' ').title()}: {score_value:.1f}/100")


def view_statistical_insights(results: Dict):
    stats = results.get('statistical', {})

    print("Statistical analysis")

    if 'summary_stats' in stats:
        summary = stats['summary_stats']
        print(f"Depth: avg={summary.get('depth_mean', 0):.2f}, range={summary.get('depth_min', 0):.0f}-{summary.get('depth_max', 0):.0f}")
        print(f"Path Length: avg={summary.get('path_length_mean', 0):.2f} chars")
        print(f"Outbound Links: avg={summary.get('outbound_links_mean', 0):.2f}")

    if 'url_health' in stats:
        health = stats['url_health']
        grade = health.get('health_grade', 'N/A')
        print(f"URL Health: {health.get('overall_health', 0):.1f}/100 (Grade: {grade})")

    if 'correlations' in stats:
        print("Significant correlations:")
        for name, corr in stats['correlations'].items():
            if corr.get('significant'):
                direction = "positive" if corr['correlation'] > 0 else "negative"
                print(f"{name.replace('_', ' ').title()} ({direction}, r={corr['correlation']:.3f})")


def view_semantic_insights(results: Dict):
    semantic = results.get('semantic_path', {})

    print("Semantic analysis")

    if 'vocabulary' in semantic:
        vocab = semantic['vocabulary']
        print(f"Total Tokens: {vocab.get('total_tokens', 0):,}")
        print(f"Unique Tokens: {vocab.get('unique_tokens', 0):,}")
        print(f"Diversity: {vocab.get('vocabulary_diversity', 'N/A').upper()}")

        if 'top_tokens' in vocab:
            print("Top 10 keywords:")
            top_tokens = list(vocab['top_tokens'].items())[:10]
            for i, (token, count) in enumerate(top_tokens, 1):
                print(f"{i}. {token}: {count}")

    if 'semantic_categories' in semantic and 'dominant_category' in semantic['semantic_categories']:
        dom = semantic['semantic_categories']['dominant_category']
        print(f"Dominant category: {dom.get('name', 'Unknown').upper()} ({dom.get('count', 0)} pages)")

    if 'content_type_prediction' in semantic:
        content_types = semantic['content_type_prediction']
        sorted_types = sorted(content_types.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        print("Content type predictions:")
        for ctype, data in sorted_types:
            print(f"{ctype}: {data['percentage']:.1f}% ({data['count']:,})")


def view_network_insights(results: Dict):
    network = results.get('network', {})

    print("Network analysis")

    if 'network_metrics' in network:
        metrics = network['network_metrics']
        print(f"Nodes: {metrics.get('nodes', 0):,}")
        print(f"Edges: {metrics.get('edges', 0):,}")
        print(f"Density: {metrics.get('density', 0):.6f}")
        print(f"Average Degree: {metrics.get('average_degree', 0):.2f}")

    if 'centrality' in network and network['centrality'].get('top_by_degree'):
        print("Top pages by connections:")
        for i, item in enumerate(network['centrality']['top_by_degree'][:3], 1):
            print(f"{i}. {item['url'][:60]} ({item['degree']} connections)")

    if 'community_detection' in network:
        communities = network['community_detection']
        print(f"Total communities: {communities.get('total_communities', 0)}")
        if communities.get('top_communities'):
            top = communities['top_communities'][0]
            print(f"Largest: {top['community']} ({top['percentage']:.1f}%)")


def view_pathway_insights(results: Dict):
    pathway = results.get('pathway', {})

    print("Pathway analysis")

    if 'architecture' in pathway:
        arch = pathway['architecture']
        print(f"Type: {arch.get('architecture_type', 'unknown').upper()}")
        print(f"Max Depth: {arch.get('max_depth', 0)} levels")
        print(f"Avg Children per Parent: {arch.get('avg_children_per_parent', 0):.2f}")
        print(f"Orphan Pages: {arch.get('orphan_pages', 0)}")

    if 'dead_ends' in pathway:
        dead = pathway['dead_ends']
        print(f"Dead-End Pages: {dead.get('count', 0):,} ({dead.get('percentage', 0):.1f}%)")


def view_alerts_recommendations(results: Dict):
    insights = results.get('insights', {})

    if insights.get('alerts'):
        print("Alerts")
        for i, alert in enumerate(insights['alerts'], 1):
            print(f"{i}. {alert}")

    if insights.get('recommendations'):
        print("Recommendations")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"{i}. {rec}")


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'analysis/results'
    results = load_results(results_dir)

    print("URL analysis insights viewer")

    view_overview(results)
    view_statistical_insights(results)
    view_semantic_insights(results)
    view_network_insights(results)
    view_pathway_insights(results)
    view_alerts_recommendations(results)

    print(f"Full results available in: {results_dir}")


if __name__ == '__main__':
    main()
