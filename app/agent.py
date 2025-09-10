"""
Agent orchestration with LangChain integration.
Uses OpenAI to generate SQL from natural language questions.
"""

import os
import re
import time
from decimal import Decimal
from typing import Any, Dict, List, Tuple

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
    """Fix common SQL syntax errors using pattern-based corrections."""

    fixes_applied = []

    # 1. Fix CAST syntax errors
    sql, cast_fixes = _fix_cast_syntax(sql)
    fixes_applied.extend(cast_fixes)

    # 2. Fix ambiguous column references
    sql, ambiguous_fixes = _fix_ambiguous_columns(sql)
    fixes_applied.extend(ambiguous_fixes)

    # 3. Fix missing table aliases
    sql, alias_fixes = _fix_missing_aliases(sql)
    fixes_applied.extend(alias_fixes)

    # 4. Fix JOIN syntax issues
    sql, join_fixes = _fix_join_syntax(sql)
    fixes_applied.extend(join_fixes)

    # 5. Fix GROUP BY issues
    sql, groupby_fixes = _fix_groupby_syntax(sql)
    fixes_applied.extend(groupby_fixes)

    # 6. Fix invalid JOIN references
    sql, join_ref_fixes = _fix_invalid_join_references(sql)
    fixes_applied.extend(join_ref_fixes)

    # 7. Fix missing column references
    sql, column_fixes = _fix_missing_columns(sql)
    fixes_applied.extend(column_fixes)

    # 8. Apply learned error patterns
    sql, learned_fixes = _apply_learned_patterns(sql)
    fixes_applied.extend(learned_fixes)

    # Debug output if fixes were applied
    if fixes_applied and os.getenv("DEBUG", "false").lower() == "true":
        print(f"SQL fixes applied: {fixes_applied}")

    return sql


def _apply_learned_patterns(sql: str) -> Tuple[str, List[str]]:
    """Apply learned error patterns from previous corrections."""
    import re

    fixes = []

    # This is where we would apply patterns learned from previous errors
    # For now, we'll implement a simple pattern matching system

    # Learn from common error patterns
    # Note: These patterns are currently disabled as they were too broad
    # and were matching valid SQL queries unnecessarily
    learned_patterns = [
        # TODO: Add more specific patterns based on actual error analysis
    ]

    for pattern_info in learned_patterns:
        if re.search(pattern_info["pattern"], sql, re.IGNORECASE):
            sql = re.sub(
                pattern_info["pattern"],
                pattern_info["replacement"],
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(pattern_info["description"])

    return sql, fixes


def _learn_from_error(sql: str, error_message: str) -> None:
    """Learn from SQL errors to improve future corrections."""
    # This would store error patterns in a database or file
    # For now, we'll just log the pattern for analysis
    if os.getenv("DEBUG", "false").lower() == "true":
        print(f"Learning from error: {error_message}")
        print(f"Problematic SQL: {sql}")

    # In a production system, you would:
    # 1. Store the error pattern in a database
    # 2. Track frequency of similar errors
    # 3. Build a machine learning model to predict fixes
    # 4. Update the correction patterns based on success rates


def _fix_cast_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix CAST syntax errors."""
    import re

    fixes = []

    # Pattern: CAST(expression) AS alias -> CAST(expression AS DECIMAL(10,2)) AS alias
    pattern = r"CAST\(([^)]+)\)\s*AS\s+(\w+)(?=\s+FROM|\s+ORDER|\s+GROUP|\s+WHERE|\s*$)"

    def replace_cast(match):
        expression = match.group(1)
        alias = match.group(2)
        fixes.append(f"Fixed CAST syntax: {alias}")
        return f"CAST({expression} AS DECIMAL(10,2)) AS {alias}"

    sql = re.sub(pattern, replace_cast, sql)
    return sql, fixes


def _fix_ambiguous_columns(sql: str) -> Tuple[str, List[str]]:
    """Fix ambiguous column references by adding table aliases."""
    import re

    fixes = []

    # Extract table names and their aliases
    tables_with_aliases = {}

    # Find FROM table
    from_match = re.search(r"FROM\s+(\w+)(?:\s+(\w+))?", sql, re.IGNORECASE)
    if from_match:
        table_name = from_match.group(1)
        alias = (
            from_match.group(2) or table_name.lower()[:2]
        )  # Use first 2 chars as alias
        tables_with_aliases[table_name] = alias

    # Find JOIN tables
    join_matches = re.finditer(r"JOIN\s+(\w+)(?:\s+(\w+))?", sql, re.IGNORECASE)
    for match in join_matches:
        table_name = match.group(1)
        alias = match.group(2) or table_name.lower()[:2]
        tables_with_aliases[table_name] = alias

    # If we have multiple tables, check for ambiguous columns
    if len(tables_with_aliases) > 1:
        # Common ambiguous columns that appear in multiple tables
        common_ambiguous_columns = ["id", "name", "created_at", "updated_at"]

        for column in common_ambiguous_columns:
            # Look for bare column references (not table.column)
            bare_column_pattern = rf"(?<!\w\.)\b{column}\b(?!\s*\.)"
            if re.search(bare_column_pattern, sql, re.IGNORECASE):
                # Try to determine the correct table based on context
                # For now, we'll use a simple heuristic: prefer the first table
                first_table = list(tables_with_aliases.keys())[0]
                first_alias = tables_with_aliases[first_table]

                # Replace bare column with table.column
                sql = re.sub(
                    bare_column_pattern,
                    f"{first_alias}.{column}",
                    sql,
                    flags=re.IGNORECASE,
                )
                fixes.append(
                    f"Fixed ambiguous column '{column}' -> '{first_alias}.{column}'"
                )

    return sql, fixes


def _fix_missing_aliases(sql: str) -> Tuple[str, List[str]]:
    """Fix missing table aliases in complex queries."""
    import re

    fixes = []

    # Add aliases to tables that don't have them
    # Pattern: FROM table1 JOIN table2 ON condition
    # Convert to: FROM table1 t1 JOIN table2 t2 ON condition

    # This is a complex transformation that would require careful parsing
    # For now, we'll just detect the issue
    if "JOIN" in sql.upper() and not re.search(r"FROM\s+\w+\s+\w+", sql, re.IGNORECASE):
        fixes.append("Detected potential missing table aliases")

    return sql, fixes


def _fix_join_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix JOIN syntax issues."""
    import re

    fixes = []

    # Fix missing ON clauses
    if "JOIN" in sql.upper() and "ON" not in sql.upper():
        fixes.append("Detected JOIN without ON clause")

    # Fix malformed JOIN conditions
    join_on_pattern = r"JOIN\s+\w+\s+ON\s+(\w+\.\w+\s*=\s*\w+\.\w+)"
    if re.search(join_on_pattern, sql):
        fixes.append("Detected JOIN condition syntax")

    return sql, fixes


def _fix_groupby_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix GROUP BY syntax issues."""
    import re

    fixes = []

    # Check if SELECT has non-aggregate columns but no GROUP BY
    if "SELECT" in sql.upper() and "GROUP BY" not in sql.upper():
        # Look for aggregate functions
        aggregate_functions = ["SUM(", "COUNT(", "AVG(", "MAX(", "MIN("]
        has_aggregates = any(func in sql.upper() for func in aggregate_functions)

        if has_aggregates:
            # Look for non-aggregate columns
            select_match = re.search(
                r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL
            )
            if select_match:
                select_clause = select_match.group(1)
                # Simple check for non-aggregate columns
                if re.search(r"\b\w+\b", select_clause) and not all(
                    func in select_clause.upper() for func in aggregate_functions
                ):
                    fixes.append("Detected potential GROUP BY issue")

    return sql, fixes


def _fix_invalid_join_references(sql: str) -> Tuple[str, List[str]]:
    """Fix invalid JOIN references like COUNT(JOIN.id)."""
    import re

    fixes = []

    # Fix COUNT(JOIN.id) -> COUNT(orders.id) or appropriate table reference
    join_id_pattern = r"COUNT\(JOIN\.id\)"
    if re.search(join_id_pattern, sql, re.IGNORECASE):
        # Try to determine the correct table reference
        # Look for table names in FROM and JOIN clauses
        from_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            sql = re.sub(
                join_id_pattern, f"COUNT({table_name}.id)", sql, flags=re.IGNORECASE
            )
            fixes.append(f"Fixed COUNT(JOIN.id) -> COUNT({table_name}.id)")
        else:
            # Fallback to orders table
            sql = re.sub(join_id_pattern, "COUNT(orders.id)", sql, flags=re.IGNORECASE)
            fixes.append("Fixed COUNT(JOIN.id) -> COUNT(orders.id)")

    # Fix other invalid JOIN references
    join_ref_pattern = r"JOIN\.(\w+)"
    if re.search(join_ref_pattern, sql, re.IGNORECASE):
        # Look for the most likely table reference
        from_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            sql = re.sub(
                join_ref_pattern, f"{table_name}.\\1", sql, flags=re.IGNORECASE
            )
            fixes.append(f"Fixed JOIN.column references -> {table_name}.column")

    return sql, fixes


def _fix_missing_columns(sql: str) -> Tuple[str, List[str]]:
    """Fix references to non-existent columns by calculating them properly."""
    import re

    fixes = []

    # Fix o.total_amount -> SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))
    if "o.total_amount" in sql:
        # Check if order_items is already joined
        if "order_items" in sql or "oi." in sql:
            # Replace with proper calculation
            sql = re.sub(
                r"o\.total_amount",
                "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(
                "Fixed o.total_amount -> SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))"
            )
        else:
            # Add JOIN to order_items and fix the column reference
            # Find the FROM clause and add the JOIN
            from_match = re.search(r"(FROM\s+orders\s+o)", sql, re.IGNORECASE)
            if from_match:
                # Add JOIN to order_items
                join_clause = " JOIN order_items oi ON oi.order_id = o.id"
                sql = sql.replace(
                    from_match.group(1), from_match.group(1) + join_clause
                )

                # Now replace the column reference (remove any existing SUM wrapper)
                sql = re.sub(
                    r"SUM\(CAST\(o\.total_amount",
                    "SUM(CAST(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)",
                    sql,
                    flags=re.IGNORECASE,
                )
                # Also handle cases without CAST
                sql = re.sub(
                    r"o\.total_amount",
                    "oi.qty * oi.unit_price * (1 - oi.discount_pct/100)",
                    sql,
                    flags=re.IGNORECASE,
                )
                fixes.append(
                    "Fixed o.total_amount -> SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) with JOIN"
                )
            else:
                # Fallback to 0 if we can't add the JOIN
                sql = re.sub(r"o\.total_amount", "0", sql, flags=re.IGNORECASE)
                fixes.append("Fixed o.total_amount -> 0 (could not add JOIN)")

    # Fix other common missing column patterns
    missing_columns = {
        r"o\.revenue": "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
        r"o\.sales": "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
        r"o\.amount": "SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100))",
    }

    for pattern, replacement in missing_columns.items():
        if re.search(pattern, sql, re.IGNORECASE):
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
            fixes.append(f"Fixed {pattern} -> {replacement}")

    return sql, fixes


def _generate_sql_with_ai(
    question: str, schema_info: Dict[str, Any]
) -> Tuple[str, bool, str]:
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
    """Robust heuristic SQL generation using pattern matching."""
    if not question or not isinstance(question, str):
        return "SELECT 'Invalid question input' AS message, COUNT(*) AS total_orders FROM orders LIMIT 1;"

    q = question.lower()

    # Pattern-based SQL generation
    patterns = [
        # Revenue/Sales patterns
        {
            "keywords": ["top", "product", "revenue"],
            "generator": _generate_revenue_query,
        },
        {"keywords": ["top", "product", "sales"], "generator": _generate_revenue_query},
        {
            "keywords": ["best", "selling", "product"],
            "generator": _generate_revenue_query,
        },
        {
            "keywords": ["highest", "revenue", "product"],
            "generator": _generate_revenue_query,
        },
        # Time-based patterns
        {"keywords": ["sales", "month"], "generator": _generate_monthly_sales_query},
        {"keywords": ["monthly", "sales"], "generator": _generate_monthly_sales_query},
        {"keywords": ["revenue", "trend"], "generator": _generate_monthly_sales_query},
        # Customer patterns
        {"keywords": ["top", "customer"], "generator": _generate_customer_query},
        {
            "keywords": ["customer", "order", "value"],
            "generator": _generate_customer_query,
        },
        {"keywords": ["new", "customer"], "generator": _generate_new_customer_query},
        # Product patterns
        {"keywords": ["product", "inventory"], "generator": _generate_inventory_query},
        {"keywords": ["low", "stock"], "generator": _generate_inventory_query},
        {"keywords": ["product", "category"], "generator": _generate_category_query},
        # Order patterns
        {"keywords": ["order", "status"], "generator": _generate_order_status_query},
        {"keywords": ["recent", "order"], "generator": _generate_recent_orders_query},
    ]

    # Find the best matching pattern
    best_match = None
    best_score = 0

    for pattern in patterns:
        score = sum(1 for keyword in pattern["keywords"] if keyword in q)
        if score > best_score:
            best_score = score
            best_match = pattern

    # Generate SQL based on the best match
    if best_match and best_score > 0:
        try:
            sql = best_match["generator"](q)
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"Heuristic generated SQL: {sql[:100]}...")
            return sql
        except Exception as e:
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"Heuristic generation failed: {e}")

    # Ultimate fallback - return a safe query
    return "SELECT 'No specific pattern matched' AS message, COUNT(*) AS total_orders FROM orders LIMIT 1;"


def _generate_revenue_query(q: str) -> str:
    """Generate revenue-based queries."""
    n = _months_from_question(q, default=3)
    limit = _extract_limit(q, default=10)

    return (
        "SELECT p.name AS product, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS revenue "
        "FROM order_items oi "
        "JOIN products p ON p.id = oi.product_id "
        "JOIN orders o ON o.id = oi.order_id "
        "WHERE o.status <> 'CANCELLED' AND "
        f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY p.name ORDER BY revenue DESC LIMIT {limit};"
    ).format(limit=limit)


def _generate_monthly_sales_query(q: str) -> str:
    """Generate monthly sales queries."""
    n = _months_from_question(q, default=6)

    return (
        "SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS total_sales "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status <> 'CANCELLED' AND "
        f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY month ORDER BY month;"
    )


def _generate_customer_query(q: str) -> str:
    """Generate customer-based queries."""
    limit = _extract_limit(q, default=10)

    return (
        "SELECT c.name AS customer, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS total_value, "
        "COUNT(DISTINCT o.id) AS order_count "
        "FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status <> 'CANCELLED' "
        "GROUP BY c.id, c.name "
        "ORDER BY total_value DESC LIMIT {limit};"
    ).format(limit=limit)


def _generate_new_customer_query(q: str) -> str:
    """Generate new customer queries."""
    n = _months_from_question(q, default=1)

    return (
        "SELECT c.name AS customer, c.email, o.order_date AS first_order "
        "FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        f"WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY c.id, c.name, c.email "
        "ORDER BY first_order DESC;"
    )


def _generate_inventory_query(q: str) -> str:
    """Generate inventory-related queries."""
    return (
        "SELECT p.name AS product, p.stock_quantity, c.name AS category "
        "FROM products p "
        "JOIN categories c ON c.id = p.category_id "
        "WHERE p.stock_quantity < 50 "
        "ORDER BY p.stock_quantity ASC;"
    )


def _generate_category_query(q: str) -> str:
    """Generate category-based queries."""
    return (
        "SELECT c.name AS category, "
        "COUNT(p.id) AS product_count, "
        "CAST(AVG(p.price) AS DECIMAL(10,2)) AS avg_price "
        "FROM categories c "
        "LEFT JOIN products p ON p.category_id = c.id "
        "GROUP BY c.id, c.name "
        "ORDER BY product_count DESC;"
    )


def _generate_order_status_query(q: str) -> str:
    """Generate order status queries."""
    return (
        "SELECT status, COUNT(*) AS order_count, "
        "CAST(AVG(total_amount) AS DECIMAL(10,2)) AS avg_amount "
        "FROM orders "
        "GROUP BY status "
        "ORDER BY order_count DESC;"
    )


def _generate_recent_orders_query(q: str) -> str:
    """Generate recent orders queries."""
    limit = _extract_limit(q, default=10)

    return (
        "SELECT o.id, c.name AS customer, o.order_date, o.status, "
        "CAST(o.total_amount AS DECIMAL(10,2)) AS total_amount "
        "FROM orders o "
        "JOIN customers c ON c.id = o.customer_id "
        "ORDER BY o.order_date DESC LIMIT {limit};"
    ).format(limit=limit)


def _extract_limit(q: str, default: int = 10) -> int:
    """Extract limit number from question."""
    import re

    # Look for patterns like "top 5", "best 10", "first 3"
    patterns = [
        r"top\s+(\d+)",
        r"best\s+(\d+)",
        r"first\s+(\d+)",
        r"last\s+(\d+)",
        r"(\d+)\s+products?",
        r"(\d+)\s+customers?",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return int(match.group(1))

    return default


def answer_question(question: str) -> dict:
    """Answer a natural language question using AI-powered SQL generation."""
    # Validate input more thoroughly
    if question is None:
        return {
            "answer_text": "Error: Question cannot be None",
            "sql": "",
            "rows": [],
            "chart_json": None,
            "sql_source": "error",
            "sql_corrected": False,
            "ai_fallback_error": False,
            "error_details": {
                "type": "input_validation_error",
                "description": "Question is None",
                "received_value": "None",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

    if not isinstance(question, str):
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

    if not question.strip():
        return {
            "answer_text": "Error: Question cannot be empty",
            "sql": "",
            "rows": [],
            "chart_json": None,
            "sql_source": "error",
            "sql_corrected": False,
            "ai_fallback_error": False,
            "error_details": {
                "type": "input_validation_error",
                "description": "Question is empty or whitespace only",
                "received_value": repr(question),
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

            # Learn from this error
            _learn_from_error(sql, str(sql_error))

            # Try to fix SQL errors and retry
            print("Attempting to fix SQL syntax...")
            fixed_sql = _fix_sql_syntax(sql)

            if fixed_sql != sql:
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
    if not q or not isinstance(q, str):
        return default

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
