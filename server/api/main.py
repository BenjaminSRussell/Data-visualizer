"""
fastapi wiring for analysis outputs and health checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

DEFAULT_OUTPUT_ROOT = Path("analysis/output")


def load_summary(output_root: Path) -> Dict[str, Any]:
    """load aggregated summary if present."""
    summary_path = output_root / "SUMMARY" / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found at {summary_path}")

    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def create_app(output_root: Path = DEFAULT_OUTPUT_ROOT) -> FastAPI:
    """build app with configurable output paths."""
    app = FastAPI(
        title="URL Analysis Platform",
        version="1.0.0",
        description="REST interface for analysis outputs and operational status.",
    )

    @app.get("/health", tags=["System"])
    async def health_check() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/summary", tags=["Results"])
    async def summary() -> Dict[str, Any]:
        try:
            return load_summary(output_root)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/summary/{pipeline_name}", tags=["Results"])
    async def pipeline_summary(pipeline_name: str) -> Dict[str, Any]:
        try:
            summary_payload = load_summary(output_root)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        for snapshot in summary_payload.get("snapshots", []):
            if snapshot.get("pipeline") == pipeline_name:
                return snapshot

        raise HTTPException(status_code=404, detail=f"No snapshot for pipeline '{pipeline_name}'.")

    return app


app = create_app()
