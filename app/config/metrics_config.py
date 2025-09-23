"""
Metrics configuration for learning system.

Defines the default structure for tracking learning metrics and performance.
Used by LearningSystem to initialize metrics tracking.
"""

from collections import defaultdict
from typing import Any, Dict

DEFAULT_METRICS_CONFIG: Dict[str, Any] = {
    "total_queries": 0,
    "successful_queries": 0,
    "ai_generated": 0,
    "heuristic_fallback": 0,
    "sql_corrected": 0,
    "cache_hits": 0,
    "error_patterns": defaultdict(int),
    "category_performance": defaultdict(lambda: {"total": 0, "successful": 0}),
    "query_complexity": defaultdict(int),
    "response_times": [],
    "accuracy_by_source": {"ai": 0, "heuristic": 0, "cache": 0, "error": 0},
    "source_totals": {"ai": 0, "heuristic": 0, "cache": 0, "error": 0},
}
