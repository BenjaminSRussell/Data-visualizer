"""Coordinate the analysis pipeline across analyzers and output writers."""
from __future__ import annotations

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Settings, get_settings
from analysis.analyzers import network_analyzer, semantic_path_analyzer, statistical_analyzer
from analysis.analyzers import subdomain_analyzer, url_component_parser
from analysis.mappers import pathway_mapper

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

AnalyzerCallable = Callable[[List[Dict[str, Any]]], Dict[str, Any]]
ANALYZERS: Dict[str, AnalyzerCallable] = {
    "statistical": statistical_analyzer.execute,
    "network": network_analyzer.execute,
    "semantic_path": semantic_path_analyzer.execute,
    "pathway": pathway_mapper.execute,
    "subdomain": subdomain_analyzer.execute,
    "url_components": url_component_parser.execute,
}


class NumpyEncoder(json.JSONEncoder):
    """Serialize NumPy values so json.dump can persist analyzer output."""

    def default(self, obj: Any) -> Any:
        import numpy as np

        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


class MasterPipeline:
    """Orchestrate end-to-end URL analysis for a JSONL dataset."""

    def __init__(
        self,
        input_file: str,
        output_dir: Optional[str] = None,
        config_path: Optional[str] = None,
        *,
        settings: Optional[Settings] = None,
    ) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.addHandler(logging.NullHandler())

        self.settings = settings or get_settings()
        self.config_path = Path(config_path) if config_path else self.settings.global_config_path
        self.config = self._load_config(self.config_path)

        self.input_path = Path(input_file)
        self.input_file = str(self.input_path)
        configured_output = Path(output_dir) if output_dir else self.settings.data.output_dir
        self.output_dir = configured_output

        self.data: List[Dict[str, Any]] = []
        self.normalized_data: List[Dict[str, Any]] = []
        self.results: Dict[str, Any] = {}
        self.execution_times: Dict[str, float] = {}

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure a file-based logger for pipeline messages."""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "master_pipeline.log"

        has_handler = any(
            isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_file
            for handler in self.logger.handlers
        )

        if not has_handler:
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            self.logger.addHandler(handler)

        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            self.logger.warning("Config file %s not found. Using defaults.", path)
            return self._default_config()

        try:
            with path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            self.logger.error("Invalid YAML in %s: %s. Using defaults.", path, exc)
            return self._default_config()
        except OSError as exc:
            self.logger.error("Unable to read %s: %s. Using defaults.", path, exc)
            return self._default_config()

        return self._merge_defaults(loaded)

    def _default_config(self) -> Dict[str, Any]:
        return {
            "data": {"output_dir": str(self.settings.data.output_dir)},
            "analysis": {
                "types": {
                    "basic": {
                        "enabled": True,
                        "analyzers": ["statistical", "network", "semantic_path", "pathway"],
                    },
                    "enhanced": {
                        "enabled": True,
                        "analyzers": ["subdomain", "url_components"],
                    },
                    "mlx": {"enabled": False},
                }
            },
            "performance": {"max_workers": self.settings.performance.max_workers},
            "output": {
                "save_individual_results": self.settings.output.save_individual_results,
                "summary_dir": str(self.settings.output.summary_dir),
            },
            "normalization": {
                "remove_fragments": self.settings.normalization.remove_fragments,
                "merge_metadata": self.settings.normalization.merge_metadata,
            },
            "mlx": {
                "embedding_dim": 128,
                "training_epochs": 3,
                "window_size": 3,
                "temporal_window_minutes": 5,
            },
        }

    def _merge_defaults(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        defaults = self._default_config()
        return self._deep_merge(defaults, loaded)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = MasterPipeline._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _analysis_config(self, tier: str) -> Dict[str, Any]:
        return (
            self.config.get("analysis", {})
            .get("types", {})
            .get(tier, {})
        ) or {}

    def load_data(self) -> bool:
        self.logger.info("Loading data from %s", self.input_file)

        if not self.input_path.exists():
            self.logger.error("Input file %s not found.", self.input_file)
            return False

        try:
            with self.input_path.open("r", encoding="utf-8") as handle:
                for line_num, line in enumerate(handle, start=1):
                    entry = line.strip()
                    if not entry:
                        continue

                    try:
                        record: Any = json.loads(entry)
                    except json.JSONDecodeError as exc:
                        self.logger.warning("Line %s is not valid JSON: %s", line_num, exc)
                        continue

                    normalized = self._normalize_record(record, line_num)
                    if normalized is not None:
                        self.data.append(normalized)

            self.logger.info("Loaded %s URLs", f"{len(self.data):,}")
            return True

        except OSError as exc:
            self.logger.error("Failed to read %s: %s", self.input_file, exc)
            return False

    def _normalize_record(self, record: Any, line_num: int) -> Optional[Dict[str, Any]]:
        if isinstance(record, dict):
            if record.get("url"):
                return record
            self.logger.warning("Line %s missing 'url' field.", line_num)
            return None

        if isinstance(record, str) and record:
            return {"url": record}

        self.logger.warning("Line %s has unsupported payload type: %s", line_num, type(record).__name__)
        return None

    def _select_analyzers(self, names: List[str]) -> Dict[str, AnalyzerCallable]:
        selected: Dict[str, AnalyzerCallable] = {}
        for name in names:
            func = ANALYZERS.get(name)
            if func:
                selected[name] = func
            else:
                self.logger.warning("Analyzer %s is not registered.", name)
        return selected

    def run_analyzer(
        self,
        name: str,
        func: AnalyzerCallable,
        data: List[Dict[str, Any]],
    ) -> Tuple[str, Dict[str, Any], float]:
        self.logger.info("Running analyzer: %s", name)
        start_time = time.time()

        try:
            result = func(data)
        except Exception as exc:  # noqa: BLE001 - analyzers may raise arbitrary exceptions
            # Analyzer plugins vary widely; capture the failure instead of crashing the pipeline.
            self.logger.exception("Analyzer %s failed", name)
            return name, {"error": str(exc)}, 0.0

        elapsed = time.time() - start_time
        self.logger.info("Analyzer %s completed in %.2fs", name, elapsed)
        return name, result, elapsed

    def run_basic_analysis(self) -> None:
        basic_cfg = self._analysis_config("basic")
        if not basic_cfg.get("enabled", True):
            return

        analyzers = self._select_analyzers(basic_cfg.get("analyzers", []))
        if not analyzers:
            self.logger.info("Basic analysis skipped because no analyzers are configured.")
            return

        self.logger.info("Starting basic analysis")
        self._run_analyzers(analyzers, "basic")

    def run_enhanced_analysis(self) -> None:
        enhanced_cfg = self._analysis_config("enhanced")
        if not enhanced_cfg.get("enabled", True):
            return

        analyzers = self._select_analyzers(enhanced_cfg.get("analyzers", []))
        if not analyzers:
            self.logger.info("Enhanced analysis skipped because no analyzers are configured.")
            return

        self.logger.info("Starting enhanced analysis")
        self._run_analyzers(analyzers, "enhanced")

    def run_mlx_analysis(self) -> None:
        """Run pattern recognition analysis (MLX ML components removed)."""
        mlx_cfg = self._analysis_config("mlx")
        if not mlx_cfg.get("enabled"):
            return

        self.logger.info("Starting pattern recognition analysis")

        try:
            from analysis.url_normalizer import URLNormalizer
            from analysis.pattern_recognition import PatternRecognizer
        except ImportError as exc:
            self.logger.warning("Pattern recognition dependencies not available: %s", exc)
            self.results["mlx"] = {"error": "Pattern recognition modules not found"}
            return

        # Normalize URLs (optional preprocessing)
        normalization_cfg = self.config.get("normalization", {})
        remove_fragments = normalization_cfg.get(
            "remove_fragments",
            self.settings.normalization.remove_fragments,
        )
        merge_metadata = normalization_cfg.get(
            "merge_metadata",
            self.settings.normalization.merge_metadata,
        )

        normalizer = URLNormalizer()
        self.logger.info("Normalizing URLs")
        start_time = time.time()
        self.normalized_data = normalizer.normalize_batch(
            self.data,
            remove_fragments=remove_fragments,
            merge_metadata=merge_metadata,
        )
        self.results["normalization"] = normalizer.get_stats()
        self.execution_times["normalization"] = time.time() - start_time

        # Run pattern recognition (pure regex, no ML)
        self.logger.info("Analyzing URL patterns")
        pattern_recognizer = PatternRecognizer()
        start_time = time.time()
        self.results["patterns"] = pattern_recognizer.analyze_patterns(self.normalized_data)
        self.execution_times["pattern_recognition"] = time.time() - start_time

    def _run_analyzers(self, analyzers: Dict[str, AnalyzerCallable], analysis_type: str) -> None:
        if not analyzers:
            return

        max_workers = max(
            1,
            int(
                self.config.get("performance", {}).get(
                    "max_workers",
                    self.settings.performance.max_workers,
                )
            ),
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.run_analyzer, name, func, self.data): name
                for name, func in analyzers.items()
            }

            for future in as_completed(futures):
                name, result, elapsed = future.result()
                self.results[f"{analysis_type}_{name}"] = result
                self.execution_times[f"{analysis_type}_{name}"] = elapsed

    def _analyze_temporal_clusters(self) -> None:
        from collections import defaultdict

        temporal_clusters: Dict[datetime, List[Dict[str, Any]]] = defaultdict(list)
        data_to_analyze = self.normalized_data if self.normalized_data else self.data
        window_minutes = max(1, int(self.config.get("mlx", {}).get("temporal_window_minutes", 5)))

        for item in data_to_analyze:
            discovered_at = item.get("discovered_at")
            if not discovered_at:
                continue

            try:
                timestamp = float(discovered_at)
            except (TypeError, ValueError):
                continue

            dt = datetime.fromtimestamp(timestamp)
            window = dt.replace(second=0, microsecond=0)
            minute_bucket = (window.minute // window_minutes) * window_minutes
            window_bucket = window.replace(minute=minute_bucket)
            temporal_clusters[window_bucket].append(item)

        cluster_analysis: List[Dict[str, Any]] = []
        for window_bucket, urls in temporal_clusters.items():
            if len(urls) < 10:
                continue

            avg_depth = sum(url.get("depth", 0) for url in urls) / len(urls)
            unique_parents = len(
                {url.get("parent_url") for url in urls if url.get("parent_url")}
            )

            cluster_analysis.append(
                {
                    "window": window_bucket.isoformat(),
                    "url_count": len(urls),
                    "avg_depth": avg_depth,
                    "unique_parents": unique_parents,
                }
            )

        cluster_analysis.sort(key=lambda entry: entry["url_count"], reverse=True)

        self.results["temporal_clusters"] = {
            "total_clusters": len(temporal_clusters),
            "significant_clusters": len(cluster_analysis),
            "clusters": cluster_analysis[:20],
        }

    def _analyze_parent_child_relationships(self) -> None:
        from collections import defaultdict

        parent_children: Dict[str, List[str]] = defaultdict(list)
        child_parent: Dict[str, str] = {}
        data_to_analyze = self.normalized_data if self.normalized_data else self.data

        for item in data_to_analyze:
            url = item.get("url")
            parent = item.get("parent_url")

            if not url or not parent:
                continue

            parent_children[parent].append(url)
            child_parent[url] = parent

        total_urls = len(data_to_analyze)
        unique_parents = len(parent_children)
        avg_children = len(child_parent) / unique_parents if unique_parents else 0.0
        max_children = max((len(children) for children in parent_children.values()), default=0)

        parent_counts = sorted(parent_children.items(), key=lambda entry: len(entry[1]), reverse=True)

        self.results["parent_child_relationships"] = {
            "total_urls": total_urls,
            "urls_with_parents": len(child_parent),
            "unique_parents": unique_parents,
            "orphan_urls": total_urls - len(child_parent),
            "avg_children_per_parent": avg_children,
            "max_children": max_children,
            "top_parents": [
                {"url": parent, "children_count": len(children)}
                for parent, children in parent_counts[:20]
            ],
        }

    def execute(self) -> Optional[Dict[str, Any]]:
        self.logger.info("Starting master analysis pipeline")
        self.logger.info("Input file: %s", self.input_file)
        self.logger.info("Output directory: %s", self.output_dir)

        if not self.load_data():
            return None

        total_start = time.time()

        self.run_basic_analysis()
        self.run_enhanced_analysis()
        self.run_mlx_analysis()

        total_elapsed = time.time() - total_start

        self.results["metadata"] = {
            "input_file": self.input_file,
            "total_urls": len(self.data),
            "analysis_timestamp": datetime.now().isoformat(),
            "total_execution_time": total_elapsed,
            "execution_times": self.execution_times,
            "config": self.config,
        }

        return self.results

    def save_results(self, subdir: str = "") -> None:
        output_path = self.output_dir / subdir if subdir else self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        self.logger.info("Saving results to %s", output_path)

        results_file = output_path / "analysis_results.json"
        with results_file.open("w", encoding="utf-8") as handle:
            json.dump(self.results, handle, indent=2, cls=NumpyEncoder)
        self.logger.info("Full results written to %s", results_file)

        save_individual = self.config.get("output", {}).get(
            "save_individual_results",
            self.settings.output.save_individual_results,
        )

        if save_individual:
            for key, result in self.results.items():
                if key in {"metadata", "insights"}:
                    continue
                result_file = output_path / f"{key}_results.json"
                with result_file.open("w", encoding="utf-8") as handle:
                    json.dump(result, handle, indent=2, cls=NumpyEncoder)

        self._save_summary_report(output_path)

    def _save_summary_report(self, output_path: Path) -> None:
        report_file = output_path / "analysis_report.txt"

        with report_file.open("w", encoding="utf-8") as handle:
            handle.write("=" * 80 + "\n")
            handle.write("URL ANALYSIS REPORT\n")
            handle.write("=" * 80 + "\n\n")

            meta = self.results.get("metadata", {})
            handle.write(f"Input File: {meta.get('input_file', 'N/A')}\n")
            handle.write(f"Total URLs: {meta.get('total_urls', 0):,}\n")
            handle.write(f"Analysis Date: {meta.get('analysis_timestamp', 'N/A')}\n")
            handle.write(f"Execution Time: {meta.get('total_execution_time', 0.0):.2f}s\n\n")

            for key, value in self.results.items():
                if key in {"metadata", "insights"} or not isinstance(value, dict):
                    continue
                if value.get("error"):
                    continue
                handle.write(f"\n{key.upper()}\n")
                handle.write("-" * 80 + "\n")
                handle.write("Analysis completed successfully\n")

        self.logger.info("Summary report written to %s", report_file)

    def format_summary(self) -> str:
        meta = self.results.get("metadata", {})
        lines = [
            "Analysis Summary",
            f"Input File: {meta.get('input_file', 'N/A')}",
            f"Total URLs Analyzed: {meta.get('total_urls', 0):,}",
            f"Total Execution Time: {meta.get('total_execution_time', 0.0):.2f}s",
            "",
            "Completed Analyses:",
        ]

        for key, value in self.results.items():
            if key in {"metadata", "insights"}:
                continue
            status = "ERROR"
            if isinstance(value, dict):
                status = "ERROR" if value.get("error") else "OK"
            else:
                status = "OK"
            lines.append(f"- {key}: {status}")

        return "\n".join(lines).strip()

    def write_summary(self, destination: Optional[Path] = None) -> Path:
        summary_text = self.format_summary()

        if destination is None:
            summary_dir_value = self.config.get("output", {}).get(
                "summary_dir",
                str(self.settings.output.summary_dir),
            )
            summary_dir = Path(summary_dir_value)
            if not summary_dir.is_absolute():
                summary_dir = self.output_dir / summary_dir
            summary_dir.mkdir(parents=True, exist_ok=True)
            dest_path = summary_dir / "pipeline_summary.txt"
        else:
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

        dest_path.write_text(summary_text + "\n", encoding="utf-8")
        self.logger.info("Pipeline summary saved to %s", dest_path)
        return dest_path


def main() -> None:
    if len(sys.argv) < 2:
        sys.stderr.write(
            "Usage: python master_pipeline.py <input_jsonl_file> [output_dir] [config_path]\n"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    config_path = sys.argv[3] if len(sys.argv) > 3 else None

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


if __name__ == "__main__":
    main()
