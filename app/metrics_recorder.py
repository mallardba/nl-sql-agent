"""
Metrics Recording Module

Centralizes all metrics recording logic for the SQL agent system.
"""

from typing import Any, Dict

from .enums import SQLSource
from .learning import record_error_metrics, record_query_metrics


def record_cache_hit_metrics(
    question: str, cached_result: Dict[str, Any], response_time: float
) -> None:
    """Record metrics for cache hit queries."""
    record_query_metrics(question, cached_result, response_time, is_ai_attempt=False)


def record_ai_attempt_metrics(
    question: str, sql: str, ai_fallback_error: bool, category: str, confidence: float
) -> None:
    """Record metrics for AI attempts (even if they failed)."""
    ai_attempt_result = {
        "answer_text": "AI attempt (may have failed)",
        "sql": sql,
        "rows": [],
        "chart_json": None,
        "sql_source": SQLSource.AI.value,
        "sql_corrected": False,
        "ai_fallback_error": ai_fallback_error,
        "query_category": category,
        "category_confidence": confidence,
        "response_time": 0,
    }
    record_query_metrics(question, ai_attempt_result, 0, is_ai_attempt=True)


def record_successful_query_metrics(
    question: str, result: Dict[str, Any], response_time: float, sql_source: SQLSource
) -> None:
    """Record metrics for successful queries."""
    if sql_source != SQLSource.HEURISTIC_FALLBACK:
        record_query_metrics(question, result, response_time, is_ai_attempt=False)


def record_heuristic_fallback_metrics(question: str, result: Dict[str, Any]) -> None:
    """Record metrics for successful heuristic fallback queries."""
    record_query_metrics(question, result, result["response_time"], is_ai_attempt=False)


def record_error_metrics_with_context(error_type: str, error_message: str) -> None:
    """Record error metrics with context."""
    record_error_metrics(error_type, error_message)


def record_complete_failure_metrics(
    question: str, error_result: Dict[str, Any]
) -> None:
    """Record metrics for complete failure scenarios."""
    record_query_metrics(
        question, error_result, error_result["response_time"], is_ai_attempt=False
    )
