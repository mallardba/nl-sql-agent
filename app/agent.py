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

from .core import (
    fix_sql_syntax,
    generate_sql_with_ai,
    heuristic_sql_fallback,
    learn_from_error,
)
from .data import (
    create_result_dictionary,
    find_similar_questions,
    generate_chart_from_rows,
    generate_simple_chart_from_rows,
    get_cache,
    get_schema_metadata,
    respond,
    run_sql,
    set_cache,
    store_question_embedding,
    to_jsonable,
)
from .enums import ErrorType, QueryCategory, SQLSource
from .learning import (
    categorize_query,
    get_query_suggestions,
    get_related_questions,
    record_ai_attempt_metrics,
    record_cache_hit_metrics,
    record_complete_failure_metrics,
    record_error_metrics_with_context,
    record_heuristic_fallback_metrics,
    record_successful_query_metrics,
)
from .utils import log_ai_error, validate_question_input


def answer_question(question: str, force_heuristic: bool = False) -> dict:
    """Answer a natural language question using AI-powered SQL generation."""
    start_time = time.time()

    # Validate input using error handler
    validation_error = validate_question_input(question, start_time)
    if validation_error:
        return validation_error

    # Categorize the query for better pattern recognition
    category_str, confidence, category_metadata = categorize_query(question)

    # Convert string category to enum
    try:
        category = QueryCategory(category_str)
    except ValueError:
        category = QueryCategory.UNKNOWN

    q = question.lower()
    cache_key = f"q::{q.strip()}"
    cached = get_cache(cache_key)
    if cached:
        # Add source info for cached results
        cached["sql_source"] = SQLSource.CACHE.value
        cached["sql_corrected"] = False
        cached["query_category"] = category.value
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
            sql_source = SQLSource.HEURISTIC
            ai_fallback_error = False
        else:
            # Generate SQL using AI (with fallback to heuristic)
            sql, sql_corrected, sql_source = generate_sql_with_ai(question, schema_info)

            # Track if this was a fallback due to AI failure
            ai_fallback_error = sql_source == SQLSource.HEURISTIC_FALLBACK

        # Record AI attempt (even if it failed and fell back to heuristic)
        if sql_source in [SQLSource.AI, SQLSource.HEURISTIC_FALLBACK]:
            record_ai_attempt_metrics(
                question, sql, ai_fallback_error, category, confidence
            )

        # Execute the SQL with error handling
        try:
            rows = run_sql(sql)
        except Exception as sql_error:
            sql_error_details = {
                "type": ErrorType.SQL_EXECUTION_ERROR.value,
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
        chart_json = generate_chart_from_rows(rows, question)

        # Create result dictionary using result processor
        result = create_result_dictionary(
            question=question,
            sql=sql,
            rows=rows,
            chart_json=chart_json,
            sql_source=sql_source,
            sql_corrected=sql_corrected,
            ai_fallback_error=ai_fallback_error,
            category=category,
            confidence=confidence,
            response_time=time.time() - start_time,
        )

        # Store successful query in question embeddings for future learning
        if sql_source in [SQLSource.AI, SQLSource.HEURISTIC] and not sql_corrected:
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

        # Get query suggestions and related questions
        try:
            similar_queries = find_similar_questions(question, n_results=3)
            result["query_suggestions"] = get_query_suggestions(
                question, category.value, n_suggestions=3
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
        record_successful_query_metrics(
            question, result, result["response_time"], sql_source
        )

        set_cache(cache_key, to_jsonable(result))
        return respond(result)

    except Exception as e:
        # Check if we have SQL error details from the inner try block
        if "sql_error_details" in locals():
            error_details = sql_error_details
            error_details["question"] = question
        else:
            error_details = {
                "type": ErrorType.AI_GENERATION_EXCEPTION.value,
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
            error_type=ErrorType.AI_GENERATION_EXCEPTION.value,
            additional_context={
                "error_details": error_details,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        # Record error metrics
        record_error_metrics_with_context(
            ErrorType.AI_GENERATION_EXCEPTION.value, str(e)
        )

        # Try heuristic fallback
        try:
            print("Attempting heuristic fallback...")
            sql = heuristic_sql_fallback(question)
            sql_source = SQLSource.HEURISTIC
            sql_corrected = False

            rows = run_sql(sql)

            # Generate chart if we have numeric data
            chart_json = generate_simple_chart_from_rows(rows)

            # Create result dictionary using result processor
            result = create_result_dictionary(
                question=question,
                sql=sql,
                rows=rows,
                chart_json=chart_json,
                sql_source=sql_source,
                sql_corrected=sql_corrected,
                ai_fallback_error=True,  # This is a fallback due to AI failure
                category=category,
                confidence=confidence,
                response_time=time.time() - start_time,
                error_details=error_details,  # Include the original error details
            )

            # Record the successful heuristic fallback
            record_heuristic_fallback_metrics(question, result)

            set_cache(cache_key, to_jsonable(result))
            return respond(result)

        except Exception as heuristic_error:
            print(f"Heuristic fallback also failed: {heuristic_error}")
            # Create error result dictionary using result processor
            error_result = create_result_dictionary(
                question=question,
                sql="",
                rows=[],
                chart_json=None,
                sql_source=SQLSource.ERROR,
                sql_corrected=False,
                ai_fallback_error=False,
                category=category,
                confidence=confidence,
                response_time=time.time() - start_time,
                error_details={
                    "type": ErrorType.COMPLETE_FAILURE.value,
                    "original_exception": error_details,
                    "heuristic_fallback_exception": {
                        "exception_type": type(heuristic_error).__name__,
                        "exception_message": str(heuristic_error),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
            )

            # Record error metrics
            record_complete_failure_metrics(question, error_result)

            return error_result
