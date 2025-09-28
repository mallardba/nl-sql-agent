"""
AI-Powered SQL Generation Agent

Core agent system that converts natural language questions into executable SQL queries.
Features OpenAI GPT-4 integration, intelligent error correction, heuristic fallbacks,
and comprehensive learning capabilities for continuous improvement.

Key Features:
- OpenAI GPT-4 powered SQL generation with context-aware prompting
- Automatic SQL error detection and correction with retry mechanisms
- Heuristic fallback system for robust query generation
- Query categorization and pattern learning integration
- Performance metrics tracking and learning system integration
- Intelligent limit extraction from natural language queries
- Comprehensive error logging and recovery mechanisms
"""

import os
import time
from decimal import Decimal

from .ai_handler import generate_sql_with_ai
from .cache import get_cache, set_cache
from .error_handler import validate_question_input
from .error_logger import log_ai_error
from .heuristic_handler import heuristic_sql_fallback
from .learning import categorize_query, get_query_suggestions, get_related_questions
from .metrics_recorder import (
    record_ai_attempt_metrics,
    record_cache_hit_metrics,
    record_complete_failure_metrics,
    record_error_metrics_with_context,
    record_heuristic_fallback_metrics,
    record_successful_query_metrics,
)
from .query_utils import determine_chart_type
from .schema_index import find_similar_questions, store_question_embedding
from .sql_corrections import fix_sql_syntax, learn_from_error
from .tools import get_schema_metadata, render_chart, respond, run_sql, to_jsonable


def answer_question(question: str, force_heuristic: bool = False) -> dict:
    """Answer a natural language question using AI-powered SQL generation."""
    start_time = time.time()

    # Validate input using error handler
    validation_error = validate_question_input(question, start_time)
    if validation_error:
        return validation_error

    # Categorize the query for better pattern recognition
    category, confidence, category_metadata = categorize_query(question)

    q = question.lower()
    cache_key = f"q::{q.strip()}"
    cached = get_cache(cache_key)
    if cached:
        # Add source info for cached results
        cached["sql_source"] = "cache"
        cached["sql_corrected"] = False
        cached["query_category"] = category
        cached["category_confidence"] = confidence

        # Record cache hit metrics
        response_time = time.time() - start_time
        cached["response_time"] = response_time
        record_cache_hit_metrics(question, cached, response_time)

        return cached

    try:
        # Get schema information for AI context
        schema_info = get_schema_metadata()

        # Generate SQL using AI (with fallback to heuristic) or force heuristic
        if force_heuristic:
            # Force heuristic generation
            sql = heuristic_sql_fallback(question)
            sql_corrected = False
            sql_source = "heuristic"
            ai_fallback_error = False
        else:
            # Generate SQL using AI (with fallback to heuristic)
            sql, sql_corrected, sql_source = generate_sql_with_ai(question, schema_info)

            # Track if this was a fallback due to AI failure
            ai_fallback_error = sql_source == "heuristic_fallback"

        # Record AI attempt (even if it failed and fell back to heuristic)
        if sql_source in ["ai", "heuristic_fallback"]:
            record_ai_attempt_metrics(
                question, sql, ai_fallback_error, category, confidence
            )

        # Execute the SQL with error handling
        try:
            rows = run_sql(sql)
        except Exception as sql_error:
            sql_error_details = {
                "type": "sql_execution_error",
                "exception_type": type(sql_error).__name__,
                "exception_message": str(sql_error),
                "sql_attempted": sql,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            print(f"SQL execution failed: {sql_error}")
            print(f"SQL error details: {sql_error_details}")

            # Learn from this error
            learn_from_error(sql, str(sql_error))

            # Try to fix SQL errors and retry
            print("Attempting to fix SQL syntax...")
            fixed_sql, fixes_applied = fix_sql_syntax(sql)

            if fixes_applied:
                print(f"Fixed SQL: {fixed_sql}")
                try:
                    rows = run_sql(fixed_sql)
                    sql = fixed_sql  # Use the fixed SQL in response
                    sql_corrected = True
                    print("SQL fix successful!")
                except Exception as retry_error:
                    # Even the fixed SQL failed
                    sql_error_details["retry_failed"] = {
                        "fixed_sql": fixed_sql,
                        "retry_error": str(retry_error),
                    }
                    print(f"SQL fix failed: {retry_error}")
                    raise sql_error
            else:
                print("No SQL fixes could be applied")
                raise sql_error

        # Generate chart if we have numeric data
        chart_json = None
        if rows and len(rows) > 0:
            cols = list(rows[0].keys())
            if len(cols) >= 2:
                # Find the first numeric column for y-axis
                y_col = None
                x_col = None

                # Look for numeric column (y-axis) - prefer revenue/sales/amount columns
                for i, col in enumerate(cols):
                    val = rows[0][col]
                    if isinstance(val, (int, float, Decimal)):
                        # Prefer columns with revenue, sales, amount, total, count, etc.
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
                                "quantity",
                                "units",
                                "price",
                                "unit price",
                                "unit_price",
                                "unit_price",
                            ]
                        ):
                            y_col = col
                            break

                # If no preferred numeric column found, use first numeric column
                if not y_col:
                    for i, col in enumerate(cols):
                        val = rows[0][col]
                        if isinstance(val, (int, float, Decimal)):
                            y_col = col
                            break

                # Look for best text column for x-axis (prefer name over id)
                for i, col in enumerate(cols):
                    if col != y_col:  # Don't use the same column for both axes
                        val = rows[0][col]
                        if isinstance(val, str):
                            # Prefer columns with "name" over "id"
                            if "name" in col.lower():
                                x_col = col
                                break

                # If no "name" column found, use first text column as fallback
                if not x_col:
                    for i, col in enumerate(cols):
                        if col != y_col:  # Don't use the same column for both axes
                            val = rows[0][col]
                            if isinstance(val, str):
                                x_col = col
                                break

                # Generate chart if we have both x and y columns
                if x_col and y_col:
                    # Extract data for chart type determination
                    x_data = [row[x_col] for row in rows]
                    y_data = [row[y_col] for row in rows]

                    # Use robust chart type selection
                    chart_type = determine_chart_type(
                        x_data, y_data, x_col, y_col, question
                    )

                    chart_json = render_chart(
                        rows, spec={"type": chart_type}, x_key=x_col, y_key=y_col
                    )

        if chart_json is not None:
            chart_json = to_jsonable(chart_json)

        # Determine success message based on source
        if sql_source == "heuristic_fallback":
            answer_text = (
                "Query executed using heuristic fallback due to AI generation failure."
            )
        elif sql_source == "heuristic":
            answer_text = "Query executed successfully using heuristic-generated SQL."
        else:
            answer_text = "Query executed successfully using AI-generated SQL."

        result = {
            "answer_text": answer_text,
            "sql": sql,
            "rows": rows,
            "chart_json": chart_json,
            "sql_source": sql_source,
            "sql_corrected": sql_corrected,
            "ai_fallback_error": ai_fallback_error,
        }

        # Store successful query in question embeddings for future learning
        if sql_source in ["ai", "heuristic"] and not sql_corrected:
            try:

                store_question_embedding(
                    question=question,
                    sql=sql,
                    metadata={
                        "sql_source": sql_source,
                        "rows_count": len(rows),
                        "has_chart": chart_json is not None,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                )
            except Exception as e:
                if os.getenv("DEBUG") == "true":
                    print(f"Failed to store question embedding: {e}")

        # Record learning metrics
        response_time = time.time() - start_time
        result["query_category"] = category
        result["category_confidence"] = confidence
        result["response_time"] = response_time

        # Get query suggestions and related questions
        try:
            similar_queries = find_similar_questions(question, n_results=3)
            result["query_suggestions"] = get_query_suggestions(
                question, category, n_suggestions=3
            )
            result["related_questions"] = get_related_questions(
                question, similar_queries
            )
        except Exception as e:
            if os.getenv("DEBUG") == "true":
                print(f"Failed to get query suggestions: {e}")
            result["query_suggestions"] = []
            result["related_questions"] = []

        # Record metrics for learning (only if this wasn't already recorded as AI attempt)
        record_successful_query_metrics(question, result, response_time, sql_source)

        set_cache(cache_key, to_jsonable(result))
        return respond(result)

    except Exception as e:
        # Check if we have SQL error details from the inner try block
        if "sql_error_details" in locals():
            error_details = sql_error_details
            error_details["question"] = question
        else:
            error_details = {
                "type": "ai_generation_exception",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "question": question,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        print(f"Error in answer_question: {e}")
        print(f"Error details: {error_details}")

        # Log AI error with full context
        log_ai_error(
            question=question,
            sql=error_details.get("generated_sql", ""),
            error_message=str(e),
            error_type="ai_generation_exception",
            additional_context={
                "error_details": error_details,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        # Record error metrics
        record_error_metrics_with_context("ai_generation_exception", str(e))

        # Try heuristic fallback
        try:
            print("Attempting heuristic fallback...")
            sql = heuristic_sql_fallback(question)
            sql_source = "heuristic"
            sql_corrected = False

            rows = run_sql(sql)

            # Generate chart if we have numeric data
            chart_json = None
            if rows and len(rows) > 0:
                cols = list(rows[0].keys())
                if len(cols) >= 2:
                    # Find the first numeric column for y-axis
                    y_col = None
                    x_col = None

                    # Look for numeric column (y-axis) - prefer revenue/sales/amount columns
                    for i, col in enumerate(cols):
                        val = rows[0][col]
                        if isinstance(val, (int, float, Decimal)):
                            # Prefer columns with revenue, sales, amount, total, count, etc.
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

                    # Look for text column (x-axis) - prefer name columns
                    for i, col in enumerate(cols):
                        if col != y_col:  # Don't use the same column for both axes
                            val = rows[0][col]
                            if isinstance(val, str):
                                # Prefer columns with "name" over "id"
                                if "name" in col.lower():
                                    x_col = col
                                    break
                                elif x_col is None:  # Fallback to first text column
                                    x_col = col

                    if y_col and x_col:
                        # Chart column selection (no debug print - too verbose)
                        x_name = x_col.lower()
                chart_type = "line" if x_name in ("month", "date", "ym") else "bar"
            chart_json = render_chart(
                rows, spec={"type": chart_type}, x_key=x_col, y_key=y_col
            )

            if chart_json is not None:
                chart_json = to_jsonable(chart_json)

            answer_text = "Query executed successfully using heuristic SQL generation."
            result = {
                "answer_text": answer_text,
                "sql": sql,
                "rows": rows,
                "chart_json": chart_json,
                "sql_source": sql_source,
                "sql_corrected": sql_corrected,
                "ai_fallback_error": True,  # This is a fallback due to AI failure
                "error_details": error_details,  # Include the original error details
                "query_category": category,
                "category_confidence": confidence,
                "response_time": time.time() - start_time,
            }

            # Record the successful heuristic fallback
            record_heuristic_fallback_metrics(question, result)

            set_cache(cache_key, to_jsonable(result))
            return respond(result)

        except Exception as heuristic_error:
            print(f"Heuristic fallback also failed: {heuristic_error}")
            # Return error response with both error details
            error_result = {
                "answer_text": f"Error processing question: {str(e)}",
                "sql": "",
                "rows": [],
                "chart_json": None,
                "sql_source": "error",
                "sql_corrected": False,
                "ai_fallback_error": False,
                "error_details": {
                    "type": "complete_failure",
                    "original_exception": error_details,
                    "heuristic_fallback_exception": {
                        "exception_type": type(heuristic_error).__name__,
                        "exception_message": str(heuristic_error),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
                "query_category": category,
                "category_confidence": confidence,
                "response_time": time.time() - start_time,
            }

            # Record error metrics
            record_complete_failure_metrics(question, error_result)

            return error_result
