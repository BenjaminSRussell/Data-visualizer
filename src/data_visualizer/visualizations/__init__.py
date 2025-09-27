"""Visualization registry and discovery utilities."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from .base import Visualization, VisualizationMetadata


def iter_visualization_modules() -> Iterable[str]:
    """Yield fully qualified module names for bundled visualizations."""

    package = __name__
    prefix = f"{package}."
    for module_info in pkgutil.walk_packages(__path__, prefix):
        if module_info.ispkg:
            continue
        yield module_info.name


def load_visualization(key: str) -> type[Visualization]:
    """Load a visualization class by its metadata key."""

    for module_name in iter_visualization_modules():
        module = importlib.import_module(module_name)
        for attribute in module.__dict__.values():
            if isinstance(attribute, type) and issubclass(attribute, Visualization):
                if getattr(attribute, "metadata", None) and attribute.metadata.key == key:
                    return attribute
    raise KeyError(f"Visualization not found for key: {key}")


def list_visualizations() -> list[VisualizationMetadata]:
    """Return metadata for all available visualizations."""

    seen: dict[str, VisualizationMetadata] = {}
    for module_name in iter_visualization_modules():
        module = importlib.import_module(module_name)
        for attribute in module.__dict__.values():
            if isinstance(attribute, type) and issubclass(attribute, Visualization):
                metadata = getattr(attribute, "metadata", None)
                if metadata and metadata.key not in seen:
                    seen[metadata.key] = metadata
    return sorted(seen.values(), key=lambda m: m.title.lower())


__all__ = [
    "Visualization",
    "VisualizationMetadata",
    "load_visualization",
    "list_visualizations",
]
