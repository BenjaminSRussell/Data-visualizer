from .urls import execute as save_url
from .metadata import execute as save_metadata
from .classifications import execute as save_classification

__all__ = ["save_url", "save_metadata", "save_classification"]
