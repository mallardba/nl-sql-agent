import os
from typing import Any, Dict, Tuple

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .enums import SQLSource
from .heuristic_handler import heuristic_sql_fallback
from .schema_index import find_similar_questions, find_similar_schema
from .sql_corrections import fix_sql_syntax

# LangChain imports (will be available after pip install)
try:
    # from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from .schema_index import find_similar_questions, find_similar_schema

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


def generate_sql_with_ai(
    question: str, schema_info: Dict[str, Any]
) -> Tuple[str, bool, str]:
    """Generate SQL using OpenAI based on the question and schema."""
    if not LANGCHAIN_AVAILABLE:
        # Fallback to heuristic approach if LangChain not available
        return heuristic_sql_fallback(question)

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
        sql, corrected = fix_sql_syntax(sql)
        if corrected and os.getenv("DEBUG", "false").lower() == "true":
            print("SQL was corrected during generation")

        # Basic SQL syntax validation
        if sql.count("(") != sql.count(")"):
            raise ValueError("Unmatched parentheses in SQL query")

        return sql, corrected, SQLSource.AI

    except Exception as e:
        print(f"AI SQL generation failed: {e}")
        # Fallback to heuristic approach
        return heuristic_sql_fallback(question), False, SQLSource.HEURISTIC_FALLBACK
