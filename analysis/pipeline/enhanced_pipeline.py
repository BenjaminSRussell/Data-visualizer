"""
Enhanced Master Analysis Pipeline - Maximum Data Extraction

Purpose: Run ALL analysis modules including new subdomain and component analyzers
         to ensure complete data extraction from URLs
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
from analyzers import subdomain_analyzer
from analyzers import url_component_parser
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
        elif isinstance(obj, set):
            return list(obj)
        return super().default(obj)


class EnhancedPipeline:
    """Enhanced URL analysis pipeline with maximum data extraction."""

    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = input_file
        self.output_dir = output_dir or 'analysis/enhanced_results'
        self.data = []
        self.results = {}
        self.execution_times = {}

        # create output directory
        Path(self.output_dir).mkdir(exist_ok=True, parents=True)

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
            import traceback
            traceback.print_exc()
            return analyzer_name, {'error': str(e)}, 0

    def execute(self) -> Dict:
        """Execute enhanced analysis pipeline."""

        print("\n" + "="*80)
        print("ENHANCED MASTER ANALYSIS PIPELINE")
        print("Maximum Data Extraction Mode")
        print("="*80)

        # load data
        if not self.load_data():
            return None

        # define all analyzers
        analyzers = {
            'statistical': statistical_analyzer.execute,
            'network': network_analyzer.execute,
            'semantic_path': semantic_path_analyzer.execute,
            'pathway': pathway_mapper.execute,
            'subdomain': subdomain_analyzer.execute,
            'url_components': url_component_parser.execute
        }

        # run all analyzers in parallel
        print(f"\nRunning {len(analyzers)} analyzers in parallel...")
        print("Extracting:")
        print("  • Statistical distributions & correlations")
        print("  • Network topology & communities")
        print("  • Semantic content & keywords")
        print("  • Navigation pathways & architecture")
        print("  • Subdomain intelligence & cross-domain links")
        print("  • URL component decomposition")

        total_start = time.time()

        with ThreadPoolExecutor(max_workers=6) as executor:
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
        print("\nGenerating enhanced insights...")
        self.results['insights'] = self._generate_enhanced_insights()

        # generate metadata
        self.results['metadata'] = {
            'input_file': self.input_file,
            'total_urls': len(self.data),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_execution_time': total_elapsed,
            'execution_times': self.execution_times,
            'analyzers_run': list(analyzers.keys())
        }

        # generate data completeness report
        self.results['data_completeness'] = self._assess_data_completeness()

        return self.results

    def _generate_enhanced_insights(self) -> Dict:
        """Generate comprehensive insights from all analyzers."""

        insights = {
            'overview': {},
            'key_findings': [],
            'recommendations': [],
            'alerts': [],
            'scores': {},
            'domain_intelligence': {},
            'url_structure': {}
        }

        # overview
        insights['overview'] = {
            'total_urls_analyzed': len(self.data),
            'analysis_modules_run': len(self.results) - 1,  # exclude metadata
            'data_quality': 'Excellent' if len(self.data) > 1000 else 'Good' if len(self.data) > 100 else 'Limited'
        }

        # extract subdomain insights
        if 'subdomain' in self.results and 'error' not in self.results['subdomain']:
            subdomain = self.results['subdomain']

            if 'domain_overview' in subdomain:
                overview = subdomain['domain_overview']
                insights['domain_intelligence'] = {
                    'total_domains': overview.get('total_domains', 0),
                    'total_subdomains': overview.get('total_subdomains', 0)
                }

                insights['key_findings'].append(
                    f"Analyzed {overview.get('total_domains', 0)} domains with {overview.get('total_subdomains', 0)} subdomains"
                )

            if 'external_dependencies' in subdomain:
                deps = subdomain['external_dependencies']
                if deps.get('critical_dependencies'):
                    count = len(deps['critical_dependencies'])
                    insights['alerts'].append(
                        f"Found {count} critical external dependencies"
                    )

        # extract component insights
        if 'url_components' in self.results and 'error' not in self.results['url_components']:
            components = self.results['url_components']

            if 'scheme_analysis' in components:
                scheme = components['scheme_analysis']
                security_ratio = scheme.get('security_ratio', 0)

                insights['scores']['https_adoption'] = security_ratio * 100

                if security_ratio < 0.9:
                    insights['alerts'].append(
                        f"Only {security_ratio:.1%} of URLs use HTTPS"
                    )

                insights['key_findings'].append(
                    f"HTTPS adoption rate: {security_ratio:.1%}"
                )

            if 'extension_analysis' in components:
                ext = components['extension_analysis']
                insights['url_structure']['unique_extensions'] = ext.get('unique_extensions', 0)

                if ext.get('most_common'):
                    insights['key_findings'].append(
                        f"Most common file extension: .{ext['most_common'][0]}"
                    )

            if 'parameter_analysis' in components:
                params = components['parameter_analysis']
                insights['url_structure']['unique_parameters'] = params.get('total_unique_parameters', 0)

        # standard insights from original analyzers
        if 'statistical' in self.results and 'error' not in self.results['statistical']:
            stats = self.results['statistical']

            if 'url_health' in stats:
                health = stats['url_health']
                insights['scores']['url_health'] = health.get('overall_health', 0)

        if 'semantic_path' in self.results and 'error' not in self.results['semantic_path']:
            semantic = self.results['semantic_path']

            if 'url_quality' in semantic:
                insights['scores']['url_quality'] = semantic['url_quality'].get('quality_score', 0)

            if 'vocabulary' in semantic:
                vocab = semantic['vocabulary']
                insights['url_structure']['unique_keywords'] = vocab.get('unique_tokens', 0)

        # calculate overall score
        if insights['scores']:
            insights['scores']['overall'] = sum(insights['scores'].values()) / len(insights['scores'])

        # generate recommendations
        if insights['scores'].get('https_adoption', 100) < 90:
            insights['recommendations'].append("Migrate remaining HTTP URLs to HTTPS")

        return insights

    def _assess_data_completeness(self) -> Dict:
        """Assess how completely we've extracted data from URLs."""

        completeness = {
            'extraction_coverage': {},
            'data_richness': {},
            'missing_opportunities': []
        }

        # check what we extracted
        total_urls = len(self.data)

        # from subdomain analyzer
        if 'subdomain' in self.results and 'error' not in self.results['subdomain']:
            subdomain = self.results['subdomain']

            if 'domain_overview' in subdomain:
                completeness['extraction_coverage']['domains'] = True
                completeness['extraction_coverage']['subdomains'] = True
                completeness['extraction_coverage']['cross_domain_links'] = True

        # from component parser
        if 'url_components' in self.results and 'error' not in self.results['url_components']:
            components = self.results['url_components']

            completeness['extraction_coverage']['schemes'] = 'scheme_analysis' in components
            completeness['extraction_coverage']['hosts'] = 'host_analysis' in components
            completeness['extraction_coverage']['ports'] = 'port_analysis' in components
            completeness['extraction_coverage']['paths'] = 'path_analysis' in components
            completeness['extraction_coverage']['extensions'] = 'extension_analysis' in components
            completeness['extraction_coverage']['parameters'] = 'parameter_analysis' in components
            completeness['extraction_coverage']['fragments'] = 'fragment_analysis' in components
            completeness['extraction_coverage']['encoding'] = 'encoding_analysis' in components

        # data richness metrics
        completeness['data_richness']['total_data_points'] = self._count_data_points()
        completeness['data_richness']['data_points_per_url'] = completeness['data_richness']['total_data_points'] / total_urls if total_urls > 0 else 0

        # coverage score (0-100)
        coverage_count = sum(1 for v in completeness['extraction_coverage'].values() if v)
        total_possible = len(completeness['extraction_coverage'])
        completeness['coverage_score'] = (coverage_count / total_possible * 100) if total_possible > 0 else 0

        return completeness

    def _count_data_points(self) -> int:
        """Count total data points extracted."""

        total = 0

        # count all leaves in results tree
        def count_recursive(obj):
            nonlocal total

            if isinstance(obj, dict):
                for v in obj.values():
                    count_recursive(v)
            elif isinstance(obj, list):
                total += len(obj)
            else:
                total += 1

        for analyzer_name, result in self.results.items():
            if analyzer_name not in ['metadata', 'insights', 'data_completeness']:
                count_recursive(result)

        return total

    def save_results(self):
        """Save all results to files."""

        print("\nSaving results...")

        # save complete results as json
        output_file = Path(self.output_dir) / 'enhanced_analysis_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, cls=NumpyEncoder)
        print(f"  ✓ Saved complete results to {output_file}")

        # save individual analyzer results
        for analyzer_name, result in self.results.items():
            if analyzer_name not in ['metadata', 'insights', 'data_completeness']:
                analyzer_file = Path(self.output_dir) / f'{analyzer_name}_results.json'
                with open(analyzer_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, cls=NumpyEncoder)
                print(f"  ✓ Saved {analyzer_name} results")

        # save enhanced summary report
        self._save_enhanced_report()

    def _save_enhanced_report(self):
        """Generate and save enhanced summary report."""

        report_file = Path(self.output_dir) / 'enhanced_analysis_report.txt'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ENHANCED URL ANALYSIS REPORT\n")
            f.write("Maximum Data Extraction\n")
            f.write("="*80 + "\n\n")

            # metadata
            meta = self.results.get('metadata', {})
            f.write(f"Input File: {meta.get('input_file', 'N/A')}\n")
            f.write(f"Total URLs Analyzed: {meta.get('total_urls', 0):,}\n")
            f.write(f"Analysis Date: {meta.get('analysis_timestamp', 'N/A')}\n")
            f.write(f"Total Execution Time: {meta.get('total_execution_time', 0):.2f}s\n")
            f.write(f"Analyzers Run: {', '.join(meta.get('analyzers_run', []))}\n")
            f.write("\n")

            # data completeness
            if 'data_completeness' in self.results:
                completeness = self.results['data_completeness']
                f.write("DATA EXTRACTION COMPLETENESS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Coverage Score: {completeness.get('coverage_score', 0):.1f}%\n")
                f.write(f"Total Data Points Extracted: {completeness['data_richness'].get('total_data_points', 0):,}\n")
                f.write(f"Data Points per URL: {completeness['data_richness'].get('data_points_per_url', 0):.1f}\n")
                f.write("\n")

            # insights
            insights = self.results.get('insights', {})

            if insights.get('domain_intelligence'):
                f.write("DOMAIN INTELLIGENCE\n")
                f.write("-" * 80 + "\n")
                di = insights['domain_intelligence']
                f.write(f"Total Domains: {di.get('total_domains', 0)}\n")
                f.write(f"Total Subdomains: {di.get('total_subdomains', 0)}\n")
                f.write("\n")

            if insights.get('url_structure'):
                f.write("URL STRUCTURE ANALYSIS\n")
                f.write("-" * 80 + "\n")
                struct = insights['url_structure']
                f.write(f"Unique Extensions: {struct.get('unique_extensions', 0)}\n")
                f.write(f"Unique Parameters: {struct.get('unique_parameters', 0)}\n")
                f.write(f"Unique Keywords: {struct.get('unique_keywords', 0)}\n")
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

        print(f"  ✓ Saved enhanced report to {report_file}")

    def print_summary(self):
        """Print summary to console."""

        print("\n" + "="*80)
        print("ENHANCED ANALYSIS SUMMARY")
        print("="*80)

        # data completeness
        if 'data_completeness' in self.results:
            completeness = self.results['data_completeness']
            print(f"\nData Extraction:")
            print(f"  Coverage Score: {completeness.get('coverage_score', 0):.1f}%")
            print(f"  Total Data Points: {completeness['data_richness'].get('total_data_points', 0):,}")
            print(f"  Data Points per URL: {completeness['data_richness'].get('data_points_per_url', 0):.1f}")

        insights = self.results.get('insights', {})

        # domain intelligence
        if insights.get('domain_intelligence'):
            print(f"\nDomain Intelligence:")
            di = insights['domain_intelligence']
            print(f"  Domains: {di.get('total_domains', 0)}")
            print(f"  Subdomains: {di.get('total_subdomains', 0)}")

        # key findings
        if insights.get('key_findings'):
            print(f"\nKey Findings:")
            for finding in insights['key_findings'][:5]:
                print(f"  • {finding}")

        print("\n" + "="*80)


def main():
    """Main execution function."""

    if len(sys.argv) < 2:
        print("Usage: python enhanced_pipeline.py <input_jsonl_file> [output_dir]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'analysis/enhanced_results'

    # create and run pipeline
    pipeline = EnhancedPipeline(input_file, output_dir)

    results = pipeline.execute()

    if results:
        pipeline.save_results()
        pipeline.print_summary()

        print(f"\n✓ Enhanced analysis complete! Results saved to {output_dir}/")
        print(f"\n🎯 Maximum data extraction achieved!")
        print(f"   All URL components, subdomains, and patterns extracted.")
    else:
        print("\n✗ Analysis failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
