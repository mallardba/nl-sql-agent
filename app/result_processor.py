"""
Result Processing Module

Handles all result processing logic including chart generation, data processing,
column detection, and result dictionary creation for the SQL agent system.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from .query_utils import determine_chart_type
from .tools import render_chart, to_jsonable


def detect_chart_columns(
    rows: List[Dict[str, Any]]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect the best x and y columns for chart generation from query results.

    Args:
        rows: List of result rows from SQL query

    Returns:
        Tuple of (x_column, y_column) or (None, None) if no suitable columns found
    """
    if not rows or len(rows) == 0:
        return None, None

    cols = list(rows[0].keys())
    if len(cols) < 2:
        return None, None

    y_col = None
    x_col = None

    # Preferred numeric column keywords for y-axis
    numeric_keywords = [
        "revenue",
        "sales",
        "amount",
        "total",
        "count",
        "sum",
        "avg",
        "quantity",
        "units",
        "price",
        "unit price",
        "unit_price",
    ]

    # Look for numeric column (y-axis) - prefer revenue/sales/amount columns
    for col in cols:
        val = rows[0][col]
        if isinstance(val, (int, float, Decimal)):
            # Prefer columns with revenue, sales, amount, total, count, etc.
            if any(keyword in col.lower() for keyword in numeric_keywords):
                y_col = col
                break

    # If no preferred numeric column found, use first numeric column
    if not y_col:
        for col in cols:
            val = rows[0][col]
            if isinstance(val, (int, float, Decimal)):
                y_col = col
                break

    # Look for best text column for x-axis (prefer name over id)
    for col in cols:
        if col != y_col:  # Don't use the same column for both axes
            val = rows[0][col]
            if isinstance(val, str):
                # Prefer columns with "name" over "id"
                if "name" in col.lower():
                    x_col = col
                    break

    # If no "name" column found, use first text column as fallback
    if not x_col:
        for col in cols:
            if col != y_col:  # Don't use the same column for both axes
                val = rows[0][col]
                if isinstance(val, str):
                    x_col = col
                    break

    return x_col, y_col


def generate_chart_from_rows(
    rows: List[Dict[str, Any]], question: str
) -> Optional[Dict[str, Any]]:
    """
    Generate chart JSON from query result rows.

    Args:
        rows: List of result rows from SQL query
        question: Original question for context

    Returns:
        Chart JSON data or None if no chart can be generated
    """
    if not rows or len(rows) == 0:
        return None

    x_col, y_col = detect_chart_columns(rows)

    if not x_col or not y_col:
        return None

    # Extract data for chart type determination
    x_data = [row[x_col] for row in rows]
    y_data = [row[y_col] for row in rows]

    # Use robust chart type selection
    chart_type = determine_chart_type(x_data, y_data, x_col, y_col, question)

    # Generate chart JSON
    chart_json = render_chart(rows, spec={"type": chart_type}, x_key=x_col, y_key=y_col)

    # Convert to JSON-serializable format
    if chart_json is not None:
        chart_json = to_jsonable(chart_json)

    return chart_json


def generate_simple_chart_from_rows(
    rows: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Generate a simple chart from rows using basic column detection.
    Used for heuristic fallback scenarios.

    Args:
        rows: List of result rows from SQL query

    Returns:
        Chart JSON data or None if no chart can be generated
    """
    if not rows or len(rows) == 0:
        return None

    cols = list(rows[0].keys())
    if len(cols) < 2:
        return None

    y_col = None
    x_col = None

    # Simple numeric column detection
    for col in cols:
        val = rows[0][col]
        if isinstance(val, (int, float, Decimal)):
            if any(
                keyword in col.lower()
                for keyword in [
                    "revenue",
                    "sales",
                    "amount",
                    "total",
                    "count",
                    "sum",
                    "avg",
                ]
            ):
                y_col = col
                break
            elif y_col is None:  # Fallback to first numeric column
                y_col = col

    # Simple text column detection
    for col in cols:
        if col != y_col:  # Don't use the same column for both axes
            val = rows[0][col]
            if isinstance(val, str):
                if "name" in col.lower():
                    x_col = col
                    break
                elif x_col is None:  # Fallback to first text column
                    x_col = col

    if not y_col or not x_col:
        return None

    # Simple chart type selection
    x_name = x_col.lower()
    chart_type = "line" if x_name in ("month", "date", "ym") else "bar"

    chart_json = render_chart(rows, spec={"type": chart_type}, x_key=x_col, y_key=y_col)

    if chart_json is not None:
        chart_json = to_jsonable(chart_json)

    return chart_json


def determine_answer_text(sql_source: str) -> str:
    """
    Determine the appropriate answer text based on SQL source.

    Args:
        sql_source: Source of the SQL query (ai, heuristic, heuristic_fallback, error)

    Returns:
        Appropriate answer text message
    """
    if sql_source == "heuristic_fallback":
        return "Query executed using heuristic fallback due to AI generation failure."
    elif sql_source == "heuristic":
        return "Query executed successfully using heuristic-generated SQL."
    elif sql_source == "error":
        return "Error processing question: Unable to generate valid SQL query."
    else:  # This covers "ai" case
        return "Query executed successfully using AI-generated SQL."


def create_result_dictionary(
    question: str,
    sql: str,
    rows: List[Dict[str, Any]],
    sql_source: str,
    sql_corrected: bool = False,
    ai_fallback_error: bool = False,
    category: str = None,
    confidence: float = None,
    response_time: float = None,
    chart_json: Optional[Dict[str, Any]] = None,
    error_details: Optional[Dict[str, Any]] = None,
    query_suggestions: List[str] = None,
    related_questions: List[str] = None,
) -> Dict[str, Any]:
    """
    Create a complete result dictionary with all necessary fields.

    This function handles learning metrics (category, confidence, response_time)
    and creates a standardized result structure.

    Args:
        question: Original question
        sql: Generated SQL query
        rows: Query result rows
        sql_source: Source of the SQL (ai, heuristic, etc.)
        sql_corrected: Whether SQL was corrected
        ai_fallback_error: Whether this was an AI fallback
        category: Query category (learning metric)
        confidence: Category confidence (learning metric)
        response_time: Response time in seconds (learning metric)
        chart_json: Chart data (optional)
        error_details: Error details (optional)
        query_suggestions: Query suggestions (optional)
        related_questions: Related questions (optional)

    Returns:
        Complete result dictionary with learning metrics included
    """
    # Generate chart if not provided
    if chart_json is None and rows:
        chart_json = generate_chart_from_rows(rows, question)

    # Determine answer text
    answer_text = determine_answer_text(sql_source)

    # Build result dictionary
    result = {
        "answer_text": answer_text,
        "sql": sql,
        "rows": rows,
        "chart_json": chart_json,
        "sql_source": sql_source,
        "sql_corrected": sql_corrected,
        "ai_fallback_error": ai_fallback_error,
    }

    # Add optional fields if provided

    # Record learning metrics
    if category is not None:
        result["query_category"] = category
    if confidence is not None:
        result["category_confidence"] = confidence
    if response_time is not None:
        result["response_time"] = response_time

    # Record errors and suggestions
    if error_details is not None:
        result["error_details"] = error_details
    if query_suggestions is not None:
        result["query_suggestions"] = query_suggestions
    if related_questions is not None:
        result["related_questions"] = related_questions

    return result
