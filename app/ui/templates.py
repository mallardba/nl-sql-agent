"""
Template rendering utilities for HTML pages.

Provides functions to load and format HTML templates with dynamic data.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List


def _serialize_for_json(obj: Any) -> Any:
    """Convert non-JSON-serializable objects to JSON-serializable ones."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    else:
        return obj


def load_template(template_name: str) -> str:
    """Load HTML template from templates directory."""
    template_path = Path(__file__).parent / "templates" / template_name
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def format_learning_dashboard_template(
    total_queries: int,
    success_rate: float,
    avg_response_time: float,
    ai_usage_rate: float,
    cache_hit_rate: float,
    correction_rate: float,
    category_data: List[Dict[str, Any]],
    error_data: List[Dict[str, Any]],
    complexity_data: List[Dict[str, Any]],
    source_data: List[Dict[str, Any]],
) -> str:
    """Format the learning dashboard template with data."""
    template = load_template("learning_dashboard.html")

    # Format category HTML
    if category_data:
        category_html = "".join(
            [
                f"""
            <div class="category-item">
                <div class="category-name">{cat['name']}</div>
                <div class="category-stats">
                    {cat['successful']}/{cat['total']} queries
                    <span class="success-rate">({cat['success_rate']:.1%} success)</span>
                </div>
            </div>
            """
                for cat in category_data
            ]
        )
    else:
        category_html = '<div class="no-data">No category data available</div>'

    # Format error HTML
    if error_data:
        error_html = "".join(
            [
                f"""
            <div class="error-item">
                <div class="error-type">{error['type'].replace('_', ' ').title()}</div>
                <div class="error-count">{error['count']} occurrences</div>
            </div>
            """
                for error in error_data
            ]
        )
    else:
        error_html = '<div class="no-data">No errors recorded</div>'

    # Format complexity HTML
    if complexity_data:
        complexity_html = "".join(
            [
                f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 6px;">
                <span style="font-weight: 600; color: #374151;">{comp['level'].title()}</span>
                <span style="color: #6b7280;">{comp['count']} queries</span>
            </div>
            """
                for comp in complexity_data
            ]
        )
    else:
        complexity_html = '<div class="no-data">No complexity data available</div>'

    # Format source HTML
    if source_data:
        source_html = "".join(
            [
                f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 6px;">
                <span style="font-weight: 600; color: #374151;">{source['source'].title()}</span>
                <div style="text-align: right;">
                    <div style="color: #6b7280; font-size: 0.9rem;">{source['successful']}/{source['total']} queries</div>
                    <div style="color: #059669; font-weight: 600;">{source['accuracy_percentage']} accuracy</div>
                </div>
            </div>
            """
                for source in source_data
            ]
        )
    else:
        source_html = '<div class="no-data">No source data available</div>'

    return template.format(
        total_queries=total_queries,
        success_rate=success_rate,
        avg_response_time=avg_response_time,
        ai_usage_rate=ai_usage_rate,
        cache_hit_rate=cache_hit_rate,
        correction_rate=correction_rate,
        category_html=category_html,
        error_html=error_html,
        complexity_html=complexity_html,
        source_html=source_html,
    )


def format_query_results_template(
    question: str,
    sql: str,
    answer_text: str,
    table_html: str,
    chart_html: str,
    suggestions_html: str,
    rows: List[Dict[str, Any]],
) -> str:
    """Format the query results template with data."""
    template = load_template("query_results.html")

    # Convert rows to JSON for JavaScript
    serialized_rows = _serialize_for_json(rows)
    results_json = json.dumps(serialized_rows) if serialized_rows else "[]"

    return template.format(
        question=question,
        sql=sql,
        answer_text=answer_text,
        table_html=table_html,
        chart_html=chart_html,
        suggestions_html=suggestions_html,
        results_json=results_json,
    )


def format_error_page_template(
    error_title: str,
    error_message: str,
    back_url: str = "/",
) -> str:
    """Format the error page template with data."""
    template = load_template("error_page.html")

    return template.format(
        error_title=error_title,
        error_message=error_message,
        back_url=back_url,
    )
