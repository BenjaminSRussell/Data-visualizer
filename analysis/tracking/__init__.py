"""
Performance Tracking Module

Track scraper performance metrics over time and identify trends.
"""

from .metrics_tracker import MetricsTracker, create_tracker

__all__ = ['MetricsTracker', 'create_tracker']
