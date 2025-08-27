"""
Agent orchestration (stub).
Wire in an LLM+ReAct loop here, or keep simple rules for MVP.
"""

import re
from decimal import Decimal

from .cache import get_cache, set_cache
from .tools import render_chart, respond, run_sql, to_jsonable


# Very simple MVP: look for keywords and route to canned SQL patterns.
# Replace with LangChain or your own planner when ready.
def _heuristic_sql(question: str) -> str:
    q = question.lower()
    if "top" in q and "product" in q and ("revenue" in q or "sales" in q):
        n = _months_from_question(q, default=3)
        return (
            "SELECT p.name AS product, CAST(SUM(oi.qty * oi.unit_price * (1 - oi.discount_pct/100)) AS DOUBLE) AS revenue "
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
    cache_key = f"q::{question.strip().lower()}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    # (1) Inspect schema (for MVP, just fetch once; later: vector search)
    # schema = describe_schema()

    # (2) Draft SQL (heuristic for MVP; replace with LLM later)
    sql = _heuristic_sql(question)

    # (3) Execute
    rows = run_sql(sql)

    # (4) Try to produce a chart for common cases
    chart_json = None
    if rows:
        cols = list(rows[0].keys())
        if len(cols) >= 2:
            y_val = rows[0][cols[1]]
            if isinstance(y_val, (int, float, Decimal)):
                # choose a nicer chart type for time buckets
                x_name = cols[0].lower()
                chart_type = "line" if x_name in ("month", "date", "ym") else "bar"
                chart_json = render_chart(rows, spec={"type": chart_type})

    if chart_json is not None:
        chart_json = to_jsonable(chart_json)

    answer_text = "Query executed successfully."
    result = {
        "answer_text": answer_text,
        "sql": sql,
        "rows": rows,
        "chart_json": chart_json,
    }
    set_cache(cache_key, to_jsonable(result))
    return respond(result)


def _months_from_question(q: str, default=3):
    m = re.search(r"\blast\s+(\d{1,2})\s+months?\b", q)
    n = int(m.group(1)) if m else default
    return max(1, min(n, 24))  # clamp 1..24
