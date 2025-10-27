from .metadata import execute as extract_metadata
from .text import execute as extract_text
from .features import execute as extract_features

__all__ = ["extract_metadata", "extract_text", "extract_features"]
