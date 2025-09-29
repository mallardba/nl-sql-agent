"""
Heuristic SQL Generation Handler

Handles heuristic SQL generation using pattern matching and fallback generators.
Provides robust fallback when AI generation fails or when forced.
"""

import os

from ..config import FALLBACK_QUERIES, HEURISTIC_PATTERNS
from .heuristic_generators import (
    _generate_category_query,
    _generate_customer_query,
    _generate_inventory_query,
    _generate_monthly_sales_query,
    _generate_new_customer_query,
    _generate_order_status_query,
    _generate_quarterly_sales_query,
    _generate_recent_orders_query,
    _generate_revenue_query,
)


def heuristic_sql_fallback(question: str) -> str:
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
            # Map generator names to actual functions
            generator_functions = {
                "_generate_revenue_query": _generate_revenue_query,
                "_generate_monthly_sales_query": _generate_monthly_sales_query,
                "_generate_quarterly_sales_query": _generate_quarterly_sales_query,
                "_generate_customer_query": _generate_customer_query,
                "_generate_new_customer_query": _generate_new_customer_query,
                "_generate_inventory_query": _generate_inventory_query,
                "_generate_category_query": _generate_category_query,
                "_generate_order_status_query": _generate_order_status_query,
                "_generate_recent_orders_query": _generate_recent_orders_query,
            }

            generator_name = best_match["generator"]
            generator_func = generator_functions.get(generator_name)

            if generator_func:
                sql = generator_func(q)
                if os.getenv("DEBUG", "false").lower() == "true":
                    print(f"Heuristic generated SQL: {sql[:100]}...")
                return sql
            else:
                if os.getenv("DEBUG", "false").lower() == "true":
                    print(f"Unknown generator function: {generator_name}")
                return FALLBACK_QUERIES["no_match"]

        except Exception as e:
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"Heuristic generation error: {e}")
            return FALLBACK_QUERIES["no_match"]

    # Ultimate fallback - return a safe query
    if os.getenv("DEBUG", "false").lower() == "true":
        print(f"No heuristic pattern matched for: {question}")
    return FALLBACK_QUERIES["no_match"]
