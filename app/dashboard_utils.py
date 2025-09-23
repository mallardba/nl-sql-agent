"""
Dashboard data processing utilities.

Provides helper functions for processing learning metrics data
for dashboard display and visualization.
"""

from typing import Any, Dict


def process_dashboard_data(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Process learning metrics for dashboard display."""
    # Calculate basic metrics
    total_queries = metrics.get("total_queries", 0)
    success_rate = metrics.get("success_rate", 0)
    avg_response_time = metrics.get("avg_response_time", 0)

    # Process category performance
    category_performance = metrics.get("category_performance", {})
    category_data = []
    for category, perf in category_performance.items():
        if perf.get("total", 0) > 0:
            category_data.append(
                {
                    "name": category.replace("_", " ").title(),
                    "total": perf.get("total", 0),
                    "successful": perf.get("successful", 0),
                    "success_rate": perf.get("success_rate", 0),
                }
            )
    category_data.sort(key=lambda x: x["total"], reverse=True)

    # Process error patterns
    error_patterns = metrics.get("error_patterns", {})
    error_data = [{"type": k, "count": v} for k, v in error_patterns.items()]
    error_data.sort(key=lambda x: x["count"], reverse=True)

    # Process query complexity
    complexity = metrics.get("query_complexity", {})
    complexity_data = [{"level": k, "count": v} for k, v in complexity.items()]

    # Process accuracy by source
    accuracy_by_source = metrics.get("accuracy_by_source", {})
    source_data = []
    for source, data in accuracy_by_source.items():
        if isinstance(data, dict):
            source_data.append(
                {
                    "source": source,
                    "successful": data.get("successful", 0),
                    "total": data.get("total", 0),
                    "accuracy_percentage": data.get("accuracy_percentage", "0.0%"),
                }
            )
        else:
            # Handle old format for backward compatibility
            source_data.append(
                {
                    "source": source,
                    "successful": data,
                    "total": data,
                    "accuracy_percentage": "100.0%" if data > 0 else "0.0%",
                }
            )

    return {
        "total_queries": total_queries,
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "ai_usage_rate": metrics.get("ai_usage_rate", 0),
        "cache_hit_rate": metrics.get("cache_hit_rate", 0),
        "correction_rate": metrics.get("correction_rate", 0),
        "category_data": category_data,
        "error_data": error_data,
        "complexity_data": complexity_data,
        "source_data": source_data,
    }
