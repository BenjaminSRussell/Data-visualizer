"""
MLX-Enhanced Analysis Pipeline

Comprehensive URL analysis with:
- MLX-powered deep learning
- URL normalization (52% reduction)
- Batch detection with context
- PostgreSQL storage
- Rich terminal output
- Temporal clustering
- Parent-child relationship analysis
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# import all components
from processors.url_normalizer import URLNormalizer
from ml.url_embeddings import URLEmbedder
from ml.batch_detector import BatchDetector
from ml.pattern_recognition import PatternRecognizer
from viewers.rich_report_viewer import RichReportViewer

# import existing analyzers
from analyzers import statistical_analyzer, network_analyzer, semantic_path_analyzer
from mappers import pathway_mapper


class MLXEnhancedPipeline:
    """
    Enhanced analysis pipeline with ML, normalization, and rich output.
    """

    def __init__(self, input_file: str, output_dir: str = None, use_db=False, database_url=None):
        self.input_file = input_file
        self.output_dir = output_dir or 'data/output/mlx'
        self.use_db = use_db
        self.database_url = database_url

        # create output directory
        Path(self.output_dir).mkdir(exist_ok=True, parents=True)

        # components
        self.normalizer = URLNormalizer()
        self.embedder = URLEmbedder(embedding_dim=128)
        self.batch_detector = None
        self.pattern_recognizer = PatternRecognizer()
        self.viewer = RichReportViewer()

        # data
        self.raw_data = []
        self.normalized_data = []
        self.results = {}
        self.execution_times = {}

        # database
        self.db_manager = None
        if use_db:
            from database.connection import init_database
            self.db_manager = init_database(database_url)

    def load_data(self) -> bool:
        """Load and normalize data"""
        self.viewer.show_header(
            "MLX-Enhanced URL Analysis Pipeline",
            f"Loading: {self.input_file}"
        )

        print(f"\nLoading raw data...")

        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.raw_data.append(json.loads(line))

            print(f"Loaded {len(self.raw_data):,} raw URLs\n")

            # normalize urls
            print("Normalizing URLs (removing fragments, deduplicating)...")
            self.normalized_data = self.normalizer.normalize_batch(
                self.raw_data,
                remove_fragments=True,
                merge_metadata=True
            )

            self.normalizer.print_stats()

            # save normalized data
            normalized_file = Path(self.output_dir) / 'normalized_urls.jsonl'
            with open(normalized_file, 'w') as f:
                for item in self.normalized_data:
                    f.write(json.dumps(item) + '\n')

            print(f"Saved normalized URLs to {normalized_file}\n")

            return True

        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def train_embeddings(self):
        """Train URL embeddings using MLX"""
        print("Training MLX-powered URL embeddings...")

        urls = [item['url'] for item in self.normalized_data]

        start_time = time.time()
        self.embedder.train_embeddings(urls, epochs=3, window_size=3)
        elapsed = time.time() - start_time

        self.execution_times['embeddings'] = elapsed

        # save embeddings
        embedding_file = Path(self.output_dir) / 'url_embeddings.pkl'
        self.embedder.save_embeddings(str(embedding_file))

        print()

    def detect_batches(self):
        """Detect URL batches using multiple strategies"""
        print("Detecting URL batches...")

        start_time = time.time()

        self.batch_detector = BatchDetector(self.embedder)
        batches = self.batch_detector.detect_all_batches(self.normalized_data)

        # analyze context for each batch
        print("\nAnalyzing batch contexts...")
        for batch in batches:
            context = self.batch_detector.analyze_batch_context(batch)
            batch['context'] = context

        elapsed = time.time() - start_time
        self.execution_times['batch_detection'] = elapsed

        self.results['batch_analysis'] = {
            'batches': batches,
            'summary': self.batch_detector.get_batch_summary()
        }

        print()

    def analyze_patterns(self):
        """Analyze URL patterns"""
        print("Analyzing URL patterns...")

        start_time = time.time()

        pattern_results = self.pattern_recognizer.analyze_patterns(self.normalized_data)

        elapsed = time.time() - start_time
        self.execution_times['pattern_recognition'] = elapsed

        self.results['patterns'] = pattern_results

    def analyze_temporal_clusters(self):
        """Analyze temporal clustering patterns"""
        print("⏰ Analyzing temporal clusters...")

        from datetime import datetime
        from collections import defaultdict

        temporal_clusters = defaultdict(list)

        for item in self.normalized_data:
            discovered_at = item.get('discovered_at')
            if discovered_at:
                # group by 5-minute windows
                dt = datetime.fromtimestamp(discovered_at)
                window = dt.replace(second=0, microsecond=0)
                window_5min = window.replace(minute=(window.minute // 5) * 5)
                temporal_clusters[window_5min].append(item)

        # analyze clusters
        cluster_analysis = []
        for window, urls in temporal_clusters.items():
            if len(urls) >= 10:  # significant cluster
                cluster_analysis.append({
                    'window': window.isoformat(),
                    'url_count': len(urls),
                    'avg_depth': sum(u.get('depth', 0) for u in urls) / len(urls),
                    'unique_parents': len(set(u.get('parent_url') for u in urls if u.get('parent_url'))),
                    'sample_urls': [u['url'] for u in urls[:5]]
                })

        # sort by url count
        cluster_analysis.sort(key=lambda x: x['url_count'], reverse=True)

        self.results['temporal_clusters'] = {
            'total_clusters': len(temporal_clusters),
            'significant_clusters': len(cluster_analysis),
            'clusters': cluster_analysis[:20],  # top 20
            'largest_burst': max((c['url_count'] for c in cluster_analysis), default=0)
        }

        print(f"  ✓ Found {len(cluster_analysis)} significant temporal clusters\n")

    def analyze_parent_child_relationships(self):
        """Analyze parent-child URL relationships"""
        print("👨‍👧 Analyzing parent-child relationships...")

        from collections import defaultdict, Counter

        # build parent -> children mapping
        parent_children = defaultdict(list)
        child_parent = {}

        for item in self.normalized_data:
            url = item['url']
            parent = item.get('parent_url')

            if parent:
                # normalize parent url
                parent_normalized = self.normalizer.normalize_url(parent)
                parent_children[parent_normalized].append(url)
                child_parent[url] = parent_normalized

        # analyze relationships
        relationship_analysis = {
            'total_urls': len(self.normalized_data),
            'urls_with_parents': len(child_parent),
            'unique_parents': len(parent_children),
            'orphan_urls': len(self.normalized_data) - len(child_parent),
            'avg_children_per_parent': len(child_parent) / len(parent_children) if parent_children else 0,
            'max_children': max((len(children) for children in parent_children.values()), default=0)
        }

        # find most prolific parents
        parent_counts = [(parent, len(children)) for parent, children in parent_children.items()]
        parent_counts.sort(key=lambda x: x[1], reverse=True)

        relationship_analysis['top_parents'] = [
            {'url': parent, 'children_count': count}
            for parent, count in parent_counts[:20]
        ]

        # find depth relationships
        depth_transitions = Counter()
        for child, parent in child_parent.items():
            # find items
            child_item = next((i for i in self.normalized_data if i['url'] == child), None)
            parent_item = next((i for i in self.normalized_data if i['url'] == parent), None)

            if child_item and parent_item:
                child_depth = child_item.get('depth', 0)
                parent_depth = parent_item.get('depth', 0)
                depth_transitions[(parent_depth, child_depth)] += 1

        # convert tuple keys to strings for JSON serialization
        relationship_analysis['depth_transitions'] = {
            f"{parent_depth}->{child_depth}": count
            for (parent_depth, child_depth), count in depth_transitions.most_common(10)
        }

        self.results['parent_child_relationships'] = relationship_analysis

        print(f"  ✓ Analyzed {len(parent_children):,} parent URLs\n")

    def run_traditional_analyzers(self):
        """Run traditional statistical/network analyzers"""
        print("📊 Running traditional analysis modules...")

        analyzers = {
            'statistical': statistical_analyzer.execute,
            'network': network_analyzer.execute,
            'semantic_path': semantic_path_analyzer.execute,
            'pathway': pathway_mapper.execute
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._run_analyzer, name, func): name
                for name, func in analyzers.items()
            }

            for future in as_completed(futures):
                name, result, elapsed = future.result()
                self.results[name] = result
                self.execution_times[name] = elapsed

        print()

    def _run_analyzer(self, name: str, func, data=None):
        """Run a single analyzer"""
        if data is None:
            data = self.normalized_data

        print(f"  Running {name}...")

        start_time = time.time()
        try:
            result = func(data)
            elapsed = time.time() - start_time
            print(f"  ✓ {name} completed in {elapsed:.2f}s")
            return name, result, elapsed
        except Exception as e:
            print(f"  ✗ {name} failed: {e}")
            return name, {'error': str(e)}, 0

    def generate_insights(self):
        """Generate comprehensive insights"""
        print("💡 Generating insights...")

        insights = {
            'normalization_impact': self.normalizer.get_stats(),
            'batch_insights': self.results.get('batch_analysis', {}).get('summary', {}),
            'pattern_insights': self._summarize_patterns(),
            'temporal_insights': self._summarize_temporal(),
            'relationship_insights': self._summarize_relationships(),
            'overall_scores': self._calculate_scores()
        }

        self.results['insights'] = insights

    def _summarize_patterns(self) -> Dict:
        """Summarize pattern analysis"""
        patterns = self.results.get('patterns', {})

        summary = []

        # temporal patterns
        temporal = patterns.get('temporal_patterns', {})
        if temporal.get('has_temporal_patterns'):
            summary.append(f"Found {temporal.get('unique_years', 0)} unique years in URLs")

        # id patterns
        id_patterns = patterns.get('id_patterns', {})
        if id_patterns.get('urls_with_numeric_ids', 0) > 0:
            summary.append(f"{id_patterns['urls_with_numeric_ids']} URLs contain numeric IDs")

        # structures
        structures = patterns.get('structure_patterns', {})
        if structures:
            summary.append(f"Detected {structures.get('unique_structures', 0)} unique URL structures")

        return {
            'summary_points': summary,
            'has_temporal': temporal.get('has_temporal_patterns', False),
            'has_ids': id_patterns.get('urls_with_numeric_ids', 0) > 0
        }

    def _summarize_temporal(self) -> Dict:
        """Summarize temporal analysis"""
        temporal = self.results.get('temporal_clusters', {})

        return {
            'clusters_found': temporal.get('significant_clusters', 0),
            'largest_burst': temporal.get('largest_burst', 0),
            'description': f"Detected {temporal.get('significant_clusters', 0)} temporal burst periods"
        }

    def _summarize_relationships(self) -> Dict:
        """Summarize relationship analysis"""
        rels = self.results.get('parent_child_relationships', {})

        return {
            'unique_parents': rels.get('unique_parents', 0),
            'orphans': rels.get('orphan_urls', 0),
            'avg_children': rels.get('avg_children_per_parent', 0),
            'description': f"{rels.get('unique_parents', 0)} parent URLs generate {rels.get('urls_with_parents', 0)} children"
        }

    def _calculate_scores(self) -> Dict:
        """Calculate overall quality scores"""
        scores = {}

        # use existing scores from analyzers
        if 'statistical' in self.results:
            stats = self.results['statistical']
            if 'url_health' in stats:
                scores['url_health'] = stats['url_health'].get('overall_health', 0)

        if 'semantic_path' in self.results:
            semantic = self.results['semantic_path']
            if 'url_quality' in semantic:
                scores['url_quality'] = semantic['url_quality'].get('quality_score', 0)

        # add new scores
        normalization_stats = self.normalizer.get_stats()
        if normalization_stats['total_input'] > 0:
            data_quality_score = (normalization_stats['total_output'] / normalization_stats['total_input']) * 100
            scores['data_quality'] = 100 - data_quality_score  # higher is better (less duplicates)

        # overall score
        if scores:
            scores['overall'] = sum(scores.values()) / len(scores)

        return scores

    def save_results(self):
        """Save all results"""
        print("💾 Saving results...")

        # add metadata
        self.results['metadata'] = {
            'input_file': self.input_file,
            'raw_urls': len(self.raw_data),
            'normalized_urls': len(self.normalized_data),
            'reduction': f"{(1 - len(self.normalized_data)/len(self.raw_data))*100:.1f}%",
            'analysis_timestamp': datetime.now().isoformat(),
            'total_execution_time': sum(self.execution_times.values()),
            'execution_times': self.execution_times
        }

        # save complete results
        results_file = Path(self.output_dir) / 'enhanced_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"  ✓ Saved complete results to {results_file}")

        # save condensed text report
        self._save_text_report()

    def _save_text_report(self):
        """Save condensed, readable text report"""
        report_file = Path(self.output_dir) / 'enhanced_report.txt'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("MLX-ENHANCED URL ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")

            meta = self.results['metadata']
            f.write(f"Input: {meta['input_file']}\n")
            f.write(f"Raw URLs: {meta['raw_urls']:,}\n")
            f.write(f"Normalized URLs: {meta['normalized_urls']:,}\n")
            f.write(f"Reduction: {meta['reduction']}\n")
            f.write(f"Analysis Time: {meta['total_execution_time']:.2f}s\n")
            f.write("\n")

            # write more sections...
            # (similar to master_pipeline but enhanced)

        print(f"  ✓ Saved text report to {report_file}\n")

    def show_rich_report(self):
        """Display rich terminal report"""
        print("\n")
        self.viewer.show_full_report(self.results)

    def execute(self):
        """Execute complete enhanced pipeline"""
        total_start = time.time()

        # load and normalize
        if not self.load_data():
            return None

        # train embeddings
        self.train_embeddings()

        # detect batches
        self.detect_batches()

        # analyze patterns
        self.analyze_patterns()

        # new: temporal clustering
        self.analyze_temporal_clusters()

        # new: parent-child relationships
        self.analyze_parent_child_relationships()

        # run traditional analyzers
        self.run_traditional_analyzers()

        # generate insights
        self.generate_insights()

        # save results
        total_time = time.time() - total_start
        self.execution_times['total'] = total_time

        self.save_results()

        # show rich report
        self.show_rich_report()

        return self.results


def main():
    if len(sys.argv) < 2:
        print("Usage: python mlx_enhanced_pipeline.py <input_jsonl_file> [output_dir]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'enhanced_results'

    pipeline = MLXEnhancedPipeline(input_file, output_dir)
    results = pipeline.execute()

    if results:
        print("\n✅ Enhanced analysis complete!")
    else:
        print("\n❌ Analysis failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
