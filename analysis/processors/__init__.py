# optional imports - may fail if dependencies not met
try:
    from .url_processor import execute as process_single_url
    from .batch_processor import execute as process_batch
    from .sitemap_processor import execute as process_sitemap
except ImportError:
    pass
from .patterns import execute as detect_patterns

__all__ = ["process_single_url", "process_batch", "process_sitemap", "detect_patterns"]
