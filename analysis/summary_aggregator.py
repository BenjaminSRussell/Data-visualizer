#!/usr/bin/env python3
"""
aggregate analysis outputs across pipelines and build summary reports.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ANALYSIS_TARGETS: Dict[str, Tuple[str, ...]] = {
    "basic": ("analysis_results.json",),
    "enhanced": ("enhanced_analysis_results.json",),
    "mlx": ("enhanced_results.json",),
}


@dataclass
class AnalysisSnapshot:
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    insights: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    path: Optional[Path] = None

    @property
    def total_urls(self) -> int:
        return int(self.metadata.get("total_urls", self.metadata.get("raw_urls", 0)))

    @property
    def timestamp(self) -> Optional[str]:
        return self.metadata.get("analysis_timestamp")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_snapshot(name: str, directory: Path) -> Optional[AnalysisSnapshot]:
    if not directory.exists():
        return None

    candidate: Optional[Path] = None
    for filename in ANALYSIS_TARGETS[name]:
        candidate_path = directory / filename
        if candidate_path.exists():
            candidate = candidate_path
            break

    if candidate is None:
        return None

    payload = load_json(candidate)
    metadata = payload.get("metadata", {})
    insights = payload.get("insights", {})

    # ensure timestamp exists
    if "analysis_timestamp" not in metadata:
        metadata["analysis_timestamp"] = datetime.now().isoformat()

    summary = {
        "key_findings": insights.get("key_findings", []),
        "alerts": insights.get("alerts", []),
        "scores": insights.get("scores", {}),
    }

    return AnalysisSnapshot(
        name=name,
        metadata=metadata,
        insights=insights,
        summary=summary,
        path=candidate,
    )


def build_markdown_report(snapshots: List[AnalysisSnapshot], aggregate: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Unified Analysis Summary\n")
    lines.append(f"_Generated: {aggregate['generated_at']}_\n")

    lines.append("## Overview\n")
    lines.append(f"- Total URLs analyzed: **{aggregate['totals']['urls']}**")
    lines.append(f"- Pipelines executed: **{', '.join(aggregate['pipelines'])}**")
    lines.append(f"- Alerts detected: **{aggregate['totals']['alerts']}**\n")

    if aggregate["highlights"]:
        lines.append("## Highlights\n")
        for highlight in aggregate["highlights"]:
            lines.append(f"- {highlight}")
        lines.append("")

    for snapshot in snapshots:
        lines.append(f"## {snapshot.name.title()} Analysis\n")
        metadata = snapshot.metadata
        lines.append(f"- Results path: `{snapshot.path}`")
        lines.append(f"- URLs processed: {snapshot.total_urls}")
        lines.append(f"- Generated: {metadata.get('analysis_timestamp', 'n/a')}")

        scores = snapshot.summary.get("scores") or {}
        if scores:
            score_bits = ", ".join(f"{k}: {v:.1f}" for k, v in scores.items() if isinstance(v, (int, float)))
            if score_bits:
                lines.append(f"- Scores: {score_bits}")

        key_findings = snapshot.summary.get("key_findings") or snapshot.insights.get("summary", {}).get("summary_points")
        if key_findings:
            lines.append("\n**Key Findings**")
            for finding in key_findings[:5]:
                lines.append(f"- {finding}")

        alerts = snapshot.summary.get("alerts")
        if alerts:
            lines.append("\n**Alerts**")
            for alert in alerts[:5]:
                lines.append(f"- ⚠️ {alert}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def aggregate_snapshots(snapshots: List[AnalysisSnapshot]) -> Dict[str, Any]:
    totals = {
        "urls": sum(snapshot.total_urls for snapshot in snapshots),
        "alerts": sum(len(snapshot.summary.get("alerts", [])) for snapshot in snapshots),
    }

    highlights: List[str] = []
    for snapshot in snapshots:
        key_findings = snapshot.summary.get("key_findings") or []
        highlights.extend(key_findings[:2])

    aggregate = {
        "generated_at": datetime.utcnow().isoformat(),
        "pipelines": [snapshot.name for snapshot in snapshots],
        "totals": totals,
        "highlights": highlights[:6],
        "snapshots": [
            {
                "pipeline": snapshot.name,
                "metadata": snapshot.metadata,
                "insights": snapshot.insights,
                "summary": snapshot.summary,
                "source": str(snapshot.path),
            }
            for snapshot in snapshots
        ],
    }

    return aggregate


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate analysis results into a unified report.")
    parser.add_argument(
        "output_root",
        nargs="?",
        default="analysis/output",
        help="Root output directory containing analysis runs.",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_stdout",
        help="Print aggregated summary to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    output_root = Path(args.output_root).resolve()

    if not output_root.exists():
        print(f"Output directory not found: {output_root}")
        return 1

    snapshots: List[AnalysisSnapshot] = []
    for name in ANALYSIS_TARGETS.keys():
        directory = output_root / name
        snapshot = extract_snapshot(name, directory)
        if snapshot:
            snapshots.append(snapshot)

    if not snapshots:
        print("No analysis results found to aggregate.")
        return 1

    aggregate = aggregate_snapshots(snapshots)

    summary_dir = output_root / "SUMMARY"
    summary_dir.mkdir(parents=True, exist_ok=True)

    # write JSON
    summary_json_path = summary_dir / "summary.json"
    with summary_json_path.open("w", encoding="utf-8") as handle:
        json.dump(aggregate, handle, indent=2)

    # write Markdown
    summary_md_path = summary_dir / "summary.md"
    report_text = build_markdown_report(snapshots, aggregate)
    summary_md_path.write_text(report_text, encoding="utf-8")

    if args.print_stdout:
        print(report_text)

    print(f"Summary generated: {summary_json_path}")
    print(f"Readable report:  {summary_md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
