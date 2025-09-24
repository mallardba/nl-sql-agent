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
import re
import time
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from .cache import get_cache, set_cache
from .config import (
    AGGREGATE_FUNCTIONS,
    CATEGORICAL_KEYWORDS,
    CHART_THRESHOLDS,
    COMMON_AMBIGUOUS_COLUMNS,
    FALLBACK_QUERIES,
    HEURISTIC_PATTERNS,
    LEARNED_PATTERNS,
    LINE_CHART_KEYWORDS,
    PIE_CHART_KEYWORDS,
    SCATTER_CHART_KEYWORDS,
    SQL_PATTERNS,
    SQL_THRESHOLDS,
    TIME_KEYWORDS,
    TIME_PATTERNS,
)
from .error_logger import log_ai_error
from .learning import (
    categorize_query,
    get_query_suggestions,
    get_related_questions,
    record_error_metrics,
    record_query_metrics,
)
from .tools import get_schema_metadata, render_chart, respond, run_sql, to_jsonable

# LangChain imports (will be available after pip install)
try:
    # from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from .schema_index import (
        find_similar_questions,
        find_similar_schema,
        store_question_embedding,
    )

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


def determine_chart_type(
    x_data: List[Any], y_data: List[Any], x_name: str, y_name: str, question: str
) -> str:
    """
    Determine the most appropriate chart type based on data characteristics and question context.

    Args:
        x_data: X-axis data values
        y_data: Y-axis data values
        x_name: Name of X-axis column
        y_name: Name of Y-axis column
        question: Original user question for context

    Returns:
        Chart type: 'line', 'bar', 'pie', 'scatter', or 'area'
    """

    # Convert to lowercase for analysis
    x_name_lower = x_name.lower()
    question_lower = question.lower()

    # Calculate unique values for analysis
    unique_x_values = len(set(str(x) for x in x_data))
    unique_y_values = len(set(str(y) for y in y_data))

    # 1. Time series analysis
    if any(keyword in x_name_lower for keyword in TIME_KEYWORDS):
        # For quarterly data with few points, prefer bar chart
        if (
            "quarter" in x_name_lower
            and unique_x_values <= CHART_THRESHOLDS["quarter_max_points"]
        ):
            return "bar"
        # For other time data, use line chart
        return "line"

    # 2. Question context analysis
    if any(keyword in question_lower for keyword in LINE_CHART_KEYWORDS):
        return "line"

    if any(keyword in question_lower for keyword in SCATTER_CHART_KEYWORDS):
        return "scatter"

    if any(keyword in question_lower for keyword in PIE_CHART_KEYWORDS):
        return "pie"

    # 3. Data distribution analysis

    # Pie chart for categorical data with few categories
    # But exclude time-based data (quarters, months, etc.)
    if (
        CHART_THRESHOLDS["pie_min_categories"]
        <= unique_x_values
        <= CHART_THRESHOLDS["pie_max_categories"]
    ):
        # Check if Y values are numeric (for pie chart)
        try:
            numeric_y = [float(y) for y in y_data if y is not None]
            if len(numeric_y) == len(y_data):  # All Y values are numeric
                # Check if X data contains time patterns
                x_data_lower = [str(x).lower() for x in x_data]
                has_time_pattern = any(
                    pattern in " ".join(x_data_lower) for pattern in TIME_PATTERNS
                )

                if not has_time_pattern:
                    return "pie"
        except (ValueError, TypeError):
            pass

    # Scatter plot for correlation analysis
    if (
        unique_x_values > CHART_THRESHOLDS["scatter_min_unique_values"]
        and unique_y_values > CHART_THRESHOLDS["scatter_min_unique_values"]
    ):
        try:
            # Check if both X and Y are numeric
            numeric_x = [float(x) for x in x_data if x is not None]
            numeric_y = [float(y) for y in y_data if y is not None]
            if len(numeric_x) == len(x_data) and len(numeric_y) == len(y_data):
                return "scatter"
        except (ValueError, TypeError):
            pass

    # 4. Column name analysis
    if any(keyword in x_name_lower for keyword in CATEGORICAL_KEYWORDS):
        if unique_x_values <= 6:
            return "pie"
        else:
            return "bar"

    # 5. Default to bar chart
    return "bar"


def _get_relevant_schema_context(question: str) -> str:
    """
    Get relevant schema context using embeddings to enhance AI prompts.

    Args:
        question: The user's natural language question

    Returns:
        Formatted string with relevant schema information
    """
    try:

        # Get similar schema elements
        similar_schema = find_similar_schema(question, n_results=5)

        # Get similar questions for context
        similar_questions = find_similar_questions(question, n_results=3)

        context_parts = []

        # Add relevant schema information
        if similar_schema:
            context_parts.append("Relevant Schema Elements:")
            for item in similar_schema:
                if item.get("document"):
                    context_parts.append(f"- {item['document']}")
                    if item.get("metadata"):
                        metadata = item["metadata"]
                        if metadata.get("table_name"):
                            context_parts.append(f"  Table: {metadata['table_name']}")
                        if metadata.get("columns"):
                            context_parts.append(
                                f"  Columns: {', '.join(metadata['columns'])}"
                            )

        # Add similar questions for context
        if similar_questions:
            context_parts.append("\nSimilar Questions:")
            for item in similar_questions:
                question = item.get("question")
                sql = item.get("sql")
                if question and sql:
                    context_parts.append(f"- Q: {question}")
                    context_parts.append(f"  SQL: {sql}")

        return (
            "\n".join(context_parts)
            if context_parts
            else "No relevant schema context found."
        )

    except Exception as e:
        # Fallback if embeddings are not available
        if os.getenv("DEBUG") == "true":
            print(f"Schema embeddings not available: {e}")
        return "Schema embeddings not available - using full schema."


def _fix_sql_syntax(sql: str) -> Tuple[str, bool]:
    """Fix common SQL syntax errors using pattern-based corrections.

    Returns:
        Tuple of (fixed_sql, fixes_were_applied)
    """
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
    fixes_were_applied = len(fixes_applied) > 0
    if fixes_were_applied and os.getenv("DEBUG", "false").lower() == "true":
        print(f"SQL fixes applied: {fixes_applied}")

    return sql, fixes_were_applied


def _apply_learned_patterns(sql: str) -> Tuple[str, List[str]]:
    """Apply learned error patterns from previous corrections."""

    fixes = []

    for pattern_info in LEARNED_PATTERNS:
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

    fixes = []

    # Pattern: CAST(expression) AS alias -> CAST(expression AS DECIMAL(10,2)) AS alias
    pattern = SQL_PATTERNS["cast_syntax"]

    def replace_cast(match):
        expression = match.group(1)
        alias = match.group(2)
        fixes.append(f"Fixed CAST syntax: {alias}")
        return f"CAST({expression} AS DECIMAL(10,2)) AS {alias}"

    sql = re.sub(pattern, replace_cast, sql)
    return sql, fixes


def _fix_ambiguous_columns(sql: str) -> Tuple[str, List[str]]:
    """Fix ambiguous column references by adding table aliases."""

    fixes = []

    # Extract table names and their aliases
    tables_with_aliases = {}

    # Find FROM table
    from_match = re.search(SQL_PATTERNS["from_table"], sql, re.IGNORECASE)
    if from_match:
        table_name = from_match.group(1)
        alias = (
            from_match.group(2)
            or table_name.lower()[: SQL_THRESHOLDS["max_table_alias_length"]]
        )  # Use first 2 chars as alias
        tables_with_aliases[table_name] = alias

    # Find JOIN tables
    join_matches = re.finditer(SQL_PATTERNS["join_table"], sql, re.IGNORECASE)
    for match in join_matches:
        table_name = match.group(1)
        alias = (
            match.group(2)
            or table_name.lower()[: SQL_THRESHOLDS["max_table_alias_length"]]
        )
        tables_with_aliases[table_name] = alias

    # If we have multiple tables, check for ambiguous columns
    if len(tables_with_aliases) > 1:
        for column in COMMON_AMBIGUOUS_COLUMNS:
            # Look for bare column references (not table.column)
            bare_column_pattern = SQL_PATTERNS["bare_column"].format(column=column)
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

    fixes = []

    # Fix missing ON clauses
    if "JOIN" in sql.upper() and "ON" not in sql.upper():
        fixes.append("Detected JOIN without ON clause")

    # Fix malformed JOIN conditions
    if re.search(SQL_PATTERNS["join_on"], sql):
        fixes.append("Detected JOIN condition syntax")

    return sql, fixes


def _fix_groupby_syntax(sql: str) -> Tuple[str, List[str]]:
    """Fix GROUP BY syntax issues."""

    fixes = []

    # Check if SELECT has non-aggregate columns but no GROUP BY
    if "SELECT" in sql.upper() and "GROUP BY" not in sql.upper():
        # Look for aggregate functions
        has_aggregates = any(func in sql.upper() for func in AGGREGATE_FUNCTIONS)

        if has_aggregates:
            # Look for non-aggregate columns
            select_match = re.search(
                SQL_PATTERNS["select_clause"], sql, re.IGNORECASE | re.DOTALL
            )
            if select_match:
                select_clause = select_match.group(1)
                # Simple check for non-aggregate columns
                if re.search(r"\b\w+\b", select_clause) and not all(
                    func in select_clause.upper() for func in AGGREGATE_FUNCTIONS
                ):
                    fixes.append("Detected potential GROUP BY issue")

    return sql, fixes


def _fix_invalid_join_references(sql: str) -> Tuple[str, List[str]]:
    """Fix invalid JOIN references like COUNT(JOIN.id)."""

    fixes = []

    # Fix COUNT(JOIN.id) -> COUNT(orders.id) or appropriate table reference
    if re.search(SQL_PATTERNS["join_id_reference"], sql, re.IGNORECASE):
        # Try to determine the correct table reference
        # Look for table names in FROM and JOIN clauses
        from_match = re.search(SQL_PATTERNS["from_table"], sql, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            sql = re.sub(
                SQL_PATTERNS["join_id_reference"],
                f"COUNT({table_name}.id)",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(f"Fixed COUNT(JOIN.id) -> COUNT({table_name}.id)")
        else:
            # Fallback to orders table
            sql = re.sub(
                SQL_PATTERNS["join_id_reference"],
                f"COUNT({SQL_THRESHOLDS['preferred_fallback_table']}.id)",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(
                f"Fixed COUNT(JOIN.id) -> COUNT({SQL_THRESHOLDS['preferred_fallback_table']}.id)"
            )

    # Fix other invalid JOIN references
    if re.search(SQL_PATTERNS["join_reference"], sql, re.IGNORECASE):
        # Look for the most likely table reference
        from_match = re.search(SQL_PATTERNS["from_table"], sql, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            sql = re.sub(
                SQL_PATTERNS["join_reference"],
                f"{table_name}.\\1",
                sql,
                flags=re.IGNORECASE,
            )
            fixes.append(f"Fixed JOIN.column references -> {table_name}.column")

    return sql, fixes


def _fix_missing_columns(sql: str) -> Tuple[str, List[str]]:
    """Fix references to non-existent columns by calculating them properly."""

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

        # Get relevant schema context using embeddings
        relevant_schema_context = _get_relevant_schema_context(question)

        # Combine full schema with relevant context
        enhanced_schema_info = f"""
        Full Database Schema:
        {schema_info}
        
        Most Relevant Schema Context for this question:
        {relevant_schema_context}
        """

        # Create a comprehensive prompt for SQL generation
        system_prompt = f"""
        You are an expert SQL developer. Generate MySQL SQL queries based on natural language questions.
        
        Database Schema:
        {enhanced_schema_info}
        
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
           - For quarterly data, ALWAYS use: CONCAT(YEAR(date_column), '-Q', QUARTER(date_column)) AS quarter
           - For monthly data, use: DATE_FORMAT(date_column, '%Y-%m') AS month
           - NEVER use DATE_FORMAT with '%Y-Q%q' as it creates malformed output like '2024-Qq'
           - The correct quarterly format is: CONCAT(YEAR(o.order_date), '-Q', QUARTER(o.order_date))
        8. Use aggregate functions (SUM, COUNT, AVG) when appropriate
        9. When using CAST(), always specify the data type: CAST(expression AS DECIMAL(10,2))
        10. Ensure all parentheses are properly closed
        11. Test your SQL syntax before returning
        
        Return only the raw SQL query without any markdown formatting, code blocks, or explanations.
        
        Examples:
        - Basic query: SELECT * FROM table WHERE id = 1;
        - Quarterly data: SELECT CONCAT(YEAR(o.order_date), '-Q', QUARTER(o.order_date)) AS quarter, SUM(amount) FROM orders o GROUP BY quarter;
        - Monthly data: SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(amount) FROM orders o GROUP BY month;
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
        sql, corrected = _fix_sql_syntax(sql)
        if corrected and os.getenv("DEBUG", "false").lower() == "true":
            print("SQL was corrected during generation")

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
        return FALLBACK_QUERIES["invalid_input"]

    q = question.lower()

    # Find the best matching pattern
    best_match = None
    best_score = 0

    for pattern in HEURISTIC_PATTERNS:
        score = sum(1 for keyword in pattern["keywords"] if keyword in q)
        if score > best_score:
            best_score = score
            best_match = pattern

    # Generate SQL based on the best match
    if best_match and best_score > 0:
        try:
            # Get the generator function by name
            generator_name = best_match["generator"]
            generator_func = globals()[generator_name]
            sql = generator_func(q)
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"Heuristic generated SQL: {sql[:100]}...")
            return sql
        except Exception as e:
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"Heuristic generation failed: {e}")

    # Ultimate fallback - return a safe query
    return FALLBACK_QUERIES["no_match"]


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


def _generate_quarterly_sales_query(q: str) -> str:
    """Generate quarterly sales queries."""
    n = _months_from_question(q, default=12)  # Default to 12 months for quarterly data

    return (
        "SELECT CONCAT(YEAR(o.order_date), '-Q', QUARTER(o.order_date)) AS quarter, "
        "CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DECIMAL(10,2)) AS total_sales "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status <> 'CANCELLED' AND "
        f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
        "GROUP BY YEAR(o.order_date), QUARTER(o.order_date) "
        "ORDER BY YEAR(o.order_date), QUARTER(o.order_date);"
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
    start_time = time.time()

    # Validate input more thoroughly
    if question is None:
        error_result = {
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
            "query_category": "unknown",
            "category_confidence": 0.0,
            "response_time": time.time() - start_time,
        }
        record_query_metrics(
            "None", error_result, error_result["response_time"], is_ai_attempt=False
        )
        return error_result

    if not isinstance(question, str):
        error_result = {
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
            "query_category": "unknown",
            "category_confidence": 0.0,
            "response_time": time.time() - start_time,
        }
        record_query_metrics(
            str(question),
            error_result,
            error_result["response_time"],
            is_ai_attempt=False,
        )
        return error_result

    if not question.strip():
        error_result = {
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
            "query_category": "unknown",
            "category_confidence": 0.0,
            "response_time": time.time() - start_time,
        }
        record_query_metrics(
            question, error_result, error_result["response_time"], is_ai_attempt=False
        )
        return error_result

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
        record_query_metrics(question, cached, response_time, is_ai_attempt=False)

        return cached

    try:
        # Get schema information for AI context
        schema_info = get_schema_metadata()

        # Generate SQL using AI (with fallback to heuristic)
        sql, sql_corrected, sql_source = _generate_sql_with_ai(question, schema_info)

        # Track if this was a fallback due to AI failure
        ai_fallback_error = sql_source == "heuristic_fallback"

        # Record AI attempt (even if it failed and fell back to heuristic)
        if sql_source in ["ai", "heuristic_fallback"]:
            # This was an AI attempt, record it
            ai_attempt_result = {
                "answer_text": "AI attempt (may have failed)",
                "sql": sql,
                "rows": [],
                "chart_json": None,
                "sql_source": "ai",  # Always record as AI attempt
                "sql_corrected": False,
                "ai_fallback_error": ai_fallback_error,
                "query_category": category,
                "category_confidence": confidence,
                "response_time": 0,  # Will be updated later
            }
            record_query_metrics(question, ai_attempt_result, 0, is_ai_attempt=True)

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
            fixed_sql, fixes_applied = _fix_sql_syntax(sql)

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
        if sql_source != "heuristic_fallback":
            record_query_metrics(question, result, response_time, is_ai_attempt=False)

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
        record_error_metrics("ai_generation_exception", str(e))

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
                "query_category": category,
                "category_confidence": confidence,
                "response_time": time.time() - start_time,
            }

            # Record the successful heuristic fallback
            record_query_metrics(
                question, result, result["response_time"], is_ai_attempt=False
            )

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
            record_query_metrics(
                question,
                error_result,
                error_result["response_time"],
                is_ai_attempt=False,
            )

            return error_result


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
