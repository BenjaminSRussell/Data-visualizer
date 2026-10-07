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
    input_path: Path = typer.Option(
        Path("data/input/site_02.jsonl"), "--input", "-i", exists=True, file_okay=True
    ),
    output_dir: Path = typer.Option(OUTPUT_ROOT, "--output", "-o"),
    analysis_type: str = typer.Option("all", "--type", "-t", help="basic|enhanced|mlx|all"),
    skip_validation: bool = typer.Option(False, "--skip-validation"),
) -> None:
    """Run analysis pipeline"""
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
    raise typer.Exit(run_command(command))


@APP.command()
def validate(
    input_path: Path = typer.Argument(..., exists=True, file_okay=True),
    strict: bool = typer.Option(False, "--strict"),
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




@APP.command()
def migrate(
    database_url: Optional[str] = typer.Option(
        None,
        "--database-url",
        help="Postgres URL (default DATABASE_URL or postgresql:///data_visualizer)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print pending versions only"),
) -> None:
    """Apply versioned SQL migrations under database/migrations/ (#25)."""
    import os
    import re

    try:
        import psycopg2
    except ImportError as exc:
        typer.echo("psycopg2 required: pip install psycopg2-binary", err=True)
        raise typer.Exit(1) from exc

    url = database_url or os.environ.get("DATABASE_URL") or "postgresql:///data_visualizer"
    # Simple URL parse for psycopg2: postgresql://user:pass@host:port/db or postgresql:///db
    migrations_dir = ROOT / "database" / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        typer.echo("No migrations found")
        raise typer.Exit(1)

    def version_of(path: Path) -> str:
        return path.stem  # e.g. 0001_initial

    pending = [f for f in files]
    if dry_run:
        typer.echo("Migration files:")
        for f in pending:
            typer.echo(f"  {version_of(f)}")
        raise typer.Exit(0)

    conn = psycopg2.connect(url)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(64) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute("SELECT version FROM schema_migrations")
            applied = {row[0] for row in cur.fetchall()}
        conn.commit()

        for path in pending:
            ver = version_of(path)
            if ver in applied or ver.startswith("0000_"):
                # 0000 is embedded above; skip duplicate file apply if present
                if ver.startswith("0000_"):
                    continue
                if ver in applied:
                    typer.echo(f"skip {ver}")
                    continue
            sql = path.read_text(encoding="utf-8")
            typer.echo(f"apply {ver}...")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations(version) VALUES (%s) ON CONFLICT DO NOTHING",
                    (ver,),
                )
            conn.commit()
            typer.echo(f"applied {ver}")
        typer.echo("migrate complete")
    except Exception as exc:
        conn.rollback()
        typer.echo(f"migrate failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    finally:
        conn.close()


if __name__ == "__main__":
    APP()
