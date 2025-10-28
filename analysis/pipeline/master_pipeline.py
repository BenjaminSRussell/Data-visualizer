"""
Master Analysis Pipeline - Unified URL Analysis System

Runs all analysis types (basic, enhanced, MLX) based on global configuration
"""

import json
import logging
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.analyzers import statistical_analyzer, network_analyzer, semantic_path_analyzer
from analysis.analyzers import subdomain_analyzer, url_component_parser
from analysis.mappers import pathway_mapper


logging.getLogger(__name__).addHandler(logging.NullHandler())


class NumpyEncoder(json.JSONEncoder):
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


class MasterPipeline:
    def __init__(self, input_file: str, output_dir: str = None, config_path: str = None):
        self.config = self._load_config(config_path or 'global.yml')
        self.input_file = input_file
        self.output_dir = output_dir or self.config['data']['output_dir']
        self.data = []
        self.normalized_data = []
        self.results = {}
        self.execution_times = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure a file-based logger for pipeline messages."""
        log_dir = Path(self.output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "master_pipeline.log"

        exists = any(
            isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_file
            for handler in self.logger.handlers
        )

        if not exists:
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(logging.INFO)
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            )
            self.logger.addHandler(handler)

        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning("Config file not found: %s. Using defaults.", config_path)
            return self._default_config()

    def _default_config(self) -> Dict:
        return {
            'data': {'output_dir': 'data/output'},
            'analysis': {
                'types': {
                    'basic': {'enabled': True, 'analyzers': ['statistical', 'network', 'semantic_path', 'pathway']},
                    'enhanced': {'enabled': True, 'analyzers': ['subdomain', 'url_components']},
                    'mlx': {'enabled': False}
                }
            },
            'performance': {'max_workers': 6}
        }

    def load_data(self) -> bool:
        self.logger.info("Loading data from %s", self.input_file)
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.data.append(json.loads(line))
            self.logger.info("Loaded %s URLs", f"{len(self.data):,}")
            return True
        except Exception as e:
            self.logger.exception("Error loading data")
            return False

    def run_analyzer(self, name: str, func, data: List[Dict]) -> Tuple[str, Dict, float]:
        self.logger.info("Running analyzer: %s", name)
        start_time = time.time()
        try:
            result = func(data)
            elapsed = time.time() - start_time
            self.logger.info("Analyzer %s completed in %.2fs", name, elapsed)
            return name, result, elapsed
        except Exception as e:
            self.logger.exception("Analyzer %s failed", name)
            return name, {'error': str(e)}, 0

    def run_basic_analysis(self):
        if not self.config['analysis']['types']['basic']['enabled']:
            return

        self.logger.info("Starting basic analysis")

        analyzers = {
            'statistical': statistical_analyzer.execute,
            'network': network_analyzer.execute,
            'semantic_path': semantic_path_analyzer.execute,
            'pathway': pathway_mapper.execute
        }

        self._run_analyzers(analyzers, 'basic')

    def run_enhanced_analysis(self):
        if not self.config['analysis']['types']['enhanced']['enabled']:
            return

        self.logger.info("Starting enhanced analysis")

        analyzers = {
            'subdomain': subdomain_analyzer.execute,
            'url_components': url_component_parser.execute
        }

        self._run_analyzers(analyzers, 'enhanced')

    def run_mlx_analysis(self):
        if not self.config['analysis']['types']['mlx']['enabled']:
            return

        self.logger.info("Starting MLX analysis")

        try:
            from analysis.processors.url_normalizer import URLNormalizer
            from analysis.ml.url_embeddings import URLEmbedder
            from analysis.ml.batch_detector import BatchDetector
            from analysis.ml.pattern_recognition import PatternRecognizer

            mlx_config = self.config.get('mlx', {})

            normalizer = URLNormalizer()
            self.logger.info("Normalizing URLs")
            self.normalized_data = normalizer.normalize_batch(
                self.data,
                remove_fragments=self.config['normalization']['remove_fragments'],
                merge_metadata=self.config['normalization']['merge_metadata']
            )
            self.results['mlx_normalization'] = normalizer.get_stats()

            embedder = URLEmbedder(embedding_dim=mlx_config.get('embedding_dim', 128))
            urls = [item['url'] for item in self.normalized_data]
            self.logger.info("Training embeddings")
            start_time = time.time()
            embedder.train_embeddings(
                urls,
                epochs=mlx_config.get('training_epochs', 3),
                window_size=mlx_config.get('window_size', 3)
            )
            self.execution_times['embeddings'] = time.time() - start_time

            self.logger.info("Detecting batches")
            batch_detector = BatchDetector(embedder)
            batches = batch_detector.detect_all_batches(self.normalized_data)
            self.results['batch_analysis'] = {
                'batches': batches,
                'summary': batch_detector.get_batch_summary()
            }

            self.logger.info("Analyzing patterns")
            pattern_recognizer = PatternRecognizer()
            self.results['patterns'] = pattern_recognizer.analyze_patterns(self.normalized_data)

            self._analyze_temporal_clusters()
            self._analyze_parent_child_relationships()

        except ImportError as e:
            self.logger.warning("MLX dependencies not available: %s", e)
            self.results['mlx'] = {'error': 'MLX dependencies not installed'}

    def _run_analyzers(self, analyzers: Dict, analysis_type: str):
        max_workers = self.config['performance']['max_workers']

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.run_analyzer, name, func, self.data): name
                for name, func in analyzers.items()
            }

            for future in as_completed(futures):
                name, result, elapsed = future.result()
                self.results[f'{analysis_type}_{name}'] = result
                self.execution_times[f'{analysis_type}_{name}'] = elapsed

    def _analyze_temporal_clusters(self):
        from collections import defaultdict

        temporal_clusters = defaultdict(list)
        data_to_analyze = self.normalized_data if self.normalized_data else self.data

        for item in data_to_analyze:
            discovered_at = item.get('discovered_at')
            if discovered_at:
                dt = datetime.fromtimestamp(discovered_at)
                window = dt.replace(second=0, microsecond=0)
                window_5min = window.replace(minute=(window.minute // 5) * 5)
                temporal_clusters[window_5min].append(item)

        cluster_analysis = []
        for window, urls in temporal_clusters.items():
            if len(urls) >= 10:
                cluster_analysis.append({
                    'window': window.isoformat(),
                    'url_count': len(urls),
                    'avg_depth': sum(u.get('depth', 0) for u in urls) / len(urls),
                    'unique_parents': len(set(u.get('parent_url') for u in urls if u.get('parent_url')))
                })

        cluster_analysis.sort(key=lambda x: x['url_count'], reverse=True)

        self.results['temporal_clusters'] = {
            'total_clusters': len(temporal_clusters),
            'significant_clusters': len(cluster_analysis),
            'clusters': cluster_analysis[:20]
        }

    def _analyze_parent_child_relationships(self):
        from collections import defaultdict

        parent_children = defaultdict(list)
        child_parent = {}
        data_to_analyze = self.normalized_data if self.normalized_data else self.data

        for item in data_to_analyze:
            url = item['url']
            parent = item.get('parent_url')

            if parent:
                parent_children[parent].append(url)
                child_parent[url] = parent

        relationship_analysis = {
            'total_urls': len(data_to_analyze),
            'urls_with_parents': len(child_parent),
            'unique_parents': len(parent_children),
            'orphan_urls': len(data_to_analyze) - len(child_parent),
            'avg_children_per_parent': len(child_parent) / len(parent_children) if parent_children else 0,
            'max_children': max((len(children) for children in parent_children.values()), default=0)
        }

        parent_counts = [(parent, len(children)) for parent, children in parent_children.items()]
        parent_counts.sort(key=lambda x: x[1], reverse=True)

        relationship_analysis['top_parents'] = [
            {'url': parent, 'children_count': count}
            for parent, count in parent_counts[:20]
        ]

        self.results['parent_child_relationships'] = relationship_analysis

    def execute(self) -> Dict:
        self.logger.info("Starting master analysis pipeline")
        self.logger.info("Input file: %s", self.input_file)
        self.logger.info("Output directory: %s", self.output_dir)
        self.logger.info("Data configuration: %s", self.config.get('data', {}))

        if not self.load_data():
            return None

        total_start = time.time()

        self.run_basic_analysis()
        self.run_enhanced_analysis()
        self.run_mlx_analysis()

        total_elapsed = time.time() - total_start

        self.results['metadata'] = {
            'input_file': self.input_file,
            'total_urls': len(self.data),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_execution_time': total_elapsed,
            'execution_times': self.execution_times,
            'config': self.config
        }

        return self.results

    def save_results(self, subdir: str = ''):
        output_path = Path(self.output_dir) / subdir if subdir else Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.logger.info("Saving results to %s", output_path)

        results_file = output_path / 'analysis_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, cls=NumpyEncoder)
        self.logger.info("Full results written to %s", results_file)

        if self.config['output']['save_individual_results']:
            for key, result in self.results.items():
                if key not in ['metadata', 'insights']:
                    result_file = output_path / f'{key}_results.json'
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, cls=NumpyEncoder)

        self._save_summary_report(output_path)

    def _save_summary_report(self, output_path: Path):
        report_file = output_path / 'analysis_report.txt'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("URL ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")

            meta = self.results.get('metadata', {})
            f.write(f"Input File: {meta.get('input_file', 'N/A')}\n")
            f.write(f"Total URLs: {meta.get('total_urls', 0):,}\n")
            f.write(f"Analysis Date: {meta.get('analysis_timestamp', 'N/A')}\n")
            f.write(f"Execution Time: {meta.get('total_execution_time', 0):.2f}s\n")
            f.write("\n")

            for key, value in self.results.items():
                if key not in ['metadata', 'insights'] and isinstance(value, dict):
                    if 'error' not in value:
                        f.write(f"\n{key.upper()}\n")
                        f.write("-" * 80 + "\n")
                        f.write(f"Analysis completed successfully\n")

        self.logger.info("Summary report written to %s", report_file)

    def format_summary(self) -> str:
        """Create a plain-text summary of completed analyses."""
        meta = self.results.get('metadata', {})
        lines = [
            "Analysis Summary",
            f"Input File: {meta.get('input_file', 'N/A')}",
            f"Total URLs Analyzed: {meta.get('total_urls', 0):,}",
            f"Total Execution Time: {meta.get('total_execution_time', 0):.2f}s",
            "",
            "Completed Analyses:"
        ]

        for key, value in self.results.items():
            if key in {'metadata', 'insights'}:
                continue
            status = "ERROR"
            if isinstance(value, dict):
                status = "ERROR" if value.get('error') else "OK"
            else:
                status = "OK"
            lines.append(f"- {key}: {status}")

        return "\n".join(lines).strip()

    def write_summary(self, destination: Optional[Path] = None) -> Path:
        """Persist the human-readable summary to disk."""
        summary_text = self.format_summary()
        dest_path = Path(destination) if destination else Path(self.output_dir) / "SUMMARY" / "pipeline_summary.txt"
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(summary_text + "\n", encoding='utf-8')
        self.logger.info("Pipeline summary saved to %s", dest_path)
        return dest_path


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python master_pipeline.py <input_jsonl_file> [output_dir] [config_path]\n")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    config_path = sys.argv[3] if len(sys.argv) > 3 else 'global.yml'

    pipeline = MasterPipeline(input_file, output_dir, config_path)
    results = pipeline.execute()

    if results:
        pipeline.save_results()
        summary_path = pipeline.write_summary()
        pipeline.logger.info("Analysis complete. Results saved to %s", pipeline.output_dir)
        pipeline.logger.info("Summary available at %s", summary_path)
    else:
        pipeline.logger.error("Analysis failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
