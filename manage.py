#!/usr/bin/env python3
"""
management cli helpers for analysis workflows.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.console import Console

APP = typer.Typer(help="Utility commands for the data visualizer stack.")
CONSOLE = Console()
ROOT = Path(__file__).parent.resolve()
RUN_SCRIPT = ROOT / "run.sh"
SERVER_SCRIPT = ROOT / "server.sh"
OUTPUT_ROOT = ROOT / "analysis" / "output"
LEGACY_DIRS = [ROOT / "analysis" / "results", ROOT / "analysis" / "enhanced_results"]
DATABASE_FILE = ROOT / "url_analyzer.db"


def run_command(command: List[str], cwd: Optional[Path] = None) -> int:
    """run subprocess and stream output."""
    return subprocess.call(command, cwd=str(cwd or ROOT))


@APP.command()
def analyze(
    input_path: Path = typer.Option(Path("Site.jsonl"), "--input", "-i", exists=True, file_okay=True),
    output_dir: Path = typer.Option(OUTPUT_ROOT, "--output", "-o"),
    analysis_type: str = typer.Option("all", "--type", "-t", help="basic|enhanced|mlx|all"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip data quality checks"),
) -> None:
    """wrap run.sh analyze command."""
    command = [
        str(RUN_SCRIPT),
        "analyze",
        "--input",
        str(input_path),
        "--output",
        str(output_dir),
        "--type",
        analysis_type,
    ]
    if skip_validation:
        command.append("--skip-validation")

    CONSOLE.log("Executing analysis pipeline...")
    code = run_command(command)
    raise typer.Exit(code)


@APP.command()
def validate(input_path: Path = typer.Argument(..., exists=True, file_okay=True), strict: bool = typer.Option(False, "--strict")) -> None:
    """trigger jsonl data validation."""
    command = ["python3", "analysis/data_validator.py", str(input_path)]
    if strict:
        command.append("--strict")

    code = run_command(command)
    raise typer.Exit(code)


@APP.command()
def flush(
    outputs: bool = typer.Option(True, help="Remove analysis output directories."),
    database: bool = typer.Option(False, help="Delete local SQLite database file."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not prompt for confirmation."),
) -> None:
    """clear analysis artifacts and optional database."""
    if not yes:
        confirmed = typer.confirm("This will remove generated data. Continue?")
        if not confirmed:
            print("[yellow]Operation cancelled.[/yellow]")
            raise typer.Exit(code=0)

    if outputs:
        if OUTPUT_ROOT.exists():
            shutil.rmtree(OUTPUT_ROOT)
            print(f"[green]Removed output directory[/green] {OUTPUT_ROOT}")
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        for sub in ["basic", "enhanced", "mlx", "SUMMARY", "logs", "cache"]:
            (OUTPUT_ROOT / sub).mkdir(parents=True, exist_ok=True)
            (OUTPUT_ROOT / sub / ".gitkeep").touch()
        for legacy in LEGACY_DIRS:
            if legacy.exists():
                shutil.rmtree(legacy)
                print(f"[green]Removed legacy directory[/green] {legacy}")

    if database and DATABASE_FILE.exists():
        DATABASE_FILE.unlink()
        print(f"[green]Deleted database file[/green] {DATABASE_FILE}")

    print("[bold green]Flush complete.[/bold green]")


@APP.command()
def summary(output_dir: Path = typer.Option(OUTPUT_ROOT, "--output", "-o")) -> None:
    """build and print aggregated summary."""
    command = ["python3", "analysis/summary_aggregator.py", str(output_dir), "--print"]
    code = run_command(command)
    raise typer.Exit(code)


@APP.command()
def server(component: str = typer.Argument("api"), args: List[str] = typer.Argument(None)) -> None:
    """wrap server.sh for runtime control."""
    command = [str(SERVER_SCRIPT), component]
    if args:
        command.extend(args)
    code = run_command(command)
    raise typer.Exit(code)


if __name__ == "__main__":
    APP()
