"""
Error Handling Module

Provides standardized error handling and validation for the NL-SQL Agent.
Handles input validation, error result creation, and error metrics recording.
"""

import time
from typing import Any, Dict, Optional

from .learning import record_query_metrics


def create_error_result(
    error_type: str,
    message: str,
    question: str = None,
    start_time: float = None,
    additional_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized error result dictionary."""
    if start_time is None:
        start_time = time.time()

    error_details = {
        "type": error_type,
        "description": message,
        "received_value": str(question) if question is not None else "None",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    if additional_details:
        error_details.update(additional_details)

    error_result = {
        "answer_text": f"Error: {message}",
        "sql": "",
        "rows": [],
        "chart_json": None,
        "sql_source": "error",
        "sql_corrected": False,
        "ai_fallback_error": False,
        "error_details": error_details,
        "query_category": "unknown",
        "category_confidence": 0.0,
        "response_time": time.time() - start_time,
    }

    # Record metrics for the error
    record_query_metrics(
        question or "None",
        error_result,
        error_result["response_time"],
        is_ai_attempt=False,
    )

    return error_result


def validate_question_input(
    question: str, start_time: float
) -> Optional[Dict[str, Any]]:
    """Validate question input and return error result if invalid.

    Note: Basic validation (None, type, empty) is handled by main.py endpoints.
    This function handles additional validation that might be needed.
    """

    # # Check for None
    # if question is None:
    #     return create_error_result(
    #         "input_validation_error",
    #         "Question cannot be None",
    #         question,
    #         start_time,
    #     )

    # # Check for non-string type
    # if not isinstance(question, str):
    #     return create_error_result(
    #         "input_validation_error",
    #         f"Invalid question input. Received: {type(question).__name__} - {question}",
    #         question,
    #         start_time,
    #         {"received_type": type(question).__name__},
    #     )

    # # Check for empty or whitespace-only string
    # if not question.strip():
    #     return create_error_result(
    #         "input_validation_error",
    #         "Question cannot be empty",
    #         question,
    #         start_time,
    #     )

    # Input is valid
    return None
