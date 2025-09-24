"""
Configuration module for NL-SQL Agent.

Contains configuration data structures for query categorization,
suggestion patterns, metrics tracking, chart type determination, SQL correction, and heuristic patterns.
"""

from .chart_type_rules import (
    CATEGORICAL_KEYWORDS,
    CHART_THRESHOLDS,
    LINE_CHART_KEYWORDS,
    PIE_CHART_KEYWORDS,
    SCATTER_CHART_KEYWORDS,
    TIME_KEYWORDS,
    TIME_PATTERNS,
)
from .heuristic_patterns import FALLBACK_QUERIES, HEURISTIC_PATTERNS
from .metrics_config import DEFAULT_METRICS_CONFIG
from .query_categories import QUERY_CATEGORIES
from .sql_correction_patterns import (
    AGGREGATE_FUNCTIONS,
    COMMON_AMBIGUOUS_COLUMNS,
    LEARNED_PATTERNS,
    SQL_PATTERNS,
    SQL_THRESHOLDS,
)
from .suggestion_patterns import GENERAL_SUGGESTIONS, SUGGESTION_PATTERNS
from .test_questions import TEST_CONFIG, TEST_QUESTIONS

__all__ = [
    "DEFAULT_METRICS_CONFIG",
    "FALLBACK_QUERIES",
    "GENERAL_SUGGESTIONS",
    "HEURISTIC_PATTERNS",
    "QUERY_CATEGORIES",
    "SUGGESTION_PATTERNS",
    "TEST_CONFIG",
    "TEST_QUESTIONS",
    "TIME_KEYWORDS",
    "LINE_CHART_KEYWORDS",
    "SCATTER_CHART_KEYWORDS",
    "PIE_CHART_KEYWORDS",
    "TIME_PATTERNS",
    "CATEGORICAL_KEYWORDS",
    "CHART_THRESHOLDS",
    "COMMON_AMBIGUOUS_COLUMNS",
    "AGGREGATE_FUNCTIONS",
    "LEARNED_PATTERNS",
    "SQL_PATTERNS",
    "SQL_THRESHOLDS",
]
