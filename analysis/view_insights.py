"""
View Analysis Insights - Interactive Report Viewer

Purpose: Display the most important and interesting insights from the analysis
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict


def load_results(results_dir: str = 'analysis/results'):
    """Load analysis results."""
    results_path = Path(results_dir)

    try:
        with open(results_path / 'analysis_results.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Results not found in {results_dir}")
        print("Run the master pipeline first:")
        print("  python3 analysis/pipeline/master_pipeline.py Site.jsonl analysis/results")
        sys.exit(1)


def print_header(title: str):
    """Print section header."""
    print("\n" + "="*80)
    print(title.center(80))
    print("="*80)


def print_section(title: str):
    """Print subsection header."""
    print(f"\n{title}")
    print("-" * 80)


def view_overview(results: Dict):
    """Display overview metrics."""
    print_header("📊 ANALYSIS OVERVIEW")

    meta = results.get('metadata', {})
    insights = results.get('insights', {})

    print(f"\n📁 Dataset: {meta.get('input_file', 'N/A')}")
    print(f"📅 Analyzed: {meta.get('analysis_timestamp', 'N/A')[:19]}")
    print(f"🔗 Total URLs: {meta.get('total_urls', 0):,}")
    print(f"⚡ Analysis Time: {meta.get('total_execution_time', 0):.2f}s")

    if 'scores' in insights:
        print("\n🎯 Overall Scores:")
        for score_name, score_value in insights['scores'].items():
            emoji = "🟢" if score_value >= 80 else "🟡" if score_value >= 60 else "🔴"
            print(f"  {emoji} {score_name.replace('_', ' ').title()}: {score_value:.1f}/100")


def view_statistical_insights(results: Dict):
    """Display statistical insights."""
    print_header("📈 STATISTICAL ANALYSIS")

    stats = results.get('statistical', {})

    if 'summary_stats' in stats:
        print_section("Basic Statistics")
        summary = stats['summary_stats']

        print(f"  Depth:")
        print(f"    • Average: {summary.get('depth_mean', 0):.2f}")
        print(f"    • Range: {summary.get('depth_min', 0):.0f} - {summary.get('depth_max', 0):.0f}")
        print(f"    • Median: {summary.get('depth_median', 0):.2f}")

        print(f"\n  Path Length:")
        print(f"    • Average: {summary.get('path_length_mean', 0):.2f} chars")
        print(f"    • Range: {summary.get('path_length_min', 0):.0f} - {summary.get('path_length_max', 0):.0f}")

        print(f"\n  Outbound Links:")
        print(f"    • Average per page: {summary.get('outbound_links_mean', 0):.2f}")
        print(f"    • Maximum: {summary.get('outbound_links_max', 0):.0f}")

    if 'url_health' in stats:
        print_section("URL Health Assessment")
        health = stats['url_health']

        grade = health.get('health_grade', 'N/A')
        grade_emoji = {"A": "🌟", "B": "⭐", "C": "✨", "D": "💫", "F": "❌"}.get(grade, "❓")

        print(f"  {grade_emoji} Overall Health: {health.get('overall_health', 0):.1f}/100 (Grade: {grade})")
        print(f"  • URL Length Optimization: {health.get('url_length_score', 0):.1f}%")
        print(f"  • Depth Optimization: {health.get('depth_score', 0):.1f}%")
        print(f"  • Fragment Health: {health.get('fragment_score', 0):.1f}%")

    if 'correlations' in stats:
        print_section("Interesting Correlations")
        for name, corr in stats['correlations'].items():
            if corr.get('significant'):
                emoji = "📈" if corr['correlation'] > 0 else "📉"
                print(f"  {emoji} {name.replace('_', ' ').title()}")
                print(f"     {corr['interpretation']}")
                print(f"     (r={corr['correlation']:.3f}, p={corr['p_value']:.4f})")


def view_semantic_insights(results: Dict):
    """Display semantic analysis insights."""
    print_header("🔤 SEMANTIC ANALYSIS")

    semantic = results.get('semantic_path', {})

    if 'vocabulary' in semantic:
        print_section("Vocabulary Analysis")
        vocab = semantic['vocabulary']

        print(f"  📚 Total Tokens: {vocab.get('total_tokens', 0):,}")
        print(f"  📖 Unique Tokens: {vocab.get('unique_tokens', 0):,}")
        print(f"  🎨 Diversity: {vocab.get('vocabulary_diversity', 'N/A').upper()}")

        if 'top_tokens' in vocab:
            print(f"\n  🔝 Top 15 Keywords:")
            top_tokens = list(vocab['top_tokens'].items())[:15]
            for i, (token, count) in enumerate(top_tokens, 1):
                bar = "█" * min(int(count / top_tokens[0][1] * 20), 20)
                print(f"    {i:2d}. {token:20s} {bar} {count:4d}")

    if 'semantic_categories' in semantic:
        print_section("Content Categories")
        categories = semantic['semantic_categories']

        if 'dominant_category' in categories:
            dom = categories['dominant_category']
            print(f"  🎯 Dominant: {dom.get('name', 'Unknown').upper()} ({dom.get('count', 0)} pages)")

        print(f"\n  📊 Distribution:")
        cat_items = [(k, v) for k, v in categories.items() if k != 'dominant_category']
        cat_items.sort(key=lambda x: x[1].get('count', 0) if isinstance(x[1], dict) else 0, reverse=True)

        for cat, data in cat_items[:10]:
            if isinstance(data, dict):
                count = data.get('count', 0)
                pct = data.get('percentage', 0)
                print(f"    • {cat:20s}: {count:4d} ({pct:5.1f}%)")

    if 'content_type_prediction' in semantic:
        print_section("Predicted Content Types")
        content_types = semantic['content_type_prediction']

        sorted_types = sorted(content_types.items(), key=lambda x: x[1]['count'], reverse=True)

        for ctype, data in sorted_types[:8]:
            count = data['count']
            pct = data['percentage']
            bar = "▓" * min(int(pct / 2), 40)
            print(f"  {ctype:25s} {bar} {pct:5.1f}% ({count:,})")


def view_network_insights(results: Dict):
    """Display network analysis insights."""
    print_header("🌐 NETWORK ANALYSIS")

    network = results.get('network', {})

    if 'network_metrics' in network:
        print_section("Network Metrics")
        metrics = network['network_metrics']

        print(f"  🔗 Nodes: {metrics.get('nodes', 0):,}")
        print(f"  ➡️  Edges: {metrics.get('edges', 0):,}")
        print(f"  🕸️  Density: {metrics.get('density', 0):.6f}")
        print(f"  📊 Average Degree: {metrics.get('average_degree', 0):.2f}")
        print(f"  🔄 Reciprocity: {metrics.get('reciprocity', 0):.4f}")

    if 'centrality' in network:
        print_section("Most Central Pages")
        centrality = network['centrality']

        if centrality.get('top_by_degree'):
            print(f"\n  🌟 Top 5 by Total Connections:")
            for i, item in enumerate(centrality['top_by_degree'][:5], 1):
                print(f"    {i}. [{item['degree']:3d} connections] {item['url'][:70]}")

        if centrality.get('top_by_in_degree'):
            print(f"\n  ⬇️  Top 5 by Incoming Links (Authority):")
            for i, item in enumerate(centrality['top_by_in_degree'][:5], 1):
                print(f"    {i}. [{item['in_degree']:3d} incoming] {item['url'][:70]}")

    if 'link_patterns' in network:
        print_section("Link Patterns")
        patterns = network['link_patterns']

        print(f"  🔗 Self Links: {patterns.get('self_links', 0):,}")
        print(f"  🌍 External Links: {patterns.get('external_links', 0):,}")
        print(f"  👥 Sibling Links: {patterns.get('sibling_links', 0):,}")

    if 'community_detection' in network:
        print_section("Communities")
        communities = network['community_detection']

        print(f"  📦 Total Communities: {communities.get('total_communities', 0)}")

        if communities.get('top_communities'):
            print(f"\n  🔝 Largest Communities:")
            for i, comm in enumerate(communities['top_communities'][:5], 1):
                print(f"    {i}. {comm['community']:30s}: {comm['size']:4d} pages ({comm['percentage']:5.1f}%)")


def view_pathway_insights(results: Dict):
    """Display pathway analysis insights."""
    print_header("🗺️  PATHWAY ANALYSIS")

    pathway = results.get('pathway', {})

    if 'architecture' in pathway:
        print_section("Site Architecture")
        arch = pathway['architecture']

        arch_type = arch.get('architecture_type', 'unknown').upper()
        arch_emoji = {
            'FLAT': '📋',
            'DEEP': '🏔️',
            'WIDE': '🌊',
            'BALANCED': '⚖️'
        }.get(arch_type, '❓')

        print(f"  {arch_emoji} Type: {arch_type}")
        print(f"  📏 Max Depth: {arch.get('max_depth', 0)} levels")
        print(f"  👥 Avg Children per Parent: {arch.get('avg_children_per_parent', 0):.2f}")
        print(f"  🔗 Total Relationships: {arch.get('total_relationships', 0):,}")
        print(f"  👻 Orphan Pages: {arch.get('orphan_pages', 0)}")

    if 'entry_points' in pathway:
        print_section("Entry Points")
        entry = pathway['entry_points']

        print(f"  🚪 Total Entry Points: {entry.get('count', 0)}")

        if entry.get('top_entry_points'):
            print(f"\n  🔝 Top 5 Entry Points:")
            for i, ep in enumerate(entry['top_entry_points'][:5], 1):
                print(f"    {i}. [Depth {ep['depth']}, {ep['children_count']} children] {ep['url'][:60]}")

    if 'navigation_hubs' in pathway:
        print_section("Navigation Hubs")
        hubs = pathway['navigation_hubs']

        print(f"  🎯 Total Hubs: {hubs.get('count', 0)}")

        if hubs.get('top_hubs'):
            print(f"\n  🔝 Top 5 Hubs:")
            for i, hub in enumerate(hubs['top_hubs'][:5], 1):
                print(f"    {i}. [{hub['total_connectivity']} connections] {hub['url'][:60]}")

    if 'dead_ends' in pathway:
        print_section("Dead Ends")
        dead = pathway['dead_ends']

        emoji = "🔴" if dead.get('percentage', 0) > 30 else "🟡" if dead.get('percentage', 0) > 15 else "🟢"
        print(f"  {emoji} Dead-End Pages: {dead.get('count', 0):,} ({dead.get('percentage', 0):.1f}%)")


def view_alerts_recommendations(results: Dict):
    """Display alerts and recommendations."""
    print_header("⚠️  ALERTS & RECOMMENDATIONS")

    insights = results.get('insights', {})

    if insights.get('alerts'):
        print_section("⚠️  Alerts")
        for i, alert in enumerate(insights['alerts'], 1):
            print(f"  {i}. {alert}")

    if insights.get('recommendations'):
        print_section("💡 Recommendations")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"  {i}. {rec}")


def main():
    """Main function."""

    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'analysis/results'

    results = load_results(results_dir)

    print("\n" + "█"*80)
    print("  🔍 URL ANALYSIS INSIGHTS VIEWER".center(80))
    print("█"*80)

    view_overview(results)
    view_statistical_insights(results)
    view_semantic_insights(results)
    view_network_insights(results)
    view_pathway_insights(results)
    view_alerts_recommendations(results)

    print("\n" + "="*80)
    print("📁 Full results available in: " + results_dir)
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
