"""
Error logging utility for AI generation exceptions.
Logs detailed error information to files for debugging and analysis.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


def log_ai_error(
    question: str,
    sql: str,
    error_message: str,
    error_type: str = "ai_generation_exception",
    additional_context: Optional[Dict[str, Any]] = None,
):
    """
    Log AI generation errors with full context to a log file.

    Args:
        question: The original user question
        sql: The SQL that was generated (if any)
        error_message: The actual error message
        error_type: Type of error for categorization
        additional_context: Any additional context data
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "question": question,
            "generated_sql": sql,
            "error_message": str(error_message),
            "additional_context": additional_context or {},
        }

        # Write to error log file
        log_file = os.path.join(log_dir, "ai_errors.jsonl")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # Also write to a human-readable log
        readable_log_file = os.path.join(log_dir, "ai_errors_readable.log")
        with open(readable_log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Timestamp: {log_entry['timestamp']}\n")
            f.write(f"Error Type: {error_type}\n")
            f.write(f"Question: {question}\n")
            f.write(f"Generated SQL: {sql}\n")
            f.write(f"Error Message: {error_message}\n")
            if additional_context:
                f.write(
                    f"Additional Context: {json.dumps(additional_context, indent=2)}\n"
                )
            f.write(f"{'='*80}\n")

        # Print to console if DEBUG mode
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"AI Error logged: {error_type} - {error_message}")

    except Exception as e:
        # Don't let logging errors break the main flow
        print(f"Failed to log AI error: {e}")


def get_error_logs(limit: int = 50) -> list:
    """
    Retrieve recent error logs for analysis.

    Args:
        limit: Maximum number of log entries to return

    Returns:
        List of error log entries
    """
    try:
        log_file = "logs/ai_errors.jsonl"
        if not os.path.exists(log_file):
            return []

        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Get the last 'limit' entries
            for line in lines[-limit:]:
                try:
                    log_entry = json.loads(line.strip())
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue

        return logs

    except Exception as e:
        print(f"Failed to retrieve error logs: {e}")
        return []


def clear_error_logs():
    """Clear all error logs."""
    try:
        log_dir = "logs"
        if os.path.exists(log_dir):
            for file in ["ai_errors.jsonl", "ai_errors_readable.log"]:
                file_path = os.path.join(log_dir, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
        print("Error logs cleared.")
    except Exception as e:
        print(f"Failed to clear error logs: {e}")


def get_error_summary() -> Dict[str, Any]:
    """
    Get a summary of error patterns from the logs.

    Returns:
        Dictionary with error statistics
    """
    try:
        logs = get_error_logs(limit=1000)  # Get more logs for better analysis

        if not logs:
            return {"total_errors": 0, "error_types": {}, "recent_errors": []}

        # Count error types
        error_types = {}
        for log in logs:
            error_type = log.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Get recent errors (last 10)
        recent_errors = logs[-10:] if len(logs) > 10 else logs

        return {
            "total_errors": len(logs),
            "error_types": error_types,
            "recent_errors": recent_errors,
            "most_common_error": (
                max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
            ),
        }

    except Exception as e:
        print(f"Failed to get error summary: {e}")
        return {"total_errors": 0, "error_types": {}, "recent_errors": []}
