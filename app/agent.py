"""
Agent orchestration with LangChain integration.
Uses OpenAI to generate SQL from natural language questions.
"""

import os
import re
import time
from decimal import Decimal
from typing import Any, Dict

from .cache import get_cache, set_cache
from .tools import get_schema_metadata, render_chart, respond, run_sql, to_jsonable

# LangChain imports (will be available after pip install)
try:
    # from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print(
        "Warning: LangChain not available. Install with: pip install langchain langchain-openai"
    )

# Initialize OpenAI client (will be set up when API key is provided)
_llm = None


def _get_llm():
    """Get or create the OpenAI LLM instance."""
    global _llm
    if _llm is None:
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain not available. Install required packages.")

        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your-openai-api-key-here":
            raise ValueError(
                "OpenAI API key not set. Please set OPENAI_API_KEY in your .env file. "
                "Get your key from: https://platform.openai.com/api-keys"
            )

        _llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            api_key=api_key,
        )
    return _llm


def _fix_sql_syntax(sql: str) -> str:
    """Fix common SQL syntax errors."""
    # Fix CAST syntax errors
    if "CAST(" in sql:
        import re

        # Pattern: CAST(expression AS revenue -> CAST(expression AS DECIMAL(10,2)) AS revenue
        # This handles cases where there's no space before AS or the alias is directly after AS
        pattern = (
            r"CAST\(([^)]+)\)\s*AS\s+(\w+)(?=\s+FROM|\s+ORDER|\s+GROUP|\s+WHERE|\s*$)"
        )

        def replace_cast(match):
            expression = match.group(1)
            alias = match.group(2)
            return f"CAST({expression} AS DECIMAL(10,2)) AS {alias}"

        sql = re.sub(pattern, replace_cast, sql)

        # Also handle the specific case: CAST(...) AS revenue FROM
        sql = re.sub(
            r"CAST\(([^)]+)\)\s*AS\s+revenue\s+FROM",
            r"CAST(\1 AS DECIMAL(10,2)) AS revenue FROM",
            sql,
        )

    return sql


def _generate_sql_with_ai(
    question: str, schema_info: Dict[str, Any]
) -> tuple[str, bool, str]:
    """Generate SQL using OpenAI based on the question and schema."""
    if not LANGCHAIN_AVAILABLE:
        # Fallback to heuristic approach if LangChain not available
        return _heuristic_sql_fallback(question)

    try:
        llm = _get_llm()

        # Create a comprehensive prompt for SQL generation
        system_prompt = f"""
        You are an expert SQL developer. Generate MySQL SQL queries based on natural language questions.
        
        Database Schema:
        {schema_info}
        
        Rules:
        1. Only generate SELECT queries (no INSERT, UPDATE, DELETE)
        2. Use proper JOINs when multiple tables are needed
        3. Include appropriate WHERE clauses for filtering
        4. Use meaningful column aliases
        5. Order results logically
        6. Limit results to reasonable amounts (use LIMIT when appropriate)
        7. Handle dates properly using MySQL date functions:
           - "last year" = INTERVAL 12 MONTH
           - "last quarter" = INTERVAL 3 MONTH  
           - "last month" = INTERVAL 1 MONTH
           - "last 6 months" = INTERVAL 6 MONTH
        8. Use aggregate functions (SUM, COUNT, AVG) when appropriate
        9. When using CAST(), always specify the data type: CAST(expression AS DECIMAL(10,2))
        10. Ensure all parentheses are properly closed
        11. Test your SQL syntax before returning
        
        Return only the raw SQL query without any markdown formatting, code blocks, or explanations.
        Example: SELECT * FROM table WHERE id = 1;
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate SQL for this question: {question}"),
        ]

        response = llm.invoke(messages)
        sql = response.content.strip()

        # Debug print for AI generated SQL (only on error)
        if os.getenv(
            "DEBUG", "false"
        ).lower() == "true" and not sql.strip().upper().startswith("SELECT"):
            print(f"AI generated SQL (ERROR): {sql}")

        # Clean up markdown code blocks if present
        if sql.startswith("```sql"):
            sql = sql[6:]  # Remove ```sql
        if sql.startswith("```"):
            sql = sql[3:]  # Remove ```
        if sql.endswith("```"):
            sql = sql[:-3]  # Remove trailing ```
        sql = sql.strip()

        # Basic safety check
        if not sql.lower().startswith("select"):
            print(f"SQL doesn't start with SELECT: {sql[:50]}...")
            raise ValueError("Generated SQL is not a SELECT query")

        # Fix common SQL syntax errors
        original_sql = sql
        sql = _fix_sql_syntax(sql)
        corrected = sql != original_sql
        if corrected and os.getenv("DEBUG", "false").lower() == "true":
            print(f"SQL corrected: {original_sql} -> {sql}")

        # Basic SQL syntax validation
        if sql.count("(") != sql.count(")"):
            raise ValueError("Unmatched parentheses in SQL query")

        return sql, corrected, "ai"

    except Exception as e:
        print(f"AI SQL generation failed: {e}")
        # Fallback to heuristic approach
        return _heuristic_sql_fallback(question), False, "heuristic_fallback"


def _heuristic_sql_fallback(question: str) -> str:
    """Fallback heuristic SQL generation (original logic)."""
    q = question.lower()
    if "top" in q and "product" in q and ("revenue" in q or "sales" in q):
        n = _months_from_question(q, default=3)
        sql = (
            "SELECT p.name AS product, CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS revenue "
            "FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id "
            "JOIN orders o ON o.id = oi.order_id "
            "WHERE o.status <> 'CANCELLED' AND "
            f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
            "GROUP BY p.name ORDER BY revenue DESC LIMIT 10;"
        )
        # Debug print for heuristic SQL (only on error)
        if os.getenv(
            "DEBUG", "false"
        ).lower() == "true" and not sql.strip().upper().startswith("SELECT"):
            print(f"Heuristic generated SQL (ERROR): {sql}")
        return sql
    if "sales by month" in q or ("monthly" in q and "sales" in q):
        return (
            "SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, "
            "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS total_sales "
            "FROM orders o "
            "JOIN order_items oi ON oi.order_id = o.id "
            "WHERE o.status <> 'CANCELLED' "
            "AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) "
            "GROUP BY month "
            "ORDER BY month;"
        )
    # Fallback simple sample
    return "SELECT * FROM customers LIMIT 10;"


def answer_question(question: str) -> dict:
    """Answer a natural language question using AI-powered SQL generation."""
    # Validate input
    if not question or not isinstance(question, str):
        return {
            "answer_text": f"Error: Invalid question input. Received: {type(question).__name__} - {question}",
            "sql": "",
            "rows": [],
            "chart_json": None,
            "sql_source": "error",
            "sql_corrected": False,
            "ai_fallback_error": False,
            "error_details": {
                "type": "input_validation_error",
                "description": f"Invalid question input: {type(question).__name__}",
                "received_value": str(question),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

    q = question.lower()
    cache_key = f"q::{q.strip()}"
    cached = get_cache(cache_key)
    if cached:
        # Add source info for cached results
        cached["sql_source"] = "cache"
        cached["sql_corrected"] = False
        return cached

    try:
        # Get schema information for AI context
        schema_info = get_schema_metadata()

        # Generate SQL using AI (with fallback to heuristic)
        sql, sql_corrected, sql_source = _generate_sql_with_ai(question, schema_info)

        # Track if this was a fallback due to AI failure
        ai_fallback_error = sql_source == "heuristic_fallback"

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

            # Try to fix common SQL errors and retry
            if "CAST" in str(sql_error) and "AS " in sql:
                print("Attempting to fix CAST syntax...")
                fixed_sql = _fix_sql_syntax(sql)
                if fixed_sql != sql:
                    print(f"Fixed SQL: {fixed_sql}")
                    try:
                        rows = run_sql(fixed_sql)
                        sql = fixed_sql  # Use the fixed SQL in response
                        sql_corrected = True
                    except Exception as retry_error:
                        # Even the fixed SQL failed
                        sql_error_details["retry_failed"] = {
                            "fixed_sql": fixed_sql,
                            "retry_error": str(retry_error),
                        }
                        raise sql_error
                else:
                    raise sql_error
            else:
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

                    # Chart column selection (no debug print - too verbose)
                    x_name = x_col.lower()
                    chart_type = "line" if x_name in ("month", "date", "ym") else "bar"
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

        # Try heuristic fallback
        try:
            print("Attempting heuristic fallback...")
            sql = _heuristic_sql_fallback(question)
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
            }

            set_cache(cache_key, to_jsonable(result))
            return respond(result)

        except Exception as heuristic_error:
            print(f"Heuristic fallback also failed: {heuristic_error}")
            # Return error response with both error details
            return {
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
            }


def _months_from_question(q: str, default=3):
    """Extract number of months from question text."""
    q_lower = q.lower()

    # Handle specific time periods
    if "last year" in q_lower or "past year" in q_lower:
        return 12
    elif "last quarter" in q_lower or "past quarter" in q_lower:
        return 3
    elif "last month" in q_lower or "past month" in q_lower:
        return 1
    elif "last 6 months" in q_lower or "past 6 months" in q_lower:
        return 6

    # Handle "last X months" pattern
    m = re.search(r"\blast\s+(\d{1,2})\s+months?\b", q_lower)
    n = int(m.group(1)) if m else default
    return max(1, min(n, 24))  # clamp 1..24
