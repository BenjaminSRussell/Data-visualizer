"""
Master Analysis Pipeline - Orchestrate All URL Analysis

Purpose: Run all analysis modules in parallel, combine results,
         generate comprehensive insights, and produce reports
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# import all analyzers
from analyzers import statistical_analyzer
from analyzers import network_analyzer
from analyzers import semantic_path_analyzer
from mappers import pathway_mapper


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return super().default(obj)


class MasterPipeline:
    """Orchestrate comprehensive URL analysis."""

    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = input_file
        self.output_dir = output_dir or 'results'
        self.data = []
        self.results = {}
        self.execution_times = {}

        # create output directory
        Path(self.output_dir).mkdir(exist_ok=True)

    def load_data(self) -> bool:
        """Load JSONL data."""
        print(f"Loading data from {self.input_file}...")

        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.data.append(json.loads(line))

            print(f"✓ Loaded {len(self.data):,} URLs")
            return True

        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return False

    def run_analysis(self, analyzer_name: str, analyzer_func, data: List[Dict]) -> Tuple[str, Dict, float]:
        """Run single analyzer with timing."""
        print(f"  Running {analyzer_name}...")

        start_time = time.time()

        try:
            result = analyzer_func(data)
            elapsed = time.time() - start_time

            print(f"  ✓ {analyzer_name} completed in {elapsed:.2f}s")
            return analyzer_name, result, elapsed

        except Exception as e:
            print(f"  ✗ {analyzer_name} failed: {e}")
            return analyzer_name, {'error': str(e)}, 0

    def execute(self) -> Dict:
        """Execute full analysis pipeline."""

        print("\n" + "="*80)
        print("MASTER ANALYSIS PIPELINE")
        print("="*80)

        # load data
        if not self.load_data():
            return None

        # define all analyzers
        analyzers = {
            'statistical': statistical_analyzer.execute,
            'network': network_analyzer.execute,
            'semantic_path': semantic_path_analyzer.execute,
            'pathway': pathway_mapper.execute
        }

        # run all analyzers in parallel
        print(f"\nRunning {len(analyzers)} analyzers in parallel...")

        total_start = time.time()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.run_analysis, name, func, self.data): name
                for name, func in analyzers.items()
            }

            for future in as_completed(futures):
                analyzer_name, result, elapsed = future.result()
                self.results[analyzer_name] = result
                self.execution_times[analyzer_name] = elapsed

        total_elapsed = time.time() - total_start

        print(f"\n✓ All analyses completed in {total_elapsed:.2f}s")

        # generate combined insights
        print("\nGenerating combined insights...")
        self.results['insights'] = self._generate_insights()

        # generate metadata
        self.results['metadata'] = {
            'input_file': self.input_file,
            'total_urls': len(self.data),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_execution_time': total_elapsed,
            'execution_times': self.execution_times
        }

        return self.results

    def _generate_insights(self) -> Dict:
        """Generate high-level insights by combining all analysis results."""

        insights = {
            'overview': {},
            'key_findings': [],
            'recommendations': [],
            'alerts': [],
            'scores': {}
        }

        # overview from metadata
        insights['overview'] = {
            'total_urls_analyzed': len(self.data),
            'analysis_modules_run': len(self.results),
            'data_quality': 'Good' if len(self.data) > 100 else 'Limited'
        }

        # extract key findings from each analyzer
        if 'statistical' in self.results and 'error' not in self.results['statistical']:
            stats = self.results['statistical']

            # health score
            if 'url_health' in stats:
                health = stats['url_health']
                insights['scores']['url_health'] = health.get('overall_health', 0)
                insights['key_findings'].append(
                    f"URL Health Score: {health.get('overall_health', 0):.1f}/100 (Grade: {health.get('health_grade', 'N/A')})"
                )

            # depth analysis
            if 'summary_stats' in stats:
                summary = stats['summary_stats']
                insights['key_findings'].append(
                    f"Average URL depth: {summary.get('depth_mean', 0):.2f} levels"
                )

                if summary.get('depth_mean', 0) > 5:
                    insights['alerts'].append("URLs are too deep on average (>5 levels)")
                    insights['recommendations'].append("Consider flattening URL hierarchy")

            # anomalies
            if 'anomalies' in stats:
                for anomaly_type, anomaly_data in stats['anomalies'].items():
                    if anomaly_data.get('count', 0) > 0:
                        insights['alerts'].append(
                            f"{anomaly_type}: {anomaly_data['count']} outliers detected"
                        )

        # network insights
        if 'network' in self.results and 'error' not in self.results['network']:
            network = self.results['network']

            if 'network_metrics' in network:
                metrics = network['network_metrics']
                insights['key_findings'].append(
                    f"Network density: {metrics.get('density', 0):.6f}"
                )

                if metrics.get('density', 0) < 0.01:
                    insights['alerts'].append("Low network density - pages are poorly connected")
                    insights['recommendations'].append("Add more internal links between pages")

            if 'link_patterns' in network:
                patterns = network['link_patterns']

                dead_ends = patterns.get('self_links', 0)
                if dead_ends > len(self.data) * 0.3:
                    insights['alerts'].append(f"High number of self-links ({dead_ends})")

        # semantic insights
        if 'semantic_path' in self.results and 'error' not in self.results['semantic_path']:
            semantic = self.results['semantic_path']

            if 'url_quality' in semantic:
                quality = semantic['url_quality']
                insights['scores']['url_quality'] = quality.get('quality_score', 0)

            if 'semantic_categories' in semantic:
                categories = semantic['semantic_categories']

                if 'dominant_category' in categories:
                    dom = categories['dominant_category']
                    insights['key_findings'].append(
                        f"Dominant content category: {dom.get('name', 'Unknown')}"
                    )

            if 'seo_insights' in semantic:
                seo = semantic['seo_insights']
                insights['recommendations'].extend(seo.get('recommendations', []))

        # pathway insights
        if 'pathway' in self.results and 'error' not in self.results['pathway']:
            pathway = self.results['pathway']

            if 'architecture' in pathway:
                arch = pathway['architecture']
                insights['key_findings'].append(
                    f"Site architecture type: {arch.get('architecture_type', 'Unknown')}"
                )

            if 'dead_ends' in pathway:
                dead = pathway['dead_ends']
                if dead.get('percentage', 0) > 20:
                    insights['alerts'].append(
                        f"High percentage of dead-end pages ({dead.get('percentage', 0):.1f}%)"
                    )
                    insights['recommendations'].append("Add navigation links to dead-end pages")

            if 'connectivity' in pathway:
                conn = pathway['connectivity']
                if not conn.get('is_fully_connected', False):
                    insights['alerts'].append(
                        f"Site is not fully connected ({conn.get('total_components', 0)} separate components)"
                    )

        # calculate overall score
        scores = insights['scores']
        if scores:
            insights['scores']['overall'] = sum(scores.values()) / len(scores)

        return insights

    def save_results(self):
        """Save all results to files."""

        print("\nSaving results...")

        # save complete results as json
        output_file = Path(self.output_dir) / 'analysis_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, cls=NumpyEncoder)
        print(f"  ✓ Saved complete results to {output_file}")

        # save individual analyzer results
        for analyzer_name, result in self.results.items():
            if analyzer_name not in ['metadata', 'insights']:
                analyzer_file = Path(self.output_dir) / f'{analyzer_name}_results.json'
                with open(analyzer_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, cls=NumpyEncoder)
                print(f"  ✓ Saved {analyzer_name} results to {analyzer_file}")

        # save summary report
        self._save_summary_report()

    def _save_summary_report(self):
        """Generate and save human-readable summary report."""

        report_file = Path(self.output_dir) / 'analysis_report.txt'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("COMPREHENSIVE URL ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")

            # metadata
            meta = self.results.get('metadata', {})
            f.write(f"Input File: {meta.get('input_file', 'N/A')}\n")
            f.write(f"Total URLs Analyzed: {meta.get('total_urls', 0):,}\n")
            f.write(f"Analysis Date: {meta.get('analysis_timestamp', 'N/A')}\n")
            f.write(f"Total Execution Time: {meta.get('total_execution_time', 0):.2f}s\n")
            f.write("\n")

            # insights
            insights = self.results.get('insights', {})

            # scores
            if 'scores' in insights:
                f.write("OVERALL SCORES\n")
                f.write("-" * 80 + "\n")
                for score_name, score_value in insights['scores'].items():
                    f.write(f"  {score_name.replace('_', ' ').title()}: {score_value:.1f}/100\n")
                f.write("\n")

            # key findings
            if insights.get('key_findings'):
                f.write("KEY FINDINGS\n")
                f.write("-" * 80 + "\n")
                for finding in insights['key_findings']:
                    f.write(f"  • {finding}\n")
                f.write("\n")

            # alerts
            if insights.get('alerts'):
                f.write("ALERTS\n")
                f.write("-" * 80 + "\n")
                for alert in insights['alerts']:
                    f.write(f"  ⚠ {alert}\n")
                f.write("\n")

            # recommendations
            if insights.get('recommendations'):
                f.write("RECOMMENDATIONS\n")
                f.write("-" * 80 + "\n")
                for rec in insights['recommendations']:
                    f.write(f"  → {rec}\n")
                f.write("\n")

            # individual analyzer summaries
            f.write("\n" + "="*80 + "\n")
            f.write("DETAILED ANALYSIS RESULTS\n")
            f.write("="*80 + "\n\n")

            # statistical
            if 'statistical' in self.results:
                self._write_statistical_summary(f, self.results['statistical'])

            # network
            if 'network' in self.results:
                self._write_network_summary(f, self.results['network'])

            # semantic
            if 'semantic_path' in self.results:
                self._write_semantic_summary(f, self.results['semantic_path'])

            # pathway
            if 'pathway' in self.results:
                self._write_pathway_summary(f, self.results['pathway'])

        print(f"  ✓ Saved summary report to {report_file}")

    def _write_statistical_summary(self, f, results: Dict):
        """Write statistical analysis summary."""
        f.write("STATISTICAL ANALYSIS\n")
        f.write("-" * 80 + "\n")

        if 'summary_stats' in results:
            stats = results['summary_stats']
            f.write(f"  Depth: {stats.get('depth_mean', 0):.2f} ± {stats.get('depth_std', 0):.2f}\n")
            f.write(f"  Path Length: {stats.get('path_length_mean', 0):.2f} ± {stats.get('path_length_std', 0):.2f}\n")
            f.write(f"  Avg Links per Page: {stats.get('outbound_links_mean', 0):.2f}\n")

        if 'url_health' in results:
            health = results['url_health']
            f.write(f"  Overall Health: {health.get('overall_health', 0):.1f}/100 ({health.get('health_grade', 'N/A')})\n")

        f.write("\n")

    def _write_network_summary(self, f, results: Dict):
        """Write network analysis summary."""
        f.write("NETWORK ANALYSIS\n")
        f.write("-" * 80 + "\n")

        if 'network_metrics' in results:
            metrics = results['network_metrics']
            f.write(f"  Nodes: {metrics.get('nodes', 0):,}\n")
            f.write(f"  Edges: {metrics.get('edges', 0):,}\n")
            f.write(f"  Density: {metrics.get('density', 0):.6f}\n")
            f.write(f"  Avg Degree: {metrics.get('average_degree', 0):.2f}\n")

        f.write("\n")

    def _write_semantic_summary(self, f, results: Dict):
        """Write semantic analysis summary."""
        f.write("SEMANTIC ANALYSIS\n")
        f.write("-" * 80 + "\n")

        if 'vocabulary' in results:
            vocab = results['vocabulary']
            f.write(f"  Unique Tokens: {vocab.get('unique_tokens', 0):,}\n")
            f.write(f"  Vocabulary Diversity: {vocab.get('vocabulary_diversity', 'N/A')}\n")

        if 'url_quality' in results:
            quality = results['url_quality']
            f.write(f"  URL Quality Score: {quality.get('quality_score', 0):.1f}/100\n")

        f.write("\n")

    def _write_pathway_summary(self, f, results: Dict):
        """Write pathway analysis summary."""
        f.write("PATHWAY ANALYSIS\n")
        f.write("-" * 80 + "\n")

        if 'architecture' in results:
            arch = results['architecture']
            f.write(f"  Architecture Type: {arch.get('architecture_type', 'N/A')}\n")
            f.write(f"  Max Depth: {arch.get('max_depth', 0)}\n")

        if 'dead_ends' in results:
            dead = results['dead_ends']
            f.write(f"  Dead-End Pages: {dead.get('count', 0)} ({dead.get('percentage', 0):.1f}%)\n")

        f.write("\n")

    def print_summary(self):
        """Print summary to console."""

        print("\n" + "="*80)
        print("ANALYSIS SUMMARY")
        print("="*80)

        insights = self.results.get('insights', {})

        # scores
        if 'scores' in insights and insights['scores']:
            print("\nOverall Scores:")
            for score_name, score_value in insights['scores'].items():
                print(f"  {score_name.replace('_', ' ').title()}: {score_value:.1f}/100")

        # key findings
        if insights.get('key_findings'):
            print("\nKey Findings:")
            for finding in insights['key_findings'][:5]:
                print(f"  • {finding}")

        # alerts
        if insights.get('alerts'):
            print(f"\n⚠ {len(insights['alerts'])} Alert(s):")
            for alert in insights['alerts'][:3]:
                print(f"  ⚠ {alert}")

        print("\n" + "="*80)


def main():
    """Main execution function."""

    if len(sys.argv) < 2:
        print("Usage: python master_pipeline.py <input_jsonl_file> [output_dir]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'results'

    # create and run pipeline
    pipeline = MasterPipeline(input_file, output_dir)

    results = pipeline.execute()

    if results:
        pipeline.save_results()
        pipeline.print_summary()

        print(f"\n✓ Analysis complete! Results saved to {output_dir}/")
    else:
        print("\n✗ Analysis failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
