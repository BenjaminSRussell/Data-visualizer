"""Base classes and helpers for visualization modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd


@dataclass(frozen=True)
class VisualizationMetadata:
    """Describes a visualization entry for documentation and discovery."""

    key: str
    title: str
    insight_type: str
    description: str
    example_url: str
    tags: tuple[str, ...] = ()


class Visualization(ABC):
    """Minimal interface that every visualization module must implement."""

    metadata: VisualizationMetadata

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}

    @abstractmethod
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a dataframe suited for plotting (override when needed)."""

    @abstractmethod
    def render(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Produce the visualization and return the output path."""

    def run(self, df: pd.DataFrame, output_dir: Path) -> Path:
        """Execute the visualization end-to-end."""

        output_dir.mkdir(parents=True, exist_ok=True)
        processed = self.prepare_data(df)
        filename = f"{self.metadata.key}.png"
        output_path = output_dir / filename
        return self.render(processed, output_path)
