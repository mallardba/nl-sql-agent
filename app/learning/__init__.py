"""
Learning and metrics modules.

This package contains modules for query categorization, metrics recording,
learning systems, and dashboard utilities.
"""

from .dashboard_utils import process_dashboard_data
from .learning import (
    categorize_query,
    clear_learning_metrics,
    get_learning_metrics,
    get_query_suggestions,
    get_related_questions,
    record_error_metrics,
    record_query_metrics,
)
from .metrics_recorder import (
    record_ai_attempt_metrics,
    record_cache_hit_metrics,
    record_complete_failure_metrics,
    record_error_metrics_with_context,
    record_heuristic_fallback_metrics,
    record_successful_query_metrics,
)

__all__ = [
    "categorize_query",
    "get_query_suggestions",
    "get_related_questions",
    "clear_learning_metrics",
    "get_learning_metrics",
    "record_query_metrics",
    "record_error_metrics",
    "record_cache_hit_metrics",
    "record_ai_attempt_metrics",
    "record_successful_query_metrics",
    "record_heuristic_fallback_metrics",
    "record_error_metrics_with_context",
    "record_complete_failure_metrics",
    "process_dashboard_data",
]
