"""Configuration utilities with environment-driven overrides."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a float.") from exc


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise ValueError(f"Environment variable {name} must be a boolean.")


@dataclass(frozen=True)
class DataSettings:
    input_dir: Path
    output_dir: Path


@dataclass(frozen=True)
class URLSourceSettings:
    baseline_file: Path
    current_file: Path


@dataclass(frozen=True)
class PerformanceSettings:
    max_workers: int
    request_timeout_seconds: float
    batch_size: int


@dataclass(frozen=True)
class RetrySettings:
    max_retries: int


@dataclass(frozen=True)
class ThresholdSettings:
    duplicate_percent: float
    statistical_outlier: float
    network_cluster_threshold: float
    response_time_warning_ms: float


@dataclass(frozen=True)
class NormalizationSettings:
    remove_fragments: bool
    merge_metadata: bool


@dataclass(frozen=True)
class OutputSettings:
    summary_dir: Path
    save_individual_results: bool


@dataclass(frozen=True)
class Settings:
    data: DataSettings
    urls: URLSourceSettings
    performance: PerformanceSettings
    retries: RetrySettings
    thresholds: ThresholdSettings
    normalization: NormalizationSettings
    output: OutputSettings
    global_config_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings assembled from defaults and environment overrides."""
    return Settings(
        data=DataSettings(
            input_dir=_resolve_path(_env_str("ANALYSIS_INPUT_DIR", "data/input")),
            output_dir=_resolve_path(_env_str("ANALYSIS_OUTPUT_DIR", "data/output")),
        ),
        urls=URLSourceSettings(
            baseline_file=_resolve_path(_env_str("ANALYSIS_BASELINE_FILE", "data/input/site_01.jsonl")),
            current_file=_resolve_path(_env_str("ANALYSIS_CURRENT_FILE", "data/input/site_02.jsonl")),
        ),
        performance=PerformanceSettings(
            max_workers=_env_int("ANALYSIS_MAX_WORKERS", 6),
            request_timeout_seconds=_env_float("ANALYSIS_REQUEST_TIMEOUT_SECONDS", 30.0),
            batch_size=_env_int("ANALYSIS_BATCH_SIZE", 1000),
        ),
        retries=RetrySettings(max_retries=_env_int("ANALYSIS_MAX_RETRIES", 3)),
        thresholds=ThresholdSettings(
            duplicate_percent=_env_float("ANALYSIS_DUPLICATE_PERCENT", 60.0),
            statistical_outlier=_env_float("ANALYSIS_STATISTICAL_OUTLIER", 3.0),
            network_cluster_threshold=_env_float("ANALYSIS_NETWORK_CLUSTER_THRESHOLD", 0.5),
            response_time_warning_ms=_env_float("ANALYSIS_RESPONSE_TIME_WARNING_MS", 2_000.0),
        ),
        normalization=NormalizationSettings(
            remove_fragments=_env_bool("ANALYSIS_REMOVE_FRAGMENTS", True),
            merge_metadata=_env_bool("ANALYSIS_MERGE_METADATA", True),
        ),
        output=OutputSettings(
            summary_dir=_resolve_path(_env_str("ANALYSIS_SUMMARY_DIR", "SUMMARY")),
            save_individual_results=_env_bool("ANALYSIS_SAVE_INDIVIDUAL_RESULTS", True),
        ),
        global_config_path=_resolve_path(_env_str("ANALYSIS_GLOBAL_CONFIG", "global.yml")),
    )


__all__ = ["Settings", "get_settings"]
