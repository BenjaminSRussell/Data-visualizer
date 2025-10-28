#!/usr/bin/env python3

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import typer

APP = typer.Typer(help="Data visualizer management CLI")
ROOT = Path(__file__).parent.resolve()
RUN_SCRIPT = ROOT / "run.sh"
OUTPUT_ROOT = ROOT / "data" / "output"
LEGACY_DIRS = [ROOT / "analysis" / "results", ROOT / "analysis" / "enhanced_results"]
DATABASE_FILE = ROOT / "url_analyzer.db"


def run_command(command: List[str], cwd: Optional[Path] = None) -> int:
    return subprocess.call(command, cwd=str(cwd or ROOT))


@APP.command()
def analyze(
    input_path: Path = typer.Option(Path("data/input/site_02.jsonl"), "--input", "-i", exists=True, file_okay=True),
    output_dir: Path = typer.Option(OUTPUT_ROOT, "--output", "-o"),
    analysis_type: str = typer.Option("all", "--type", "-t", help="basic|enhanced|mlx|all"),
    skip_validation: bool = typer.Option(False, "--skip-validation"),
) -> None:
    """Run analysis pipeline"""
    command = [str(RUN_SCRIPT), "analyze", "--input", str(input_path), "--output", str(output_dir), "--type", analysis_type]
    if skip_validation:
        command.append("--skip-validation")
    raise typer.Exit(run_command(command))


@APP.command()
def validate(
    input_path: Path = typer.Argument(..., exists=True, file_okay=True),
    strict: bool = typer.Option(False, "--strict")
) -> None:
    """Validate JSONL data"""
    command = ["python3", "analysis/data_validator.py", str(input_path)]
    if strict:
        command.append("--strict")
    raise typer.Exit(run_command(command))


@APP.command()
def flush(
    outputs: bool = typer.Option(True, help="Remove output directories"),
    database: bool = typer.Option(False, help="Delete database file"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Clear analysis artifacts"""
    if not yes and not typer.confirm("Remove generated data?"):
        typer.echo("Cancelled")
        raise typer.Exit(0)

    if outputs:
        if OUTPUT_ROOT.exists():
            shutil.rmtree(OUTPUT_ROOT)
            typer.echo(f"Removed {OUTPUT_ROOT}")
        else:
            typer.echo(f"{OUTPUT_ROOT} not found")

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        for sub in ["basic", "enhanced", "mlx", "SUMMARY", "logs", "cache"]:
            (OUTPUT_ROOT / sub).mkdir(parents=True, exist_ok=True)
            (OUTPUT_ROOT / sub / ".gitkeep").touch()

        for legacy in LEGACY_DIRS:
            if legacy.exists():
                shutil.rmtree(legacy)
                typer.echo(f"Removed {legacy}")
            else:
                typer.echo(f"{legacy} not found")

    if database:
        if DATABASE_FILE.exists():
            DATABASE_FILE.unlink()
            typer.echo(f"Deleted {DATABASE_FILE}")
        else:
            typer.echo(f"{DATABASE_FILE} not found")

    typer.echo("Flush complete")


@APP.command()
def summary(output_dir: Path = typer.Option(OUTPUT_ROOT, "--output", "-o")) -> None:
    """Generate aggregated summary"""
    command = ["python3", "analysis/summary_aggregator.py", str(output_dir), "--print"]
    raise typer.Exit(run_command(command))


if __name__ == "__main__":
    APP()
