"""
Configuration module for NL-SQL Agent.

Contains configuration data structures for query categorization,
suggestion patterns, and metrics tracking.
"""

from .metrics_config import DEFAULT_METRICS_CONFIG
from .query_categories import QUERY_CATEGORIES
from .suggestion_patterns import GENERAL_SUGGESTIONS, SUGGESTION_PATTERNS

__all__ = [
    "DEFAULT_METRICS_CONFIG",
    "GENERAL_SUGGESTIONS",
    "QUERY_CATEGORIES",
    "SUGGESTION_PATTERNS",
]
