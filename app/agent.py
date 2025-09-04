"""
Agent orchestration with LangChain integration.
Uses OpenAI to generate SQL from natural language questions.
"""

import os
import re
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


def _generate_sql_with_ai(question: str, schema_info: Dict[str, Any]) -> str:
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
        7. Handle dates properly using MySQL date functions
        8. Use aggregate functions (SUM, COUNT, AVG) when appropriate
        
        Return only the SQL query, no explanations.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate SQL for this question: {question}"),
        ]

        response = llm.invoke(messages)
        sql = response.content.strip()

        # Basic safety check
        if not sql.lower().startswith("select"):
            raise ValueError("Generated SQL is not a SELECT query")

        return sql

    except Exception as e:
        print(f"AI SQL generation failed: {e}")
        # Fallback to heuristic approach
        return _heuristic_sql_fallback(question)


def _heuristic_sql_fallback(question: str) -> str:
    """Fallback heuristic SQL generation (original logic)."""
    q = question.lower()
    if "top" in q and "product" in q and ("revenue" in q or "sales" in q):
        n = _months_from_question(q, default=3)
        return (
            "SELECT p.name AS product, CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS revenue "
            "FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id "
            "JOIN orders o ON o.id = oi.order_id "
            "WHERE o.status <> 'CANCELLED' AND "
            f"o.order_date >= DATE_SUB(CURDATE(), INTERVAL {n} MONTH) "
            "GROUP BY p.name ORDER BY revenue DESC LIMIT 10;"
        )
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
    q = question.lower()
    cache_key = f"q::{q.strip()}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    try:
        # Get schema information for AI context
        schema_info = get_schema_metadata()

        # Generate SQL using AI (with fallback to heuristic)
        sql = _generate_sql_with_ai(question, schema_info)

        # Execute the SQL
        rows = run_sql(sql)

        # Generate chart if we have numeric data
        chart_json = None
        if rows:
            cols = list(rows[0].keys())
            if len(cols) >= 2:
                y_val = rows[0][cols[1]]
                if isinstance(y_val, (int, float, Decimal)):
                    x_name = cols[0].lower()
                    chart_type = "line" if x_name in ("month", "date", "ym") else "bar"
                    chart_json = render_chart(rows, spec={"type": chart_type})

        if chart_json is not None:
            chart_json = to_jsonable(chart_json)

        answer_text = "Query executed successfully using AI-generated SQL."
        result = {
            "answer_text": answer_text,
            "sql": sql,
            "rows": rows,
            "chart_json": chart_json,
        }

        set_cache(cache_key, to_jsonable(result))
        return respond(result)

    except Exception as e:
        print(f"Error in answer_question: {e}")
        # Return error response
        return {
            "answer_text": f"Error processing question: {str(e)}",
            "sql": "",
            "rows": [],
            "chart_json": None,
        }


def _months_from_question(q: str, default=3):
    """Extract number of months from question text."""
    m = re.search(r"\blast\s+(\d{1,2})\s+months?\b", q.lower())
    n = int(m.group(1)) if m else default
    return max(1, min(n, 24))  # clamp 1..24
